from fastapi import FastAPI
from src.api.routers import auth, pipeline, insights


app = FastAPI(title='M-pesa Analyser')

app.include_router(auth.router)
app.include_router(pipeline.router)
app.include_router(insights.router)