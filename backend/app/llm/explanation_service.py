import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ValidationError

from openai import AsyncOpenAI
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class AlternativeActionContext(BaseModel):
    action: str
    expected_value: float
    is_valid: bool
    rejection_reasons: List[str]

class ExplanationContext(BaseModel):
    transaction_id: str
    selected_action: str
    amount_minor: int
    predicted_natural_recovery_prob: float
    estimated_incremental_uplift: float
    expected_incremental_revenue: float
    intervention_cost: float
    final_expected_net_contribution: float
    alternative_actions: List[AlternativeActionContext]
    experiment_name: Optional[str] = None
    experiment_arm: Optional[str] = None

class ExplanationResponse(BaseModel):
    merchant_facing_explanation: str
    rejected_alternative_explanation: str
    customer_facing_message: str
    transaction_summary: str
    experiment_summary: str

SYSTEM_PROMPT = """
You are the RECO (Revenue Experimentation & Conversion Optimizer) Decision Explainer.
Your job is to strictly explain the deterministic decision that has ALREADY been made by the system.
You MUST NOT invent, alter, or independently determine the decision, financial values, or eligibility.

You will receive a JSON context with the following deterministic data:
- Selected action
- Predicted natural recovery (probability)
- Estimated incremental uplift
- Expected incremental revenue
- Intervention cost
- Final expected net contribution
- Alternative actions and why they were rejected.

You must output a JSON object with EXACTLY these keys:
- "merchant_facing_explanation": Clear explanation distinguishing natural recovery, uplift, cost, and net contribution.
- "rejected_alternative_explanation": Why alternative actions were rejected (e.g., negative net contribution, policy violation).
- "customer_facing_message": A polite, safe message to the customer appropriate for the selected action (if DO_NOTHING, output a generic polite support message).
- "transaction_summary": A one sentence summary of the financials.
- "experiment_summary": Note on the experiment arm if applicable, else "N/A".
"""

class ExplanationService:
    def __init__(self, api_key: str = "dummy_key", base_url: Optional[str] = None):
        # Allow overriding base_url for testing or using local models
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
    def _fallback_explanation(self, context: ExplanationContext) -> ExplanationResponse:
        """Fallback when LLM is unavailable or repeatedly returns malformed data."""
        reason = (
            f"The selected intervention ({context.selected_action}) produces the highest net value "
            f"after costs. Expected net contribution: {context.final_expected_net_contribution:.2f}. "
            f"Natural recovery probability is {context.predicted_natural_recovery_prob:.2f}."
        )
        if context.selected_action == "DO_NOTHING":
            reason = (
                "The customer already has an estimated probability of recovering naturally, "
                "or the selected interventions produce insufficient incremental value after intervention costs."
            )
            
        return ExplanationResponse(
            merchant_facing_explanation=f"Decision: {context.selected_action}. Reason: {reason}",
            rejected_alternative_explanation="Alternatives were either blocked by policy or had lower expected net contribution.",
            customer_facing_message="We are processing your transaction. Please contact support if you need help.",
            transaction_summary=f"Tx {context.transaction_id} selected {context.selected_action} with net contribution {context.final_expected_net_contribution:.2f}.",
            experiment_summary=f"Experiment: {context.experiment_name} | Arm: {context.experiment_arm}" if context.experiment_name else "N/A"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APITimeoutError, openai.APIConnectionError, ValidationError, json.JSONDecodeError)),
        reraise=True
    )
    async def _call_llm_with_retry(self, prompt_json: str) -> ExplanationResponse:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo", # Default model
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_json}
                ],
                response_format={"type": "json_object"},
                timeout=10.0 # 10 second timeout
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
                
            parsed = json.loads(content)
            return ExplanationResponse.model_validate(parsed)
            
        except Exception as e:
            logger.warning(f"LLM call or validation failed: {str(e)}")
            raise

    async def generate_explanation(self, context: ExplanationContext) -> ExplanationResponse:
        # 1. Strip secrets / PII before prompting. 
        # The ExplanationContext inherently does not contain PII (no names, emails, raw DB rows).
        prompt_json = context.model_dump_json()
        
        logger.info(f"Requesting LLM explanation for transaction {context.transaction_id}")
        
        try:
            return await self._call_llm_with_retry(prompt_json)
        except Exception as e:
            logger.error(f"Failed to generate LLM explanation after retries: {str(e)}. Using fallback.")
            return self._fallback_explanation(context)
