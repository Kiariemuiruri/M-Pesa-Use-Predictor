import os
import sys
import pandas as pd
import dill
from src.exception import CustomException
from src.core.supabase_client import supabase_admin


def save_object(file_path, obj):
    try:
        dir_path = os.path.dirname(file_path)

        os.makedirs(dir_path, exist_ok=True)

        with open(file_path, 'wb') as file_obj:
            dill.dump(obj, file_obj)
    except Exception as e:
        raise CustomException(e, sys)
    
def fetch_user_transactions(user_id: str) -> pd.DataFrame:
    res = supabase_admin.table("transactions") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
    
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    df['amount'] = df['amount'].astype(float)
    df['balance'] = df['balance'].astype(float)

    return df