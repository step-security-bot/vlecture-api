from fastapi import (
    APIRouter,
    Response,
    Depends,
    Body,
)
from sqlalchemy import Enum
from sqlalchemy.orm import Session

from src.utils.db import get_db
from src.schemas.auth import RegisterSchema, LoginSchema
from src.services import auth


class AuthRouterTags(Enum):
    auth = "auth"


auth_router = APIRouter(prefix="/v1/auth", tags=[AuthRouterTags.auth])


@auth_router.post("/register", tags=[AuthRouterTags.auth])
def register(payload: RegisterSchema = Body(), session: Session = Depends(get_db)):
    """Processes request to register user account."""
    return auth.register(session, payload=payload)


@auth_router.post("/login", tags=[AuthRouterTags.auth])
def login(
    response: Response,
    payload: LoginSchema = Body(),
    session: Session = Depends(get_db),
):
    """Processes user's authentication and returns a token
    on successful authentication.

    request body:
    - email,
    - password
    """
    return auth.login(response, session, payload)
