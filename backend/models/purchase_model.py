"""
Purchase Model - Handles purchase data structure
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class PurchaseItem(BaseModel):
    """Model for items being purchased"""
    id: str
    type: Literal["tokens", "rank", "cosmetic"]
    name: str
    description: str
    price_cad: Optional[float] = None
    price_tokens: Optional[int] = None
    tokens_received: Optional[int] = None
    rank_upgrade: Optional[str] = None


class PaymentMethod(BaseModel):
    """Model for payment method information"""
    card_number: str = Field(..., min_length=13, max_length=19)
    card_name: str = Field(..., min_length=3)
    expiry_date: str = Field(..., pattern=r'^\d{2}/\d{2}$')  # MM/YY format
    cvv: str = Field(..., min_length=3, max_length=4)
    billing_zip: str = Field(..., min_length=5)


class ProcessPaymentRequest(BaseModel):
    """Request model for processing payments"""
    purchase_item: PurchaseItem
    payment_method: PaymentMethod


class Purchase(BaseModel):
    """Model representing a completed purchase"""
    purchase_id: str
    user_email: str
    item_id: str
    item_type: Literal["tokens", "rank", "cosmetic"]
    item_name: str
    amount_cad: Optional[float] = None
    amount_tokens: Optional[int] = None
    payment_method_last4: Optional[str] = None  # Last 4 digits of card
    tokens_received: Optional[int] = None
    rank_upgrade: Optional[str] = None
    purchase_date: datetime
    status: Literal["pending", "completed", "failed", "refunded"] = "completed"
    transaction_id: Optional[str] = None  # Payment processor transaction ID


class PurchaseResponse(BaseModel):
    """Response model for successful purchases"""
    success: bool
    purchase_id: str
    message: str
    tokens_added: Optional[int] = None
    new_rank: Optional[str] = None
    new_token_balance: Optional[int] = None