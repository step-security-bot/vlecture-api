from fastapi import FastAPI, status, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict

from starlette.status import HTTP_400_BAD_REQUEST

from src.utils.db import Base, engine, get_db
from src.schemas.users import CreateUserSchema, UserLoginSchema
from src.models.users import User
from src.services.users import create_user, get_user


app = FastAPI()

# CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "api.vlecture.com",
    "vlecture-api-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Hello world!"}


@app.get("/hi")
def hi():
    return {"message": "Bonjour!"}


@app.post("/signup", tags=["auth"])
def signup(payload: CreateUserSchema = Body(), session: Session = Depends(get_db)):
    """Processes request to register user account."""
    existing_user = None
    if (
        len(payload.email) == 0
        or len(payload.first_name) == 0
        or (payload.last_name) == 0
        or (payload.hashed_password) == 0
    ):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="All required fields must be filled!",
        )
    try:
        existing_user = get_user(session=session, email=payload.email)
    except Exception:
        payload.hashed_password = User.hash_password(payload.hashed_password)
        return create_user(session, user=payload)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists!"
        )
    else:
        payload.hashed_password = User.hash_password(payload.hashed_password)
        return create_user(session, user=payload)


@app.post("/login", tags=["auth"])
def login(payload: UserLoginSchema = Body(), session: Session = Depends(get_db)):
    """Processes user's authentication and returns a token
    on successful authentication.

    request body:

    - email,

    - password
    """
    try:
        user: User = get_user(session=session, email=payload.email)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user credentials"
        )

    is_validated: bool = user.validate_password(payload.password)
    if not is_validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user credentials"
        )

    user.generate_token()
    return user
