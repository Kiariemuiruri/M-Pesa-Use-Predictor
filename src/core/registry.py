import joblib, io
from src.core.supabase_client import supabase


BUCKET = 'models'

def save_model_to_storage(user_id: str, model_name: str, model_obj):
    buffer = io.BytesIO()
    joblib.dump(model_obj, buffer)
    buffer.seek(0)
    path = f"{user_id}/{model_name}.joblib"

    # upsert = True overrites on retrain
    supabase.storage.from_(BUCKET).upload(
        path, buffer.read(),
        file_options={"content-type": "application/octet-stream", "upsert":"true"}
    )

def load_from_storage(user_id: str, model_name: str):
    path = f"{user_id}/{model_name}.joblib"
    data = supabase.storage.from_(BUCKET).download(path)
    return joblib.load(io.BytesIO(data))