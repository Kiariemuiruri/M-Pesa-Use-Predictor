from fastapi import FastAPI, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.api.routers import auth, pipeline, insights
import uvicorn

app = FastAPI(title='M-pesa Analyser')

@app.get("/")
def read_route():
    return {"message": "Endpoint Health okay ✔️"}

@app.get("/debug/auth")
def debug_auth(creds: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    import httpx, os
    token = creds.credentials
    res = httpx.get(
        f"{os.environ['SUPABASE_URL']}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": os.environ["SUPABASE_ANON_KEY"]
        }
    )
    return {"status_code": res.status_code, "response": res.json()}
app.include_router(auth.router)
app.include_router(pipeline.router)
app.include_router(insights.router)
