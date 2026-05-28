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
    model_path = os.path.join('artifacts', 'model.pkl')
    engineered_features = os.path.join('artifacts', 'parsed.parquet')


class ModelTrainer:
    def __init__(self):
        self.trainer_config = ModelTrainerConfig()
        self.feature_engineering = FeatureEngineering()

    
    def initiate_model_trainer(self):
        logging.info('Entered model training object')

        try:
            model = XGBRegressor(
            n_estimators=150,
            max_depth=3,       # prevent overfitting on small data
            max_leaves=3,
            #min_samples_leaf=4,
            learning_rate=0.4,
            random_state=42
            )

            targets = ['money_sent', 'paybill_payment', 'till_payment', 
                    'pochi_payment', 'airtime', 'withdrawal']
            
            
            target_dfs = self.feature_engineering.initiate_feature_engineering(df_path=self.trainer_config.engineered_features)
            # print(target_dfs['airtime'].head(3))
            for target in targets:
                target_df = target_dfs[target]

                n = len(target_df)

                
                # ── Features:
                features = target_df[['lag1', 'lag2','lag3','rolling_mean_3','rolling_std_3','year','month',
                                'dayofweek', 'hour']].values
                
                model_target = target_df[target].values

                # ── 80/20 split — ensure at least 1 row in test ──
                train_len = min(max(int(n * 0.8), 1), n - 1)

                X_train, X_test = features[:train_len], features[train_len:]
                y_train, y_test = model_target[:train_len], model_target[train_len:]

                # model train
                model.fit(X_train, y_train)

                # evaluate
                y_pred       = model.predict(X_test)
                y_train_pred = model.predict(X_train)
                test_score   = r2_score(y_test, y_pred)
                train_score = r2_score(y_train, y_train_pred)
                
                print("{} train_score: {:.3f}".format(target, train_score))
                print("{} test score: {:.3f}".format(target, test_score))
                
                save_object(
                    file_path = self.trainer_config.model_path,
                    obj = model
                )

                logging.info('Model trained and saved successfully')
                 
            
        except Exception as e:
            raise CustomException(e, sys)