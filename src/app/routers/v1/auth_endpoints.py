from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.database import async_get_db
from app.domain.token_blacklist.models import Token
from app.services.security import get_token

router = APIRouter(tags=["auth"])


@router.post("/login")
async def login_user(
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Token:
    return await get_token(response, db, form)
