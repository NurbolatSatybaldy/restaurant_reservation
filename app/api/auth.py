from fastapi import APIRouter, HTTPException, Depends, Form, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.responses import RedirectResponse
from app.models.user import User
from app.db.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/register")
def register(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),  # "client" or "host"
        db: Session = Depends(get_db)
):
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if role not in ("client", "host"):
        raise HTTPException(status_code=400, detail="Invalid role. Choose 'client' or 'host'.")

    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password, role=role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # After successful registration, redirect to the login page.
    return RedirectResponse(url="/login", status_code=302)


@router.post("/login")
def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user_obj = db.query(User).filter(User.email == email).first()
    if not user_obj or not verify_password(password, user_obj.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_obj.email}, expires_delta=access_token_expires
    )
    # Store the token in the session so the user stays logged in
    request.session["access_token"] = access_token
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.pop("access_token", None)
    return RedirectResponse(url="/", status_code=302)
