import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from infrastructure.db.postgres.auth_repo import AuthRepository
from api.dependencies import get_auth_repo

router = APIRouter()


class RequestLinkBody(BaseModel):
    email: EmailStr


class VerifyBody(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    household_id: str
    email: str
    is_onboarded: bool


@router.post("/request-link", status_code=204)
async def request_link(
    body: RequestLinkBody,
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repo)],
) -> None:
    household = await auth_repo.get_or_create_household(body.email)
    token = await auth_repo.create_magic_token(household.id)

    app_url = os.environ.get("APP_URL", "http://localhost:5173")
    magic_link = f"{app_url}/auth/verify?token={token}"

    if os.environ.get("ENVIRONMENT", "development") == "development":
        print(f"\n[DEV] Magic link for {body.email}:\n{magic_link}\n")
    else:
        import resend
        resend.api_key = os.environ["RESEND_API_KEY"]
        from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        resend.Emails.send({
            "from": f"Dinner Solved <{from_email}>",
            "to": [body.email],
            "subject": "Your Dinner Solved sign-in link",
            "html": (
                f"<p>Click the link below to sign in to Dinner Solved. "
                f"It expires in 15 minutes.</p>"
                f'<p><a href="{magic_link}">Sign in</a></p>'
                f"<p>Or copy this URL: {magic_link}</p>"
            ),
        })


@router.post("/verify", response_model=VerifyResponse)
async def verify_token(
    body: VerifyBody,
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repo)],
) -> VerifyResponse:
    result = await auth_repo.validate_and_consume_token(body.token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    household_id, email = result
    is_onboarded = await auth_repo.has_meal_template(household_id)
    return VerifyResponse(household_id=str(household_id), email=email, is_onboarded=is_onboarded)
