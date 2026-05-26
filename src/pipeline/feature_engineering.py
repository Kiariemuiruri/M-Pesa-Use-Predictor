import os
import sys
import pandas as pd
import sklearn
from datetime import datetime
from dataclasses import dataclass

from src.logger import logging
from src.exception import CustomException


@dataclass
class FeatureEngineeringConfig:
    engineered_path = os.path.join('artifacts', 'engineered.csv')

class FeatureEngineering:
    def __init__(self):
        self.engineering_config = FeatureEngineeringConfig()

    # start by pivoting the features to be engineered
    def prepare_data(self, df_path):
        logging.info('Data pivoting started')

        try:
            df = pd.read_csv(df_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            print(df['timestamp'].dtype)
            outflows = df[df['txn_type'].isin(['sent', 'paybill', 'till', 'pochi', 'airtime',
                                            'withdrawal'])].copy()
            
            # map transactions into categories
            type_to_category = {
                'sent': 'money_sent',
                'paybill': 'paybill_payment',
                'till': 'till_payment',
                'pochi': 'pochi_payment',
                'airtime': 'airtime',
                'withdrawal': 'withdrawal'
            }

            outflows['category']  = outflows['txn_type'].map(type_to_category)
            
            # pivot: months=rows, categories=columns
            spending_df = outflows.pivot_table(
                index   = 'timestamp',
                columns = 'category',
                values  = 'amount',
                aggfunc = 'sum'
            ).fillna(0)

            spending_df = spending_df.reset_index()
            logging.info('Data pivoting complete')
            
            return spending_df

        except Exception as e:
            raise CustomException(e, sys)
        
    def initiate_feature_engineering(self, df_path):
        logging.info('Entered feature engineering object')

        try:
            target_dfs = {}

            spending_df = self.prepare_data(df_path=df_path)
            targets = ['money_sent', 'paybill_payment', 'till_payment', 
                    'pochi_payment', 'airtime', 'withdrawal']
            
            for target in targets:
                if target not in spending_df.columns:
                    print(f"⚠  '{target}' not found — skipping")
                    continue

                # build target df
                target_df = spending_df[['timestamp', target]]

                # sort by time
                target_df = target_df.sort_values('timestamp').reset_index(drop=True)

                # create lag features
                target_df['lag1'] = target_df[target].shift(1)
                target_df['lag2'] = target_df[target].shift(2)
                target_df['lag3'] = target_df[target].shift(3)

                # Rolling behavior
                target_df['rolling_mean_3'] = (target_df[target].rolling(3).mean())
                target_df['rolling_std_3']  = (target_df[target].rolling(3).std())

                # calendar info
                target_df['year'] = target_df['timestamp'].dt.year  # helps with trend
                target_df['month'] = target_df['timestamp'].dt.month
                target_df['dayofweek'] = target_df['timestamp'].dt.dayofweek
                target_df['hour']      = target_df['timestamp'].dt.hour

                # remove NaNs caused by shifting
                target_df = target_df.dropna().reset_index(drop=True)

                target_dfs[target] = target_df

                os.makedirs(os.path.dirname(self.engineering_config.engineered_path), exist_ok=True)
                #target_dfs.to_csv(self.engineering_config.engineered_path, header=True)

                logging.info('Feature engineerig complete')
                return target_dfs

        except Exception as e:
            raise CustomException(e,sys)

