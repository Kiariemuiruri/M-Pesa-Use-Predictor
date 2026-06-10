from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import numpy as np
from datetime import datetime
import math
import sys
from src.core.auth import get_current_user
from src.core.supabase_client import supabase_admin
from src.components.data_parsing import DataParsing          # your existing parser
from src.pipeline.model_trainer import ModelTrainer
from src.components.data_ingestion import DataIngestion
from src.reports.predict import TransactionsReport
from src.logger import logging
from src.exception import CustomException
from src.core.registry import save_model_to_storage, load_from_storage, list_user_models
from src.utils import fetch_user_transactions
import json


router = APIRouter(prefix='/pipeline', tags=['pipeline'])

class SMSUpload(BaseModel):
    messages: list[str]

def serialize_record(records: dict) -> dict:
    """Convert pandas/numpy types to plain Python types for JSON serialization."""
    cleaned = {}
    for k, v in records.items():
        if isinstance(v, pd.Timestamp):
            cleaned[k] = v.isoformat()
        elif isinstance(v, float) and math.isnan(v):
            cleaned[k] = None
        elif hasattr(v, 'item'):
            cleaned[k] = v.item()
        else:
            cleaned[k] = v
    return cleaned

def to_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_serializable(i) for i in obj]
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj

@router.post('/upload')
def upload_and_train(body: SMSUpload, user: dict = Depends(get_current_user)):
    try:
        user_id = user['id']

        # extract M-pesa SMSes
        ingestion = DataIngestion()
        df = ingestion.initiate_data_ingestion()

        # parse sms into Transactions
        parsing = DataParsing()
        parsed_df = parsing.initiate_data_parsing(df)
        
        records = parsed_df.to_dict(orient='records')
        records = [serialize_record(r) for r in records]
        #print(json.dumps(records[0], indent=2, default=str))
        #if records.empty:
        #   raise HTTPException(400, "No valid M-pesa transactions found")
        logging.info("Pipeline parsing complete")
        #list_user_models(user_id)

        seen = set()
        unique_records = []
        for r in records:
            r['user_id'] = user_id
            tid = r.get('transaction_id')
            if tid and tid not in seen:
                seen.add(tid)
                unique_records.append(r)
            elif not tid:
                unique_records.append(r)

        supabase_admin.table('transactions').upsert(unique_records, on_conflict="transaction_id").execute()

        # fetch the transactions from DB for training and report generation
        df = fetch_user_transactions(user_id=user_id)

        # train models on users data
        trainer = ModelTrainer()
        trainer.initiate_model_trainer(df=df, user_id=user_id)

        # generate report and predictions
        transactions_report = TransactionsReport()
        report = transactions_report.generate_report(user_id, transactions_df=df)
        prediction = transactions_report.predict_next_month(user_id, df=df)

        # save model + metadata to DB
        supabase_admin.table('reports').upsert({
            'user_id': user_id,
            'report': to_json_serializable(report),
            'predictions': to_json_serializable(prediction),
            'generated_at': datetime.now().isoformat(),
            'model_version': 'v.0.0.1'
        }, on_conflict='user_id').execute()

        return {'status': 'done', 'transactions': len(records)}
    
    except Exception as e:
        raise CustomException(e, sys)