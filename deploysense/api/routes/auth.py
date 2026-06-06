"""
DeploySense — Authentication Routes

ENDPOINTS (maps to architecture/03-api-definitions.md):
  POST   /auth/github           — Exchange GitHub OAuth code for JWT
  GET    /auth/me               — Get current authenticated user

FLOW:
  1. Frontend redirects user to GitHub:
     https://github.com/login/oauth/authorize?client_id=xxx&scope=repo,user:email
  2. User authorizes, GitHub redirects to frontend with ?code=xxx
  3. Frontend sends code to POST /auth/github
  4. Backend exchanges code → GitHub token → GitHub profile → JWT
  5. Frontend stores JWT, sends it as Bearer token on all requests
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deploysense.api.auth import (
    create_access_token,
    exchange_github_code,
    fetch_github_user,
    get_current_user,
)
from deploysense.database import get_db_session
from deploysense.logging import get_logger
from deploysense.models import User

logger = get_logger(__name__)

router = APIRouter()


# ─── Request/Response Schemas ────────────────────────────────────────────────

class GitHubAuthRequest(BaseModel):
    """OAuth authorization code from GitHub."""
    code: str


class AuthResponse(BaseModel):
    """JWT token response after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    user: "UserProfile"


class UserProfile(BaseModel):
    """Authenticated user profile."""
    id: uuid.UUID
    github_username: str
    email: str | None
    avatar_url: str | None
    role: str

    model_config = {"from_attributes": True}


# ─── POST /auth/github ──────────────────────────────────────────────────────

@router.post("/auth/github", response_model=AuthResponse)
async def github_auth(
    body: GitHubAuthRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Authenticate via GitHub OAuth.

    FLOW:
      1. Exchange authorization code for GitHub access token
      2. Fetch user profile from GitHub API
      3. Create or update user in our database
      4. Issue a JWT for subsequent API calls

    WHY create-or-update (upsert):
      A user may have logged in before. We update their email/avatar
      on every login to keep our data fresh.

    TRADEOFF: We don't store the GitHub access token in this implementation.
    For Phase 1 Sprint 1 webhook processing, we'll need to store it
    (encrypted) for background GitHub API calls.
    """
    # Step 1: Exchange code for token
    token_data = await exchange_github_code(body.code)
    github_token = token_data["access_token"]

    # Step 2: Fetch GitHub profile
    github_user = await fetch_github_user(github_token)

    # Step 3: Create or update user
    result = await db.execute(
        select(User).where(User.github_username == github_user["login"])
    )
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.email = github_user.get("email")
        user.avatar_url = github_user.get("avatar_url")
        logger.info("user_login", github_username=user.github_username)
    else:
        # Create new user
        user = User(
            github_username=github_user["login"],
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
            role="engineer",
        )
        db.add(user)
        await db.flush()
        logger.info("user_created", github_username=user.github_username)

    # Step 4: Issue JWT
    access_token = create_access_token(
        user_id=str(user.id),
        github_username=user.github_username,
    )

    return AuthResponse(
        access_token=access_token,
        user=UserProfile.model_validate(user),
    )


# ─── GET /auth/me ────────────────────────────────────────────────────────────

@router.get("/auth/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)) -> UserProfile:
    """
    Get the currently authenticated user's profile.

    PURPOSE: Frontend calls this on page load to verify the JWT
    is still valid and display user info in the navigation bar.
    """
    return UserProfile.model_validate(user)
