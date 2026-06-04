from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from src.core.auth import get_current_user
from src.core.supabase_client import supabase
from src.components.data_parsing import DataParsing          # your existing parser
from src.pipeline.model_trainer import ModelTrainer
from src.components.data_ingestion import DataIngestion
from src.reports.predict import TransactionsReport
from src.core.registry import save_model_to_storage
import json


router = APIRouter(prefix='/pipeline', tags=['pipeline'])

class SMSUpload(BaseModel):
    messages: list[str]


@router.post('/upload')
def upload_and_train(body: SMSUpload, user: dict = Depends(get_current_user)):
    user_id = user['sub']

    # extract M-pesa SMSes
    ingestion = DataIngestion()
    df = ingestion.initiate_data_ingestion(body.messages)

    # parse sms into Transactions
    parsing = DataParsing()
    parsed_df = parsing.initiate_data_parsing(df)
    
    records = parsed_df.to_dict(orient='records')
    if records.empty:
        raise HTTPException(400, "No valid M-pesa transactions found")
    
    for r in records:
        r['user_id'] = user_id

    supabase.table('transactions').upsert(records, on_conflict="transaction_id").execute()

    # train models on users data
    trainer = ModelTrainer()
    models = trainer.initiate_model_trainer(user_id, parsed_df)

    # save .joblib files to supabase storage
    for model_name, model_obj in models.items():
        save_model_to_storage(user_id, model_name, model_obj)

    # generate report and predictions
    transactions_report = TransactionsReport()
    report = transactions_report.generate_report(user_id, parsed_df)
    prediction = transactions_report.predict_next_month(user_id, parsed_df)

    # save model + metadata to DB
    supabase.table('reports').upsert({
        'user_id': user_id,
        'report': report,
        'prediction': prediction,
        'generated_at': datetime.now()

    })

    return {'status': 'done', 'transactions': len(records)}