"""
Purchase Service - Business logic for handling purchases
"""
import csv
import os
import secrets
from datetime import datetime
from typing import Optional
from backend.models.purchase_model import Purchase, PurchaseItem, PaymentMethod
from backend.services import user_service

# Path configuration
PURCHASE_CSV_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../database/users/purchase_history.csv"
    )
)


def ensure_purchase_csv_exists():
    """Ensure the directory and
         CSV file exist, and create headers if missing."""
    os.makedirs(os.path.dirname(PURCHASE_CSV_PATH), exist_ok=True)
    if not os.path.exists(PURCHASE_CSV_PATH):
        with open(PURCHASE_CSV_PATH,
                  "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "purchase_id", "user_email", "item_id", "item_type",
                "item_name", "amount_cad", "amount_tokens",
                "payment_method_last4", "tokens_received", "rank_upgrade",
                "purchase_date", "status", "transaction_id"
            ])


def generate_purchase_id() -> str:
    """Generate a unique purchase ID"""
    return f"PUR-{secrets.token_hex(8).upper()}"


def generate_transaction_id() -> str:
    """Generate a mock transaction ID
        (in production, this would come from payment processor)"""
    return f"TXN-{secrets.token_hex(12).upper()}"


def process_payment(
    card_number: str,
    card_name: str,
    expiry_date: str,
    cvv: str,
    billing_zip: str,
    amount: float
) -> tuple[bool, Optional[str]]:
    """
    Process payment through payment gateway (mock implementation)

    In production, this would integrate with Stripe, PayPal, etc.
    For now, this is a mock that always succeeds.

    Returns:
        tuple[bool, Optional[str]]: (success, transaction_id or error_message)
    """
    # Mock validation - in production, this would call real payment processor

    # Basic validation
    if len(card_number.replace(" ", "")) < 13:
        return False, "Invalid card number"

    if len(cvv) < 3:
        return False, "Invalid CVV"

    # Check expiry date
    try:
        month, year = expiry_date.split("/")
        month = int(month)
        year = int(year) + 2000  # Convert YY to YYYY

        if month < 1 or month > 12:
            return False, "Invalid expiry date"

        # Simple expiry check (should be more sophisticated in production)
        current_year = datetime.now().year
        current_month = datetime.now().month

        if year < current_year or (
                year == current_year and month < current_month):
            return False, "Card has expired"

    except (ValueError, IndexError):
        return False, "Invalid expiry date format"

    # Mock successful payment
    transaction_id = generate_transaction_id()
    return True, transaction_id


def save_purchase(purchase: Purchase) -> bool:
    """Save a purchase to the CSV file"""
    ensure_purchase_csv_exists()

    try:
        with open(PURCHASE_CSV_PATH,
                  "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                purchase.purchase_id,
                purchase.user_email,
                purchase.item_id,
                purchase.item_type,
                purchase.item_name,
                purchase.amount_cad or "",
                purchase.amount_tokens or "",
                purchase.payment_method_last4 or "",
                purchase.tokens_received or "",
                purchase.rank_upgrade or "",
                purchase.purchase_date.isoformat(),
                purchase.status,
                purchase.transaction_id or ""
            ])
        return True
    except Exception as e:
        print(f"Error saving purchase: {e}")
        return False


def add_tokens_to_user(user_email: str, tokens: int) -> bool:
    """
    Add tokens to a user's balance.

    Args:
        user_email: User's email address
        tokens: Number of tokens to add

    Returns:
        True if successful, False otherwise
    """
    try:
        # Simply call the user_service function - it already handles everything
        return user_service.add_tokens_to_user(user_email, tokens)
    except Exception as e:
        print(f"Error adding tokens to user: {e}")
        return False


def process_purchase_with_cad(
    user_email: str,
    purchase_item: PurchaseItem,
    payment_method: PaymentMethod
) -> tuple[bool, str, Optional[Purchase]]:
    """
    Process a purchase using CAD (real money)

    Returns:
        tuple[bool, str, Optional[Purchase]]:
          (success, message, purchase_object)
    """
    # Validate that item can be purchased with CAD
    if purchase_item.price_cad is None:
        return False, "This item cannot be purchased with CAD", None

    # Validate user exists
    user = user_service.get_user_by_email(user_email)
    if not user:
        return False, "User not found", None

    # Process payment
    success, result = process_payment(
        card_number=payment_method.card_number,
        card_name=payment_method.card_name,
        expiry_date=payment_method.expiry_date,
        cvv=payment_method.cvv,
        billing_zip=payment_method.billing_zip,
        amount=purchase_item.price_cad
    )

    if not success:
        return False, f"Payment failed: {result}", None

    transaction_id = result

    # Create purchase record
    purchase = Purchase(
        purchase_id=generate_purchase_id(),
        user_email=user_email,
        item_id=purchase_item.id,
        item_type=purchase_item.type,
        item_name=purchase_item.name,
        amount_cad=purchase_item.price_cad,
        payment_method_last4=payment_method.card_number[-4:],
        tokens_received=purchase_item.tokens_received,
        rank_upgrade=purchase_item.rank_upgrade,
        purchase_date=datetime.now(),
        status="completed",
        transaction_id=transaction_id
    )

    # Save purchase to history
    if not save_purchase(purchase):
        return False, "Failed to save purchase record", None

    # Apply purchase effects
    try:
        # If purchasing tokens, add them to user's balance
        if purchase_item.tokens_received:
            add_tokens_to_user(user_email, purchase_item.tokens_received)

        # If purchasing rank upgrade, update user's tier
        if purchase_item.rank_upgrade:
            success = user_service.update_user_tier(
                email=user_email,
                new_tier=purchase_item.rank_upgrade
            )
            if not success:
                return False, "Failed to apply rank upgrade", None

        return True, "Purchase completed successfully", purchase

    except Exception as e:
        print(f"Error applying purchase effects: {e}")
        return False, {
            "Purchase completed but failed to apply benefits", purchase}


def process_purchase_with_tokens(
    user_email: str,
    purchase_item: PurchaseItem
) -> tuple[bool, str, Optional[Purchase]]:
    """
    Process a purchase using tokens (in-game currency)

    Returns:
        tuple[bool, str, Optional[Purchase]]:
          (success, message, purchase_object)
    """
    # Validate that item can be purchased with tokens
    if purchase_item.price_tokens is None:
        return False, "This item cannot be purchased with tokens", None

    # Validate user exists and get current token balance
    user = user_service.get_user_by_email(user_email)
    if not user:
        return False, "User not found", None

    # Check if user has sufficient tokens
    user_tokens = user.tokens if user.tokens else 0
    if user_tokens < purchase_item.price_tokens:
        return False, f"Insufficient tokens. You have {
            user_tokens} but need {purchase_item.price_tokens}", None

    # Create purchase record
    purchase = Purchase(
        purchase_id=generate_purchase_id(),
        user_email=user_email,
        item_id=purchase_item.id,
        item_type=purchase_item.type,
        item_name=purchase_item.name,
        amount_tokens=purchase_item.price_tokens,
        tokens_received=purchase_item.tokens_received,
        rank_upgrade=purchase_item.rank_upgrade,
        purchase_date=datetime.now(),
        status="completed",
        transaction_id=generate_transaction_id()
    )

    # Save purchase to history
    if not save_purchase(purchase):
        return False, "Failed to save purchase record", None

    # Apply purchase effects
    try:
        # Deduct tokens from user
        deduct_success = user_service.deduct_tokens_from_user(
            user_email, purchase_item.price_tokens)
        if not deduct_success:
            return False, "Failed to deduct tokens from user", None

        # If purchasing rank upgrade, update user's tier
        if purchase_item.rank_upgrade:
            success = user_service.update_user_tier(
                email=user_email,
                new_tier=purchase_item.rank_upgrade
            )
            if not success:
                return False, "Failed to apply rank upgrade", None

        return True, "Purchase completed successfully", purchase

    except Exception as e:
        print(f"Error applying purchase effects: {e}")
        return False, {
            "Purchase completed but failed to apply benefits", purchase}


def get_user_purchase_history(
        user_email: str) -> list[Purchase]:
    """Get all purchases for a user"""
    purchases = []

    if not os.path.exists(PURCHASE_CSV_PATH):
        return purchases

    try:
        with open(PURCHASE_CSV_PATH,
                  "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["user_email"].lower() == user_email.lower():
                    purchase = Purchase(
                        purchase_id=row["purchase_id"],
                        user_email=row["user_email"],
                        item_id=row["item_id"],
                        item_type=row["item_type"],
                        item_name=row["item_name"],
                        amount_cad=float(row["amount_cad"])
                        if row["amount_cad"] else None,
                        amount_tokens=int(row["amount_tokens"])
                        if row["amount_tokens"] else None,
                        payment_method_last4=row["payment_method_last4"]
                        if row["payment_method_last4"] else None,
                        tokens_received=int(row["tokens_received"])
                        if row["tokens_received"] else None,
                        rank_upgrade=row["rank_upgrade"]
                        if row["rank_upgrade"] else None,
                        purchase_date=datetime.fromisoformat(
                            row["purchase_date"]),
                        status=row["status"],
                        transaction_id=row["transaction_id"]
                        if row["transaction_id"] else None
                    )
                    purchases.append(purchase)
    except Exception as e:
        print(f"Error reading purchase history: {e}")

    return purchases
