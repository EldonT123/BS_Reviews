# tests/backend/payment/unit/test_purchase_service_unit.py
"""
Unit tests for purchase_service module
Tests business logic and utility functions in isolation
"""
import pytest
from datetime import datetime
from backend.main import app
from fastapi.testclient import TestClient
from backend.services import purchase_service
from backend.models.purchase_model import (
    Purchase, PurchaseItem, PaymentMethod, ProcessPaymentRequest
)

client = TestClient(app)

# ==================== Test Constants ====================
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "ValidPass123!"
TEST_USERNAME = "testuser"

# Card Details
CARD_NUMBER_VALID = "4532015112830366"
CARD_NUMBER_INVALID = "123"
CARD_NAME = "John Doe"
CARD_NAME_INVALID = "JD"
EXPIRY_DATE = "12/25"
EXPIRY_DATE_INVALID = "1225"
EXPIRY_DATE_EXPIRED = "01/20"
EXPIRY_DATE_INVALID_MONTH = "13/25"
CVV = "123"
CVV_INVALID = "1"
BILLING_ZIP = "12345"
BILLING_ZIP_INVALID = "123"

# Purchase Details
AMOUNT = 19.99
PURCHASE_ID = "PUR-123456"
TRANSACTION_ID = "TXN-123456"
ITEM_ID_TOKENS = "tokens_500"
ITEM_ID_RANK = "rank_slug"

# Purchase Item Details
ITEM_NAME_TOKENS = "500 Tokens"
ITEM_NAME_RANK = "Upgrade to Slug"
ITEM_TYPE_TOKENS = "tokens"
ITEM_TYPE_RANK = "rank"
TOKENS_RECEIVED = 500
RANK_UPGRADE = "slug"
PRICE_CAD_TOKENS = 19.99
PRICE_CAD_RANK = 9.99
PRICE_TOKENS_RANK = 1000


# ==================== Generate IDs Tests ====================

def test_generate_purchase_id_format():
    """Test that purchase ID has correct format."""
    purchase_id = purchase_service.generate_purchase_id()
    
    assert purchase_id.startswith("PUR-")
    assert len(purchase_id) == 20  # PUR- (4) + 16 hex chars


def test_generate_purchase_id_uniqueness():
    """Test that generated purchase IDs are unique."""
    ids = {purchase_service.generate_purchase_id() for _ in range(100)}
    
    assert len(ids) == 100  # All should be unique


def test_generate_transaction_id_format():
    """Test that transaction ID has correct format."""
    transaction_id = purchase_service.generate_transaction_id()
    
    assert transaction_id.startswith("TXN-")
    assert len(transaction_id) == 28  # TXN- (4) + 24 hex chars


def test_generate_transaction_id_uniqueness():
    """Test that generated transaction IDs are unique."""
    ids = {purchase_service.generate_transaction_id() for _ in range(100)}
    
    assert len(ids) == 100  # All should be unique


# ==================== Payment Validation Tests ====================

def test_process_payment_valid_card():
    """Test successful payment processing with valid card."""
    success, result = purchase_service.process_payment(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE,
        cvv=CVV,
        billing_zip=BILLING_ZIP,
        amount=AMOUNT
    )
    
    assert success is True
    assert result is not None
    assert result.startswith("TXN-")


def test_process_payment_invalid_card_number_too_short():
    """Test payment fails with card number too short."""
    success, result = purchase_service.process_payment(
        card_number=CARD_NUMBER_INVALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE,
        cvv=CVV,
        billing_zip=BILLING_ZIP,
        amount=AMOUNT
    )
    
    assert success is False
    assert "Invalid card number" in result


def test_process_payment_invalid_cvv_too_short():
    """Test payment fails with CVV too short."""
    success, result = purchase_service.process_payment(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE,
        cvv=CVV_INVALID,
        billing_zip=BILLING_ZIP,
        amount=AMOUNT
    )
    
    assert success is False
    assert "Invalid CVV" in result


def test_process_payment_invalid_expiry_format():
    """Test payment fails with invalid expiry format."""
    success, result = purchase_service.process_payment(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE_INVALID,
        cvv=CVV,
        billing_zip=BILLING_ZIP,
        amount=AMOUNT
    )
    
    assert success is False
    assert "Invalid expiry date format" in result


def test_process_payment_invalid_expiry_month():
    """Test payment fails with invalid expiry month."""
    success, result = purchase_service.process_payment(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE_INVALID_MONTH,
        cvv=CVV,
        billing_zip=BILLING_ZIP,
        amount=AMOUNT
    )
    
    assert success is False
    assert "Invalid expiry date" in result


def test_process_payment_expired_card():
    """Test payment fails with expired card."""
    success, result = purchase_service.process_payment(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE_EXPIRED,
        cvv=CVV,
        billing_zip=BILLING_ZIP,
        amount=AMOUNT
    )
    
    assert success is False
    assert "expired" in result.lower()


# ==================== Purchase Model Tests ====================

def test_create_purchase_with_tokens():
    """Test creating a purchase with token reward."""
    purchase = Purchase(
        purchase_id=PURCHASE_ID,
        user_email=TEST_EMAIL,
        item_id=ITEM_ID_TOKENS,
        item_type=ITEM_TYPE_TOKENS,
        item_name=ITEM_NAME_TOKENS,
        amount_cad=PRICE_CAD_TOKENS,
        payment_method_last4=CARD_NUMBER_VALID[-4:],
        tokens_received=TOKENS_RECEIVED,
        purchase_date=datetime.now(),
        status="completed",
        transaction_id=TRANSACTION_ID
    )
    
    assert purchase.purchase_id == PURCHASE_ID
    assert purchase.tokens_received == TOKENS_RECEIVED
    assert purchase.status == "completed"
    assert purchase.user_email == TEST_EMAIL


def test_create_purchase_with_rank_upgrade():
    """Test creating a purchase with rank upgrade."""
    purchase = Purchase(
        purchase_id=PURCHASE_ID,
        user_email=TEST_EMAIL,
        item_id=ITEM_ID_RANK,
        item_type=ITEM_TYPE_RANK,
        item_name=ITEM_NAME_RANK,
        amount_cad=PRICE_CAD_RANK,
        payment_method_last4=CARD_NUMBER_VALID[-4:],
        rank_upgrade=RANK_UPGRADE,
        purchase_date=datetime.now(),
        status="completed",
        transaction_id=TRANSACTION_ID
    )
    
    assert purchase.rank_upgrade == RANK_UPGRADE
    assert purchase.item_type == ITEM_TYPE_RANK
    assert purchase.purchase_id == PURCHASE_ID


# ==================== PurchaseItem Validation Tests ====================

def test_create_valid_purchase_item_tokens():
    """Test creating a valid token purchase item."""
    item = PurchaseItem(
        id=ITEM_ID_TOKENS,
        type=ITEM_TYPE_TOKENS,
        name=ITEM_NAME_TOKENS,
        description="Popular choice - 10% bonus!",
        price_cad=PRICE_CAD_TOKENS,
        tokens_received=TOKENS_RECEIVED
    )
    
    assert item.id == ITEM_ID_TOKENS
    assert item.price_cad == PRICE_CAD_TOKENS
    assert item.tokens_received == TOKENS_RECEIVED
    assert item.type == ITEM_TYPE_TOKENS


def test_create_valid_purchase_item_rank():
    """Test creating a valid rank upgrade purchase item."""
    item = PurchaseItem(
        id=ITEM_ID_RANK,
        type=ITEM_TYPE_RANK,
        name=ITEM_NAME_RANK,
        description="Unlock advanced features",
        price_cad=PRICE_CAD_RANK,
        price_tokens=PRICE_TOKENS_RANK,
        rank_upgrade=RANK_UPGRADE
    )
    
    assert item.id == ITEM_ID_RANK
    assert item.rank_upgrade == RANK_UPGRADE
    assert item.price_cad == PRICE_CAD_RANK
    assert item.price_tokens == PRICE_TOKENS_RANK
    assert item.type == ITEM_TYPE_RANK


# ==================== PaymentMethod Validation Tests ====================

def test_create_valid_payment_method():
    """Test creating a valid payment method."""
    method = PaymentMethod(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE,
        cvv=CVV,
        billing_zip=BILLING_ZIP
    )
    
    assert method.card_number == CARD_NUMBER_VALID
    assert method.card_name == CARD_NAME
    assert method.expiry_date == EXPIRY_DATE
    assert method.cvv == CVV
    assert method.billing_zip == BILLING_ZIP


def test_payment_method_card_number_too_short():
    """Test PaymentMethod validation rejects short card number."""
    with pytest.raises(ValueError):
        PaymentMethod(
            card_number=CARD_NUMBER_INVALID,
            card_name=CARD_NAME,
            expiry_date=EXPIRY_DATE,
            cvv=CVV,
            billing_zip=BILLING_ZIP
        )


def test_payment_method_invalid_expiry_format():
    """Test PaymentMethod validation rejects invalid expiry format."""
    with pytest.raises(ValueError):
        PaymentMethod(
            card_number=CARD_NUMBER_VALID,
            card_name=CARD_NAME,
            expiry_date=EXPIRY_DATE_INVALID,
            cvv=CVV,
            billing_zip=BILLING_ZIP
        )


def test_payment_method_cvv_too_short():
    """Test PaymentMethod validation rejects short CVV."""
    with pytest.raises(ValueError):
        PaymentMethod(
            card_number=CARD_NUMBER_VALID,
            card_name=CARD_NAME,
            expiry_date=EXPIRY_DATE,
            cvv=CVV_INVALID,
            billing_zip=BILLING_ZIP
        )


def test_payment_method_billing_zip_too_short():
    """Test PaymentMethod validation rejects short ZIP code."""
    with pytest.raises(ValueError):
        PaymentMethod(
            card_number=CARD_NUMBER_VALID,
            card_name=CARD_NAME,
            expiry_date=EXPIRY_DATE,
            cvv=CVV,
            billing_zip=BILLING_ZIP_INVALID
        )


def test_payment_method_cardholder_name_too_short():
    """Test PaymentMethod validation rejects short cardholder name."""
    with pytest.raises(ValueError):
        PaymentMethod(
            card_number=CARD_NUMBER_VALID,
            card_name=CARD_NAME_INVALID,
            expiry_date=EXPIRY_DATE,
            cvv=CVV,
            billing_zip=BILLING_ZIP
        )


# ==================== ProcessPaymentRequest Validation Tests ====================

def test_create_valid_payment_request():
    """Test creating a valid payment request."""
    item = PurchaseItem(
        id=ITEM_ID_TOKENS,
        type=ITEM_TYPE_TOKENS,
        name=ITEM_NAME_TOKENS,
        description="Popular choice",
        price_cad=PRICE_CAD_TOKENS,
        tokens_received=TOKENS_RECEIVED
    )
    
    method = PaymentMethod(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE,
        cvv=CVV,
        billing_zip=BILLING_ZIP
    )
    
    request = ProcessPaymentRequest(
        purchase_item=item,
        payment_method=method
    )
    
    assert request.purchase_item.id == ITEM_ID_TOKENS
    assert request.payment_method.card_name == CARD_NAME


def test_create_rank_upgrade_payment_request():
    """Test creating a payment request for rank upgrade."""
    item = PurchaseItem(
        id=ITEM_ID_RANK,
        type=ITEM_TYPE_RANK,
        name=ITEM_NAME_RANK,
        description="Premium features",
        price_cad=PRICE_CAD_RANK,
        price_tokens=PRICE_TOKENS_RANK,
        rank_upgrade=RANK_UPGRADE
    )
    
    method = PaymentMethod(
        card_number=CARD_NUMBER_VALID,
        card_name=CARD_NAME,
        expiry_date=EXPIRY_DATE,
        cvv=CVV,
        billing_zip=BILLING_ZIP
    )
    
    request = ProcessPaymentRequest(
        purchase_item=item,
        payment_method=method
    )
    
    assert request.purchase_item.rank_upgrade == RANK_UPGRADE
    assert request.purchase_item.type == ITEM_TYPE_RANK