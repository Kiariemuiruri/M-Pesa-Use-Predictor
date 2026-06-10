from fastapi import APIRouter, Depends, HTTPException
from src.core.auth import  get_current_user
from src.core.supabase_client import supabase
from src.utils import fetch_user_transactions


router = APIRouter(prefix="/insights", tags=["insights"])

@router.get('/report')
def get_report(user: dict = Depends(get_current_user)):
    user_id = user['id']
    res = supabase.table('reports') \
        .select("reports", "prediction", "generated_at") \
        .eq('user_id', user_id) \
        .single() \
        .execute()
    
    if not res.data:
        raise HTTPException(404, "No report found. Upload SMS data first")
    
    return res.data

@router.get('/transaction')
def get_transactions(user: dict = Depends(get_current_user), limit: int=50):
    user_id = user['id']
    res = supabase.table('transaction') \
        .select("*") \
        .eq("user_id", user_id) \
        .order("timestamp", desc=True) \
        .limit(limit) \
        .execute()
    
    return res.data
    
