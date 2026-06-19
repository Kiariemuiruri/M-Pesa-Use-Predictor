from fastapi import APIRouter, Depends, HTTPException
from src.core.auth import  get_current_user
from src.core.supabase_client import supabase, supabase_admin
from src.utils import fetch_user_transactions
from src.exception import CustomException
import sys

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get('/report')
def get_report(user: dict = Depends(get_current_user)):
    try:
        user_id = user['id']
        print(user_id)
        res = supabase_admin.table('reports') \
            .select("report", "predictions", "generated_at") \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        if not res.data:
            raise HTTPException(404, "No report found. Upload SMS data first")
        
        return res.data
    
    except Exception as e:
        raise CustomException(e, sys)

@router.get('/transaction')
def get_transactions(user: dict = Depends(get_current_user), limit: int=50):
    try:
        user_id = user['id']
        res = supabase_admin.table('transaction') \
            .select("*") \
            .eq("user_id", user_id) \
            .order("timestamp", desc=True) \
            .limit(limit) \
            .execute()
        
        return res.data
    
    except Exception as e:
        raise CustomException(e, sys)
    
