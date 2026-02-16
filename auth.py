"""
Authentication Module for MNN Pipeline API

Provides JWT and OAuth2 authentication mechanisms alongside the existing API key authentication.
Supports token-based authentication with refresh tokens and role-based access control.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# HTTP Bearer scheme for general token auth
http_bearer = HTTPBearer(auto_error=False)


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: List[str] = []


class User(BaseModel):
    """User model for authentication."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class AuthService:
    """
    Authentication service providing JWT and OAuth2 functionality.

    Manages user authentication, token generation/validation, and role-based access control.
    """

    def __init__(self):
        """Initialize authentication service with in-memory user store."""
        # In production, replace with database backend
        self._users_db: Dict[str, UserInDB] = {}
        self._refresh_tokens: Dict[str, str] = {}  # token -> username

        # Create a default admin user for testing
        self._create_default_users()

    def _create_default_users(self):
        """Create default users for testing."""
        if os.getenv("CREATE_DEFAULT_USERS", "true").lower() == "true":
            # Admin user
            self.create_user(
                username="admin",
                password="admin123",
                email="admin@mnn.local",
                full_name="System Administrator",
                roles=["admin", "user"]
            )

            # Regular user
            self.create_user(
                username="user",
                password="user123",
                email="user@mnn.local",
                full_name="Regular User",
                roles=["user"]
            )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user from database by username."""
        return self._users_db.get(username)

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        roles: List[str] = None
    ) -> UserInDB:
        """
        Create a new user.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: User email address
            full_name: User's full name
            roles: List of role names (default: ["user"])

        Returns:
            Created user object

        Raises:
            ValueError: If username already exists
        """
        if username in self._users_db:
            raise ValueError(f"User '{username}' already exists")

        if roles is None:
            roles = ["user"]

        user = UserInDB(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=self.get_password_hash(password),
            roles=roles,
            disabled=False
        )

        self._users_db[username] = user
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authentication succeeds, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if user.disabled:
            return None
        return user

    def create_access_token(
        self,
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Token payload data
            expires_delta: Token expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, username: str) -> str:
        """
        Create a refresh token.

        Args:
            username: Username for the token

        Returns:
            Encoded JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        # Store refresh token
        self._refresh_tokens[encoded_jwt] = username

        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            TokenData if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Check token type
            if payload.get("type") != token_type:
                return None

            username: str = payload.get("sub")
            if username is None:
                return None

            user_id: str = payload.get("user_id")
            roles: List[str] = payload.get("roles", [])

            return TokenData(username=username, user_id=user_id, roles=roles)

        except JWTError:
            return None

    def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            token: Refresh token to revoke

        Returns:
            True if token was revoked, False if token not found
        """
        if token in self._refresh_tokens:
            del self._refresh_tokens[token]
            return True
        return False

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token if refresh token is valid, None otherwise
        """
        # Verify refresh token
        token_data = self.verify_token(refresh_token, token_type="refresh")
        if not token_data:
            return None

        # Check if token is in store
        if refresh_token not in self._refresh_tokens:
            return None

        # Get user
        user = self.get_user(token_data.username)
        if not user or user.disabled:
            return None

        # Create new access token
        access_token = self.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.username,
                "roles": user.roles
            }
        )

        return access_token


# Global auth service instance
_auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the global authentication service instance."""
    return _auth_service


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.

    Supports both OAuth2 password bearer and HTTP Bearer authentication.
    Returns None if authentication is disabled or token is invalid.

    Args:
        token: OAuth2 token from Authorization header
        credentials: HTTP Bearer credentials

    Returns:
        User object if authenticated, None otherwise

    Raises:
        HTTPException: If token is invalid (only when auth is required)
    """
    from config import config

    # If authentication is disabled, return None
    if not config.API_AUTH_ENABLED:
        return None

    # Try OAuth2 token first, then Bearer token
    token_str = token or (credentials.credentials if credentials else None)

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = get_auth_service()
    token_data = auth_service.verify_token(token_str, token_type="access")

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user(token_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return User(**user.dict())


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require authentication for an endpoint.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User object

    Raises:
        HTTPException: If user is not authenticated
    """
    from config import config

    if not config.API_AUTH_ENABLED:
        # Return a default user when auth is disabled
        return User(username="anonymous", roles=["user"])

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


async def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.

    Args:
        required_role: Role name required to access the endpoint

    Returns:
        Dependency function that checks user role
    """
    async def role_checker(current_user: User = Depends(require_auth)) -> User:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user

    return role_checker
