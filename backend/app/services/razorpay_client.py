import razorpay
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RazorpayTestClient:
    """
    A server-side client for Razorpay strictly restricted to Test Mode.
    Never exposes API secrets.
    """
    def __init__(self):
        # Enforce Test Mode Only
        if settings.app_env == "production":
            raise RuntimeError("CRITICAL SECURITY: Razorpay client cannot run in production mode.")
        
        self.key_id = settings.razorpay_key_id or "rzp_test_dummy"
        self.key_secret = settings.razorpay_key_secret or "dummy_secret"
        
        if not self.key_id.startswith("rzp_test_"):
            raise ValueError("CRITICAL SECURITY: Only Razorpay test keys (rzp_test_...) are allowed.")
            
        # Initialize official client
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        
    def create_test_order(self, amount_minor: int, currency: str, receipt_id: str) -> dict:
        """Create a test order in Razorpay."""
        logger.info(f"Creating Razorpay test order for receipt {receipt_id} amount {amount_minor}")
        data = {
            "amount": amount_minor,
            "currency": currency,
            "receipt": receipt_id,
            "payment_capture": 1 # Auto capture for test mode
        }
        # In a real environment, this makes an HTTP call. We will mock it in tests.
        return self.client.order.create(data=data)
        
    def fetch_payment(self, payment_id: str) -> dict:
        """Fetch payment details from Razorpay."""
        logger.info(f"Fetching Razorpay payment {payment_id}")
        return self.client.payment.fetch(payment_id)
