from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.db.mongo import users_collection
from app.api.v1.schemas import UserCreate, UserDB, Token
from app.auth_utils import hash_password, verify_password, create_access_token
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter()


@router.post("/signup")
async def signup(user: UserCreate):
    existing = await users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hash_password(user.password)
    user_doc = {
        "username": user.username,
        "hashed_password": hashed,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await users_collection.insert_one(user_doc)

    return {"message": "User created successfully",
            "user_id": str(result.inserted_id)}


@router.post("/login", response_model=Token)
async def login(user: UserCreate):
    db_user = await users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password,
                                          db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": db_user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDB:
    """
    FastAPI dependency to get the currently logged-in user from JWT token.
    Gives 401 if token is invalid or user does not exist.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user = await users_collection.find_one({"username": username})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return UserDB(id=str(user["_id"]), username=user["username"])

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
