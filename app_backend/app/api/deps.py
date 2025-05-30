from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.services.supabase_client import supabase_client # Assuming supabase_client handles user fetching
from app.schemas.auth_schemas import UserResponse # Or a more detailed User model if needed
import httpx # Required for fetching Supabase JWKS

# This is a simplified JWT validation. For Supabase, you'd typically validate against their JWKS.
# Supabase provides its own mechanisms for user management via its API,
# and the token it issues is what we need to validate.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    if supabase_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized",
        )

    try:
        # The token received from Supabase client login IS the JWT.
        # We need to validate it. Supabase typically uses RS256.
        # For simplicity in this example, we're using Supabase's user fetch,
        # which implicitly validates the token on the Supabase side.
        # A more robust solution involves fetching Supabase's JWKS and validating the token locally.

        # user_response = supabase_client.auth.get_user(token) # This is how you get user with token
        # This call validates the token with Supabase and returns the user or an error

        # To make this testable without actual Supabase calls during unit tests for other endpoints,
        # and to demonstrate basic JWT structure:
        # We'll assume the token IS the user_id for this simplified mock example for protected routes.
        # IN A REAL APP: Decode and validate the JWT properly using Supabase's public key (JWKS).

        # Simplified approach for now: get_user will validate the token with Supabase
        user_data = supabase_client.auth.get_user(token) # this is a UserResponse object from supabase-py

        if not user_data or not user_data.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Adapt User object from Supabase to your UserResponse schema
        return UserResponse(id=str(user_data.user.id), email=user_data.user.email)

    except Exception as e: # Catch broader exceptions from Supabase client if session is invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
