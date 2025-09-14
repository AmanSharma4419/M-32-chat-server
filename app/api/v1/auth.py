from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import jwt
import os
from datetime import datetime, timedelta
from app.db.mongo import users_collection
from app.auth_utils import hash_password, verify_password, create_access_token
from app.api.v1.schemas import UserCreate, UserDB, Token

router = APIRouter()

# Environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/signup")
async def signup(user: UserCreate):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed = hash_password(user.password)
    user_doc = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await users_collection.insert_one(user_doc)
    return {"message": "User created successfully",
            "user_id": str(result.inserted_id)}


@router.post("/login", response_model=Token)
async def login(user: UserCreate):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password,
                                          db_user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": db_user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/google/login")
async def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500,
                            detail="Google OAuth not configured")

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(request: Request, code: str):
    import requests as pyrequests

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )

    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_res = pyrequests.post(token_url, data=token_data)
    if token_res.status_code != 200:
        raise HTTPException(status_code=400,
                            detail="Failed to fetch token from Google")

    tokens = token_res.json()

    try:
        id_info = id_token.verify_oauth2_token(
            tokens["id_token"],
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=400,
                            detail="Invalid token from Google")

    email = id_info.get("email")
    name = id_info.get("name")

    if not email:
        raise HTTPException(
            status_code=400, detail="Google account email not available"
        )

    # Check if user exists in MongoDB
    user = await users_collection.find_one({"email": email})
    if not user:
        user_doc = {
            "email": email,
            "full_name": name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "auth_provider": "google"
        }
        result = await users_collection.insert_one(user_doc)
        user_id = str(result.inserted_id)
    else:
        user_id = str(user["_id"])

    # Create JWT token
    token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user_id, "email": email, "name": name
    }}


@router.post("/googleauth")
async def google_auth(payload: dict):
    """
    Accepts: { idToken, email, name, provider, providerId }
    Verifies Google idToken, creates/gets user, returns JWT.
    """
    id_token_str = payload.get("idToken")
    email = payload.get("email")
    name = payload.get("name")
    provider = payload.get("provider")
    provider_id = payload.get("providerId")

    if not id_token_str or not email:
        raise HTTPException(
            status_code=400, detail="idToken and email required")

    try:
        id_info = id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), GOOGLE_CLIENT_ID)
        if id_info.get("email") != email:
            raise HTTPException(
                status_code=400, detail="Email mismatch in token")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid Google idToken: {str(e)}")

    # Check if user exists
    user = await users_collection.find_one({"email": email})
    if not user:
        user_doc = {
            "email": email,
            "full_name": name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "auth_provider": provider or "google",
            "provider_id": provider_id,
        }
        result = await users_collection.insert_one(user_doc)
        user_id = str(result.inserted_id)
    else:
        user_id = str(user["_id"])
        name = user.get("full_name", name)

    # Create JWT token
    token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": token, "token_type": "bearer", "user": {"id": user_id, "email": email, "name": name}}


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDB:
    """
    FastAPI dependency to get the currently logged-in user from JWT token.
    Gives 401 if token is invalid or user does not exist.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return UserDB(
            id=str(user.get("_id")),
            username=user.get("username") or user.get(
                "email") or user.get("full_name"),
            full_name=user.get("full_name"),
            email=user.get("email"),
        )

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
