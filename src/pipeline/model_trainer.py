import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from dataclasses import dataclass

from src.pipeline.feature_engineering import FeatureEngineering
from src.logger import logging
from src.exception import CustomException
from src.utils import save_object


@dataclass 
class ModelTrainerConfig:
    model_path = os.path.join('models', 'model.pkl')
    engineered_features = os.path.join('artifacts', 'parsed.parquet')


class ModelTrainer:
    def __init__(self):
        self.trainer_config = ModelTrainerConfig()
        self.feature_engineering = FeatureEngineering()

    
    def initiate_model_trainer(self, user_id,df):
        logging.info('Entered model training object')

        try:
            targets = ['money_sent', 'paybill_payment', 'till_payment',
                    'pochi_payment', 'airtime', 'withdrawal']

            target_dfs = self.feature_engineering.initiate_feature_engineering(df=df)
            

            model_paths = {}  # store one path per target
             # ── tuned model per target ────────────────────────

            models = {'money_sent': XGBRegressor(n_estimators=100,max_depth=5,max_leaves=3,learning_rate=0.3,random_state=42),
                      'paybill_payment': XGBRegressor(n_estimators=150,max_depth=3,max_leaves=3,learning_rate=0.4,random_state=42),
                      'till_payment': XGBRegressor(n_estimators=150,max_depth=4,max_leaves=5,learning_rate=0.1,random_state=42),
                      'pochi_payment': XGBRegressor(n_estimators=150,max_depth=3,max_leaves=3,learning_rate=0.4,random_state=42),
                      'airtime': XGBRegressor(n_estimators=150,max_depth=3,max_leaves=3,learning_rate=0.5,random_state=42),
                      'withdrawal': XGBRegressor(n_estimators=150,max_depth=3,max_leaves=4,learning_rate=0.4,random_state=42)
                      }
                
                   

            for target in targets:
                target_df = target_dfs[target]
                n         = len(target_df)


                features = target_df[['lag1', 'lag2', 'lag3','rolling_mean_3', 'rolling_std_3',
                                        'year', 'month', 'dayofweek', 'hour']].values
                    
    
                model_target = target_df[target].values

                train_len       = min(max(int(n * 0.8), 1), n - 1)
                X_train, X_test = features[:train_len], features[train_len:]
                y_train, y_test = model_target[:train_len], model_target[train_len:]
                
                model = models[target]
                model.fit(X_train, y_train)

                y_pred       = model.predict(X_test)
                y_train_pred = model.predict(X_train)
                test_score   = r2_score(y_test, y_pred)
                train_score  = r2_score(y_train, y_train_pred)

                print(f"{target} — train: {train_score:.3f}  test: {test_score:.3f}")
                #print(f"  y_test:  {y_test}")
                #print(f"  y_pred:  {y_pred.round(2)}")

                # ── Save one model file per target ────────────────
                target_model_path = self.trainer_config.model_path.replace('.pkl', f'_{target}.pkl')
                    
                save_object(file_path=target_model_path, obj=model)
                model_paths[target] = target_model_path

                logging.info(f'Model saved → {target_model_path}')

            return "XGBoost", model # model_paths   return dict of paths, not just one path
            
        except Exception as e:
            raise CustomException(e, sys)