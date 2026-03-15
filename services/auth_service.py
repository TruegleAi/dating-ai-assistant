"""
Authentication Service for Munch AI Dating Assistant
Handles JWT token generation, password hashing, and user authentication
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY environment variable is required. "
        "Generate a secure key: openssl rand -hex 32"
    )
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


# ===================== PYDANTIC MODELS =====================

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user email
    user_id: int
    exp: datetime
    type: str  # "access" or "refresh"


class AuthResult(BaseModel):
    """Authentication result"""
    success: bool
    message: str
    token: Optional[Token] = None
    user_id: Optional[int] = None


# ===================== PASSWORD UTILITIES =====================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ===================== JWT TOKEN UTILITIES =====================

def create_access_token(email: str, user_id: int) -> Tuple[str, datetime]:
    """
    Create a JWT access token.

    Args:
        email: User's email address
        user_id: User's database ID

    Returns:
        Tuple of (token string, expiration datetime)
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "user_id": user_id,
        "exp": expires,
        "type": "access",
        "iat": now
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires


def create_refresh_token(email: str, user_id: int) -> Tuple[str, datetime]:
    """
    Create a JWT refresh token.

    Args:
        email: User's email address
        user_id: User's database ID

    Returns:
        Tuple of (token string, expiration datetime)
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "user_id": user_id,
        "exp": expires,
        "type": "refresh",
        "iat": now
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires


def create_tokens(email: str, user_id: int) -> Token:
    """
    Create both access and refresh tokens.

    Args:
        email: User's email address
        user_id: User's database ID

    Returns:
        Token object with both tokens
    """
    access_token, _ = create_access_token(email, user_id)
    refresh_token, _ = create_refresh_token(email, user_id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Validate token type
        if payload.get("type") != token_type:
            return None

        # Validate expiration (use UTC timezone-aware datetime)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            return None

        return TokenPayload(
            sub=payload["sub"],
            user_id=payload["user_id"],
            exp=exp,
            type=payload["type"]
        )
    except JWTError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[Token]:
    """
    Create a new access token using a refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        New Token object if refresh token is valid, None otherwise
    """
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        return None

    return create_tokens(payload.sub, payload.user_id)


# ===================== AUTH SERVICE CLASS =====================

class AuthService:
    """
    Authentication service for user management.
    Handles registration, login, and token operations.
    """

    def __init__(self, db_service):
        """
        Initialize AuthService with database service.

        Args:
            db_service: DatabaseService instance for user operations
        """
        self.db_service = db_service

    def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        subscription_tier: str = "free"
    ) -> AuthResult:
        """
        Register a new user with email and password.

        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            username: Optional username
            subscription_tier: Subscription level (free/premium)

        Returns:
            AuthResult with success status and tokens if successful
        """
        # Check if user already exists
        existing_user = self.db_service.get_user_by_email(email)
        if existing_user:
            return AuthResult(
                success=False,
                message="Email already registered"
            )

        # Validate password
        if len(password) < 8:
            return AuthResult(
                success=False,
                message="Password must be at least 8 characters"
            )

        # Hash password and create user
        password_hash = hash_password(password)

        try:
            user = self.db_service.create_user_with_password(
                email=email,
                password_hash=password_hash,
                username=username,
                subscription_tier=subscription_tier
            )

            # Generate tokens
            tokens = create_tokens(user.email, user.id)

            return AuthResult(
                success=True,
                message="User registered successfully",
                token=tokens,
                user_id=user.id
            )
        except Exception as e:
            return AuthResult(
                success=False,
                message=f"Registration failed: {str(e)}"
            )

    def login(self, email: str, password: str) -> AuthResult:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            AuthResult with success status and tokens if successful
        """
        # Get user
        user = self.db_service.get_user_by_email(email)
        if not user:
            return AuthResult(
                success=False,
                message="Invalid email or password"
            )

        # Check if user is active
        if hasattr(user, 'is_active') and not user.is_active:
            return AuthResult(
                success=False,
                message="Account is disabled"
            )

        # Verify password
        if not user.password_hash:
            return AuthResult(
                success=False,
                message="No password set. Please use OAuth or reset password."
            )

        if not verify_password(password, user.password_hash):
            return AuthResult(
                success=False,
                message="Invalid email or password"
            )

        # Generate tokens
        tokens = create_tokens(user.email, user.id)

        return AuthResult(
            success=True,
            message="Login successful",
            token=tokens,
            user_id=user.id
        )

    def refresh(self, refresh_token: str) -> AuthResult:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            AuthResult with new tokens if successful
        """
        tokens = refresh_access_token(refresh_token)
        if not tokens:
            return AuthResult(
                success=False,
                message="Invalid or expired refresh token"
            )

        # Verify user still exists and is active
        payload = verify_token(refresh_token, token_type="refresh")
        if payload:
            user = self.db_service.get_user_by_email(payload.sub)
            if not user:
                return AuthResult(
                    success=False,
                    message="User not found"
                )
            if hasattr(user, 'is_active') and not user.is_active:
                return AuthResult(
                    success=False,
                    message="Account is disabled"
                )

        return AuthResult(
            success=True,
            message="Token refreshed successfully",
            token=tokens,
            user_id=payload.user_id if payload else None
        )

    def change_password(self, user_id: int, old_password: str, new_password: str) -> AuthResult:
        """
        Change user's password.

        Args:
            user_id: User's database ID
            old_password: Current password
            new_password: New password

        Returns:
            AuthResult with success status
        """
        user = self.db_service.get_user_by_id(user_id)
        if not user:
            return AuthResult(
                success=False,
                message="User not found"
            )

        # Verify old password
        if not user.password_hash or not verify_password(old_password, user.password_hash):
            return AuthResult(
                success=False,
                message="Current password is incorrect"
            )

        # Validate new password
        if len(new_password) < 8:
            return AuthResult(
                success=False,
                message="New password must be at least 8 characters"
            )

        # Update password
        new_hash = hash_password(new_password)
        success = self.db_service.update_user_password(user_id, new_hash)

        if success:
            return AuthResult(
                success=True,
                message="Password changed successfully"
            )
        else:
            return AuthResult(
                success=False,
                message="Failed to update password"
            )


# ===================== SINGLETON INSTANCE =====================

_auth_service_instance: Optional[AuthService] = None


def get_auth_service(db_service=None) -> AuthService:
    """
    Get or create AuthService singleton instance.

    Args:
        db_service: DatabaseService instance (required on first call)

    Returns:
        AuthService instance
    """
    global _auth_service_instance

    if _auth_service_instance is None:
        if db_service is None:
            from services.database_service import get_database_service
            db_service = get_database_service()
        _auth_service_instance = AuthService(db_service)

    return _auth_service_instance
