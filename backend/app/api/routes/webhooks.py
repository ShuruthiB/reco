from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db_session
from app.services.webhook_processor import WebhookProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str = Header(None, alias="X-Razorpay-Event-Id"),
    session: AsyncSession = Depends(get_db_session)
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header")
        
    if not x_razorpay_event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event id header")

    raw_body = await request.body()
    processor = WebhookProcessor(session)
    
    try:
        success = await processor.process_razorpay_webhook(raw_body, x_razorpay_signature, x_razorpay_event_id)
        if not success:
            # If processing failed cleanly (e.g. downstream error), return 500 so Razorpay retries
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing failed")
    except ValueError as e:
        # Invalid signature
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    return {"status": "ok"}
