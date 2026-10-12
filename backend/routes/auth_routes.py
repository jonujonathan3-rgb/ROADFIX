
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import verify_admin_credentials, create_access_token, get_current_admin

router = APIRouter(
    prefix="/api/auth",
    tags=["Admin Authentication"]
)


@router.post("/login")
def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    valid_credentials = verify_admin_credentials(
        form_data.username,
        form_data.password
    )

    if not valid_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(form_data.username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 60
    }


@router.get("/me")
def get_admin_profile(admin_username: str = Depends(get_current_admin)):
    return {
        "authenticated": True,
        "username": admin_username,
        "role": "admin"
    }