"""
Tests for authentication functionality.
"""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.models import UserCreate, UserLogin
from pydantic import ValidationError


class TestPasswordValidation:
    """Tests for password validation rules."""

    def test_valid_password(self):
        """Test that a valid password is accepted."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecureP@ssw0rd123!"
        )
        assert user.password == "SecureP@ssw0rd123!"

    def test_password_too_short(self):
        """Test that passwords under 12 characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="Short1!"
            )
        assert "at least 12" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_password_no_uppercase(self):
        """Test that passwords without uppercase letters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="lowercase123!@#"
            )
        assert "uppercase" in str(exc_info.value).lower()

    def test_password_no_lowercase(self):
        """Test that passwords without lowercase letters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="UPPERCASE123!@#"
            )
        assert "lowercase" in str(exc_info.value).lower()

    def test_password_no_digit(self):
        """Test that passwords without digits are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="NoDigitsHere!@#"
            )
        assert "digit" in str(exc_info.value).lower()

    def test_password_no_special_char(self):
        """Test that passwords without special characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="NoSpecialChar123"
            )
        assert "special" in str(exc_info.value).lower()


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test that valid emails are accepted."""
        user = UserCreate(
            email="valid.email@example.com",
            username="testuser",
            password="SecureP@ssw0rd123!"
        )
        assert user.email == "valid.email@example.com"

    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="SecureP@ssw0rd123!"
            )


class TestUserLogin:
    """Tests for user login validation."""

    def test_valid_login_data(self):
        """Test that valid login data is accepted."""
        login = UserLogin(
            email="test@example.com",
            password="anypassword123"
        )
        assert login.email == "test@example.com"

    def test_login_email_required(self):
        """Test that email is required for login."""
        with pytest.raises(ValidationError):
            UserLogin(password="somepassword")


class TestJWTHandler:
    """Tests for JWT token handling."""

    def test_create_and_verify_token(self, mock_env_vars):
        """Test token creation and verification."""
        from auth.jwt_handler import create_access_token, verify_token

        # Create token
        user_data = {"user_id": "test-user-123", "email": "test@example.com"}
        token = create_access_token(user_data)

        assert token is not None
        assert isinstance(token, str)

        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload.get("user_id") == "test-user-123"
        assert payload.get("email") == "test@example.com"

    def test_verify_invalid_token(self, mock_env_vars):
        """Test that invalid tokens are rejected."""
        from auth.jwt_handler import verify_token

        result = verify_token("invalid-token-string")
        assert result is None

    def test_token_expiration(self, mock_env_vars):
        """Test that expired tokens are handled correctly."""
        from auth.jwt_handler import create_access_token, verify_token
        from datetime import timedelta

        # Create token with very short expiration (already expired)
        user_data = {"user_id": "test-user-123"}
        token = create_access_token(user_data, expires_delta=timedelta(seconds=-1))

        # Should return None for expired token
        result = verify_token(token)
        assert result is None
