import joblib, io
from src.core.supabase_client import supabase


BUCKET = 'models'

def save_model_to_storage(user_id: str, model_name: str, model_obj):
    buffer = io.BytesIO()
    joblib.dump(model_obj, buffer)
    buffer.seek(0)
    path = f"{user_id}/{model_name}.joblib"

    # upsert = True overwrites on retrain
    supabase.storage.from_(BUCKET).upload(
        path, buffer.read(),
        file_options={"content-type": "application/octet-stream", "upsert":"true"}
    )

def load_from_storage(user_id: str):
    targets = ['money_sent', 'paybill_payment', 'till_payment',
               'pochi_payment', "airtime", 'withdrawal']

    models = {}
    for target in targets:
        path = f"{user_id}/{target}.joblib"
        buffer = io.BytesIO()
        data = supabase.storage.from_(BUCKET).download(path)
        buffer.write(data)
        buffer.seek(0)
        models[target] = joblib.load(buffer)
        
    return models

def list_user_models(user_id: str):
    files = supabase.storage.from_(BUCKET).list(user_id)
    print(files)

