"""
Purchase Routes - API endpoints for handling purchases
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from backend.models.purchase_model import (
    ProcessPaymentRequest,
    PurchaseResponse,
    Purchase
)
from backend.services import purchase_service, user_service

router = APIRouter()


@router.post("/process-payment", response_model=PurchaseResponse)
async def process_payment(
    request: ProcessPaymentRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Process a payment for a purchase
    
    Supports purchases with:
    - Real money (CAD) - requires payment method
    - Tokens - requires sufficient token balance
    """
    # Extract session ID from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    session_id = authorization.replace("Bearer ", "")
    
    # Verify session and get user
    user = user_service.verify_session_id(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Determine if this is a CAD or token purchase
    is_cad_purchase = request.purchase_item.price_cad is not None and \
                      request.purchase_item.price_tokens is None
    
    is_token_purchase = request.purchase_item.price_tokens is not None and \
                        request.purchase_item.price_cad is None
    
    if is_cad_purchase:
        # Process CAD purchase
        success, message, purchase = purchase_service.process_purchase_with_cad(
            user_email=user.email,
            purchase_item=request.purchase_item,
            payment_method=request.payment_method
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Build response
        response = PurchaseResponse(
            success=True,
            purchase_id=purchase.purchase_id,
            message=message,
            tokens_added=purchase.tokens_received,
            new_rank=purchase.rank_upgrade
        )
        
        # Get updated token balance if tokens were added
        if purchase.tokens_received:
            updated_user = user_service.get_user_by_email(user.email)
            response.new_token_balance = getattr(updated_user, 'tokens', 0)
        
        return response
    
    elif is_token_purchase:
        # Process token purchase
        success, message, purchase = purchase_service.process_purchase_with_tokens(
            user_email=user.email,
            purchase_item=request.purchase_item
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Build response
        response = PurchaseResponse(
            success=True,
            purchase_id=purchase.purchase_id,
            message=message,
            tokens_added=purchase.tokens_received,
            new_rank=purchase.rank_upgrade
        )
        
        # Get updated token balance
        updated_user = user_service.get_user_by_email(user.email)
        response.new_token_balance = getattr(updated_user, 'tokens', 0)
        
        return response
    
    else:
        # Both or neither price is set
        raise HTTPException(
            status_code=400,
            detail="Purchase item must have either CAD or token price (not both)"
        )


@router.get("/purchase-history")
async def get_purchase_history(
    authorization: Optional[str] = Header(None)
):
    """
    Get purchase history for the authenticated user
    """
    # Extract session ID from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    session_id = authorization.replace("Bearer ", "")
    
    # Verify session and get user
    user = user_service.verify_session_id(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Get purchase history
    purchases = purchase_service.get_user_purchase_history(user.email)
    
    return {
        "purchases": [
            {
                "purchase_id": p.purchase_id,
                "item_name": p.item_name,
                "item_type": p.item_type,
                "amount_cad": p.amount_cad,
                "amount_tokens": p.amount_tokens,
                "tokens_received": p.tokens_received,
                "rank_upgrade": p.rank_upgrade,
                "purchase_date": p.purchase_date.isoformat(),
                "status": p.status
            }
            for p in purchases
        ]
    }


@router.get("/available-items")
async def get_available_items():
    """
    Get all available items for purchase
    
    This endpoint returns the catalog of items that can be purchased
    """
    # This would typically come from a database
    # For now, return the same items as defined in the frontend
    
    return {
        "token_packages": [
            {
                "id": "tokens_100",
                "type": "tokens",
                "name": "100 Tokens",
                "description": "Small token package",
                "price_cad": 4.99,
                "tokens_received": 100
            },
            {
                "id": "tokens_500",
                "type": "tokens",
                "name": "500 Tokens",
                "description": "Popular choice - 10% bonus!",
                "price_cad": 19.99,
                "tokens_received": 500
            },
            {
                "id": "tokens_1000",
                "type": "tokens",
                "name": "1000 Tokens",
                "description": "Best value - 20% bonus!",
                "price_cad": 34.99,
                "tokens_received": 1000
            }
        ],
        "rank_upgrades": [
            {
                "id": "rank_slug",
                "type": "rank",
                "name": "Upgrade to Slug",
                "description": "Unlock advanced features and priority support",
                "price_cad": 9.99,
                "price_tokens": 1000,
                "rank_upgrade": "slug"
            },
            {
                "id": "rank_banana_slug",
                "type": "rank",
                "name": "Upgrade to Banana Slug",
                "description": "Premium tier with exclusive features and profile customization",
                "price_cad": 19.99,
                "price_tokens": 2000,
                "rank_upgrade": "banana_slug"
            }
        ]
    }