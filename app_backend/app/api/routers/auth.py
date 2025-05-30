from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth_schemas import UserCreate, UserLogin, Token, UserResponse
from app.services.supabase_client import supabase_client
from app.api.deps import get_current_user


router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")
    try:
        # Supabase handles password hashing automatically
        user_session = supabase_client.auth.sign_up({
            "email": user_in.email,
            "password": user_in.password,
        })
        # In supabase-py v1, sign_up returns a Session object which contains user details or an error.
        # In supabase-py v2 (alpha/beta), it might return a UserResponse object directly or similar.
        # Assuming user_session.user contains the user details upon successful signup.
        if user_session.user:
             # Supabase might require email confirmation. For this example, we assume direct creation.
            return UserResponse(id=str(user_session.user.id), email=user_session.user.email) # Corrected to use user_session.user.email
        elif user_session.error: # Check if there was an error object
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=user_session.error.message)
        else: # Should not happen if user or error is always present
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown error during registration")

    except Exception as e:
        # Catching generic exception for cases like network errors or unexpected Supabase responses
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": form_data.email,
            "password": form_data.password
        })
        if response.session and response.session.access_token:
            return Token(access_token=response.session.access_token, token_type="bearer")
        # In supabase-py v1, error is part of the response object directly if session is None.
        # In supabase-py v2, it might be response.error.
        # Checking response.error first, then response.message if error object itself is the message string
        elif hasattr(response, 'error') and response.error:
             detail_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail_message)
        else: # Fallback for other unexpected structures or if no session and no clear error
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown error during login or invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
