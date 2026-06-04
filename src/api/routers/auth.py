from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from src.core.supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

class AuthPayload(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(body: AuthPayload):
    res = supabase.auth.sign_up({"email": body.email, "password": body.password})
    if res.user is None:
        raise HTTPException(400, "Registration failed")
    return {"user_id": res.user.id, "email": res.user.email}

@router.post("/login")
def login(body: AuthPayload):
    res = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
    if res.user is None:
        raise HTTPException(401, "Invalid credentials")
    return {
        "access_token": res.session.access_token,
        "user_id": res.user.id
    }