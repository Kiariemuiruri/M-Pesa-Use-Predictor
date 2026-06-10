from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx, os

bearer = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    token = creds.credentials
    
    # Verify token directly with Supabase instead of decoding locally
    res = httpx.get(
        f"{os.environ['SUPABASE_URL']}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": os.environ["SUPABASE_ANON_KEY"]
        }
    )
    
    if res.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    return res.json()  # contains id, email, etc.