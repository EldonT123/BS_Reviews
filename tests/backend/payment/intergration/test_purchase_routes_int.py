# tests/backend/payment/integration/test_purchase_integration.py
"""
Integration tests for purchase routes and service
Tests complete workflows and API interactions using in-memory storage
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from io import StringIO
from fastapi.testclient import TestClient
from backend.main import app
from backend.services import user_service
from backend.models.user_model import User

client = TestClient(app)


# ==================== Test Constants ====================

# User Details
TEST_EMAIL = "test@example.com"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "TestPassword123!"

WORKFLOW_EMAIL = "workflow@example.com"
WORKFLOW_USERNAME = "workflowuser"
WORKFLOW_PASSWORD = "TestPassword123!"

# Card Details
CARD_NUMBER_VALID = "4532015112830366"
CARD_NUMBER_INVALID = "123"
CARD_NAME = "John Doe"
CARD_NAME_ALT = "Jane Doe"
EXPIRY_DATE = "12/25"
CVV = "123"
CVV_ALT = "456"
BILLING_ZIP = "12345"
BILLING_ZIP_ALT = "54321"

# Item IDs
ITEM_ID_TOKENS_100 = "tokens_100"
ITEM_ID_TOKENS_500 = "tokens_500"
ITEM_ID_RANK_SLUG = "rank_slug"
ITEM_ID_RANK_BANANA = "rank_banana_slug"

# Item Names
ITEM_NAME_TOKENS_100 = "100 Tokens"
ITEM_NAME_TOKENS_500 = "500 Tokens"
ITEM_NAME_RANK_SLUG = "Upgrade to Slug"
ITEM_NAME_RANK_BANANA = "Upgrade to Banana Slug"

# Item Types
ITEM_TYPE_TOKENS = "tokens"
ITEM_TYPE_RANK = "rank"

# Prices
PRICE_CAD_TOKENS_100 = 4.99
PRICE_CAD_TOKENS_500 = 19.99
PRICE_CAD_RANK_SLUG = 9.99
PRICE_CAD_RANK_BANANA = 19.99

# Tokens
TOKENS_RECEIVED_100 = 100
TOKENS_RECEIVED_500 = 500

# Descriptions
DESC_TOKENS = "Test"
DESC_TOKENS_POPULAR = "Popular choice - 10% bonus!"

# API Status Codes
STATUS_OK = 200
STATUS_UNAUTHORIZED = 401
STATUS_VALIDATION_ERROR = 422


# ==================== In-Memory Storage ====================

class InMemoryUserStorage:
    """In-memory storage for user data during tests."""
    def __init__(self):
        self.users = {}  # email -> (username, password_hash, tier)
    
    def add_user(self, email, username, password_hash, tier):
        self.users[email.lower()] = (username, password_hash, tier)
    
    def get_user(self, email):
        return self.users.get(email.lower())
    
    def user_exists(self, email):
        return email.lower() in self.users
    
    def to_csv(self):
        """Convert to CSV format for mocking file reads."""
        lines = ["user_email,username,user_password,user_tier\n"]
        for email, (username, pwd_hash, tier) in self.users.items():
            lines.append(f"{email},{username},{pwd_hash},{tier}\n")
        return "".join(lines)
    
    def clear(self):
        self.users.clear()


class InMemoryPurchaseStorage:
    """In-memory storage for purchase data during tests."""
    def __init__(self):
        self.purchases = []
    
    def add_purchase(self, purchase_data):
        self.purchases.append(purchase_data)
    
    def to_csv(self):
        """Convert to CSV format for mocking file reads."""
        if not self.purchases:
            return "purchase_id,user_email,item_id,item_type,item_name,amount_cad,amount_tokens,payment_method_last4,tokens_received,rank_upgrade,purchase_date,status,transaction_id\n"
        
        lines = ["purchase_id,user_email,item_id,item_type,item_name,amount_cad,amount_tokens,payment_method_last4,tokens_received,rank_upgrade,purchase_date,status,transaction_id\n"]
        for p in self.purchases:
            lines.append(f"{p[0]},{p[1]},{p[2]},{p[3]},{p[4]},{p[5]},{p[6]},{p[7]},{p[8]},{p[9]},{p[10]},{p[11]},{p[12]}\n")
        return "".join(lines)
    
    def clear(self):
        self.purchases.clear()


# ==================== Global Storage ====================
user_storage = InMemoryUserStorage()
purchase_storage = InMemoryPurchaseStorage()


# ==================== Fixtures ====================

@pytest.fixture(autouse=True)
def reset_all_storage():
    """Reset all in-memory storage before each test."""
    user_service.user_sessions.clear()
    user_service.session_ids.clear()
    user_storage.clear()
    purchase_storage.clear()
    yield
    user_service.user_sessions.clear()
    user_service.session_ids.clear()
    user_storage.clear()
    purchase_storage.clear()


@pytest.fixture
def mock_user_csv():
    """Mock user service CSV operations with in-memory storage."""
    def mock_read_users():
        """Mock read_users to return in-memory data."""
        users = {}
        csv_content = user_storage.to_csv()
        lines = csv_content.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line:
                parts = line.split(',')
                email = parts[0].lower()
                username = parts[1]
                password_hash = parts[2]
                tier = parts[3] if len(parts) > 3 else User.TIER_SNAIL
                users[email] = (username, password_hash, tier)
        return users
    
    def mock_save_user(email, username, password_hash, tier=User.TIER_SNAIL):
        """Mock save_user to store in memory."""
        user_storage.add_user(email, username, password_hash, tier)
    
    with patch('backend.services.user_service.read_users', side_effect=mock_read_users), \
         patch('backend.services.user_service.save_user', side_effect=mock_save_user), \
         patch('backend.services.user_service.ensure_user_csv_exists'):
        yield


@pytest.fixture
def mock_purchase_csv():
    """Mock purchase service CSV operations with in-memory storage."""
    def mock_save_purchase(purchase):
        """Mock save_purchase to store in memory."""
        purchase_storage.add_purchase([
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
    
    def mock_get_purchase_history(email):
        """Mock get_user_purchase_history to return in-memory data."""
        from backend.models.purchase_model import Purchase
        from datetime import datetime
        
        purchases = []
        for p in purchase_storage.purchases:
            if p[1].lower() == email.lower():
                purchase = Purchase(
                    purchase_id=p[0],
                    user_email=p[1],
                    item_id=p[2],
                    item_type=p[3],
                    item_name=p[4],
                    amount_cad=float(p[5]) if p[5] else None,
                    amount_tokens=int(p[6]) if p[6] else None,
                    payment_method_last4=p[7] if p[7] else None,
                    tokens_received=int(p[8]) if p[8] else None,
                    rank_upgrade=p[9] if p[9] else None,
                    purchase_date=datetime.fromisoformat(p[10]),
                    status=p[11],
                    transaction_id=p[12] if p[12] else None
                )
                purchases.append(purchase)
        return purchases
    
    with patch('backend.services.purchase_service.save_purchase', side_effect=mock_save_purchase), \
         patch('backend.services.purchase_service.get_user_purchase_history', side_effect=mock_get_purchase_history), \
         patch('backend.services.purchase_service.ensure_purchase_csv_exists'):
        yield


@pytest.fixture
def authenticated_user(mock_user_csv):
    """Create an authenticated user and return session ID."""
    user_service.create_user(
        email=TEST_EMAIL,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        tier=User.TIER_SNAIL
    )
    
    _, session_id = user_service.authenticate_user(
        email=TEST_EMAIL,
        password=TEST_PASSWORD
    )
    
    return {
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "session_id": session_id
    }


# ==================== Helper Functions ====================

def create_payment_request(
    item_id,
    item_type,
    item_name,
    description,
    price_cad,
    tokens_received=None,
    rank_upgrade=None,
    card_number=CARD_NUMBER_VALID,
    card_name=CARD_NAME,
    expiry_date=EXPIRY_DATE,
    cvv=CVV,
    billing_zip=BILLING_ZIP
):
    """Helper function to create a payment request JSON."""
    purchase_item = {
        "id": item_id,
        "type": item_type,
        "name": item_name,
        "description": description,
        "price_cad": price_cad
    }
    
    if tokens_received:
        purchase_item["tokens_received"] = tokens_received
    if rank_upgrade:
        purchase_item["rank_upgrade"] = rank_upgrade
    
    return {
        "purchase_item": purchase_item,
        "payment_method": {
            "card_number": card_number,
            "card_name": card_name,
            "expiry_date": expiry_date,
            "cvv": cvv,
            "billing_zip": billing_zip
        }
    }


# ==================== Available Items Route Tests ====================

class TestGetAvailableItems:
    """Test the available items endpoint."""
    
    def test_get_available_items_returns_token_packages(self):
        """Test that available items endpoint returns token packages."""
        response = client.get("/api/store/available-items")
        
        assert response.status_code == STATUS_OK
        data = response.json()
        assert "token_packages" in data
        assert len(data["token_packages"]) >= 3
    
    def test_get_available_items_returns_rank_upgrades(self):
        """Test that available items endpoint returns rank upgrades."""
        response = client.get("/api/store/available-items")
        
        assert response.status_code == STATUS_OK
        data = response.json()
        assert "rank_upgrades" in data
        assert len(data["rank_upgrades"]) >= 2
    
    def test_token_package_structure(self):
        """Test that token packages have correct structure."""
        response = client.get("/api/store/available-items")
        data = response.json()
        
        token_package = data["token_packages"][0]
        assert "id" in token_package
        assert "type" in token_package
        assert "name" in token_package
        assert "description" in token_package
        assert "price_cad" in token_package
        assert "tokens_received" in token_package
        assert token_package["type"] == ITEM_TYPE_TOKENS
    
    def test_rank_upgrade_structure(self):
        """Test that rank upgrades have correct structure."""
        response = client.get("/api/store/available-items")
        data = response.json()
        
        rank_upgrade = data["rank_upgrades"][0]
        assert "id" in rank_upgrade
        assert "type" in rank_upgrade
        assert "name" in rank_upgrade
        assert "description" in rank_upgrade
        assert "price_cad" in rank_upgrade
        assert "rank_upgrade" in rank_upgrade
        assert rank_upgrade["type"] == ITEM_TYPE_RANK


# ==================== Process Payment Route Tests ====================

class TestProcessPayment:
    """Test the process payment endpoint."""
    
    def test_process_payment_missing_authorization(self):
        """Test that payment fails without authorization header."""
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_500,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_500,
            description=DESC_TOKENS,
            price_cad=PRICE_CAD_TOKENS_500,
            tokens_received=TOKENS_RECEIVED_500
        )
        
        response = client.post(
            "/api/store/process-payment",
            json=payment_request
        )
        
        assert response.status_code == STATUS_UNAUTHORIZED
        assert "Missing or invalid authorization" in response.json()["detail"]
    
    def test_process_payment_invalid_session(self):
        """Test that payment fails with invalid session."""
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_500,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_500,
            description=DESC_TOKENS,
            price_cad=PRICE_CAD_TOKENS_500,
            tokens_received=TOKENS_RECEIVED_500
        )
        
        response = client.post(
            "/api/store/process-payment",
            headers={"Authorization": "Bearer invalid_session"},
            json=payment_request
        )
        
        assert response.status_code == STATUS_UNAUTHORIZED
        assert "Invalid or expired session" in response.json()["detail"]
    
    def test_process_payment_token_purchase_success(self, mock_user_csv, mock_purchase_csv, authenticated_user):
        """Test successful token purchase."""
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_500,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_500,
            description=DESC_TOKENS_POPULAR,
            price_cad=PRICE_CAD_TOKENS_500,
            tokens_received=TOKENS_RECEIVED_500
        )
        
        response = client.post(
            "/api/store/process-payment",
            headers={"Authorization": f"Bearer {authenticated_user['session_id']}"},
            json=payment_request
        )
        
        assert response.status_code == STATUS_OK
        data = response.json()
        assert data["success"] is True
        assert "purchase_id" in data
        assert data["purchase_id"].startswith("PUR-")
        assert data["tokens_added"] == TOKENS_RECEIVED_500
    
    def test_process_payment_invalid_card(self, mock_user_csv, mock_purchase_csv, authenticated_user):
        """Test payment fails with invalid card."""
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_500,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_500,
            description=DESC_TOKENS,
            price_cad=PRICE_CAD_TOKENS_500,
            tokens_received=TOKENS_RECEIVED_500,
            card_number=CARD_NUMBER_INVALID
        )
        
        response = client.post(
            "/api/store/process-payment",
            headers={"Authorization": f"Bearer {authenticated_user['session_id']}"},
            json=payment_request
        )
        
        assert response.status_code == STATUS_VALIDATION_ERROR
    
    def test_process_payment_100_tokens_purchase(self, mock_user_csv, mock_purchase_csv, authenticated_user):
        """Test purchasing 100 tokens package."""
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_100,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_100,
            description=DESC_TOKENS,
            price_cad=PRICE_CAD_TOKENS_100,
            tokens_received=TOKENS_RECEIVED_100
        )
        
        response = client.post(
            "/api/store/process-payment",
            headers={"Authorization": f"Bearer {authenticated_user['session_id']}"},
            json=payment_request
        )
        
        assert response.status_code == STATUS_OK
        data = response.json()
        assert data["tokens_added"] == TOKENS_RECEIVED_100


# ==================== Purchase History Route Tests ====================

class TestGetPurchaseHistory:
    """Test the purchase history endpoint."""
    
    def test_get_purchase_history_missing_authorization(self):
        """Test that history request fails without authorization."""
        response = client.get("/api/store/purchase-history")
        
        assert response.status_code == STATUS_UNAUTHORIZED
        assert "Missing or invalid authorization" in response.json()["detail"]
    
    def test_get_purchase_history_invalid_session(self):
        """Test that history request fails with invalid session."""
        response = client.get(
            "/api/store/purchase-history",
            headers={"Authorization": "Bearer invalid_session"}
        )
        
        assert response.status_code == STATUS_UNAUTHORIZED
    
    def test_get_purchase_history_empty(self, mock_user_csv, mock_purchase_csv, authenticated_user):
        """Test getting purchase history for user with no purchases."""
        response = client.get(
            "/api/store/purchase-history",
            headers={"Authorization": f"Bearer {authenticated_user['session_id']}"}
        )
        
        assert response.status_code == STATUS_OK
        data = response.json()
        assert "purchases" in data
        assert len(data["purchases"]) == 0
    
    def test_get_purchase_history_after_single_purchase(self, mock_user_csv, mock_purchase_csv, authenticated_user):
        """Test getting purchase history after making a single purchase."""
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_500,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_500,
            description=DESC_TOKENS,
            price_cad=PRICE_CAD_TOKENS_500,
            tokens_received=TOKENS_RECEIVED_500
        )
        
        # Make a purchase
        client.post(
            "/api/store/process-payment",
            headers={"Authorization": f"Bearer {authenticated_user['session_id']}"},
            json=payment_request
        )
        
        # Get purchase history
        response = client.get(
            "/api/store/purchase-history",
            headers={"Authorization": f"Bearer {authenticated_user['session_id']}"}
        )
        
        assert response.status_code == STATUS_OK
        data = response.json()
        assert len(data["purchases"]) >= 1
        
        purchase = data["purchases"][0]
        assert purchase["item_type"] == ITEM_TYPE_TOKENS
        assert purchase["tokens_received"] == TOKENS_RECEIVED_500
        assert purchase["status"] == "completed"


# ==================== Complete Purchase Workflow Tests ====================

class TestCompletePurchaseWorkflow:
    """Test complete purchase workflows."""
    
    def test_token_purchase_workflow(self, mock_user_csv, mock_purchase_csv):
        """Test complete workflow: signup -> login -> purchase."""
        # Signup
        signup_response = client.post(
            "/api/users/signup",
            json={
                "email": WORKFLOW_EMAIL,
                "username": WORKFLOW_USERNAME,
                "password": WORKFLOW_PASSWORD
            }
        )
        assert signup_response.status_code == STATUS_OK
        
        # Login
        login_response = client.post(
            "/api/users/login",
            json={
                "email": WORKFLOW_EMAIL,
                "password": WORKFLOW_PASSWORD
            }
        )
        assert login_response.status_code == STATUS_OK
        session_id = login_response.json()["session_id"]
        
        # Get available items
        items_response = client.get("/api/store/available-items")
        assert items_response.status_code == STATUS_OK
        
        # Purchase tokens
        payment_request = create_payment_request(
            item_id=ITEM_ID_TOKENS_100,
            item_type=ITEM_TYPE_TOKENS,
            item_name=ITEM_NAME_TOKENS_100,
            description=DESC_TOKENS,
            price_cad=PRICE_CAD_TOKENS_100,
            tokens_received=TOKENS_RECEIVED_100,
            card_name=CARD_NAME_ALT,
            cvv=CVV_ALT,
            billing_zip=BILLING_ZIP_ALT
        )
        
        purchase_response = client.post(
            "/api/store/process-payment",
            headers={"Authorization": f"Bearer {session_id}"},
            json=payment_request
        )
        assert purchase_response.status_code == STATUS_OK
        purchase_data = purchase_response.json()
        assert purchase_data["success"] is True
        assert purchase_data["tokens_added"] == TOKENS_RECEIVED_100