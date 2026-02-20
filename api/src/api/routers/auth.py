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
        resend.Emails.send({
            "from": "Dinner Solved <noreply@dinner-solved.app>",
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
    household_id = await auth_repo.validate_and_consume_token(body.token)
    if household_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return VerifyResponse(household_id=str(household_id))
