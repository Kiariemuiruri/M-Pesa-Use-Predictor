import os
import sys
import pandas as pd
import numpy as np
import joblib
from dataclasses import dataclass
from src.logger import logging
from src.exception import CustomException
from src.pipeline.feature_engineering import FeatureEngineering


@dataclass
class PredictConfig:
    data_path = os.path.join('artifacts', 'parsed.parquet')
    model_path = os.path.join('artifacts', 'model.pkl')


class TransactionsReport:
    def __init__(self):
        predict_config = PredictConfig()

    
    def generate_report(self, data_path):
        logging.info('Initiated report generation')

        try:
             
            transactions_df = pd.read_parquet(data_path)

            received = transactions_df[transactions_df['txn_type'] == 'received']
            sent = transactions_df[transactions_df['txn_type'] == 'sent']
            paybill = transactions_df[transactions_df['txn_type'] == 'paybill']
            till = transactions_df[transactions_df['txn_type'] == 'till']
            pochi = transactions_df[transactions_df['txn_type'] == 'pochi']
            airtime = transactions_df[transactions_df['txn_type'] == 'airtime']
            withdraw = transactions_df[transactions_df['txn_type'] == 'withdrawal']
            fuliza = transactions_df[transactions_df['txn_type'] == 'fuliza_borrowed']
            fuliza_deduct = transactions_df[transactions_df['txn_type'] == 'fuliza_deducted']
            fuliza_rem = transactions_df[transactions_df['txn_type'] == 'fuliza_reminder']

            def top5(subset):
                if subset.empty or 'name' not in subset.columns:
                    return []
                
                return (
                    subset.groupby('name')['amount']
                    .agg(['sum', 'count'])
                    .sort_values('sum', ascending=False)
                    .head(5)
                    .reset_index()
                    .rename(columns={'sum': 'total', 'count': 'times'})
                    .assign(total=lambda x: x['total'].round(2))
                    .to_dict('records')
                )
            
            total_in = received['amount'].sum() + fuliza['amount'].sum()
            total_out = (sent['amount'].sum() + paybill['amount'].sum() +
                        till['amount'].sum()  + pochi['amount'].sum()  +
                        airtime['amount'].sum() + withdraw['amount'].sum())
            
            logging.info('Report successfully generated') 
            
            return {
                "received":{
                    'total'       :      TransactionsReport._fmt(received['amount'].sum()),
                    'times'       :      len(received),
                    'larget'      :     TransactionsReport._fmt(received['amount'].max()) if not received.empty else 0,
                },
                'sent':{
                    'total'       :      TransactionsReport._fmt(sent['amount'].sum()),
                    'times'       :      len(sent),
                    'largest'     :    TransactionsReport._fmt(sent['amount'].max()) if not sent.empty else 0,
                },
                "paybill":{
                    'total'       :      TransactionsReport._fmt(paybill['amount'].sum()),
                    'times'       :      len(paybill),
                    'larget'      :     TransactionsReport._fmt(paybill['amount'].max()) if not paybill.empty else 0,
                },
                "till":{
                    'total'       :      TransactionsReport._fmt(till['amount'].sum()),
                    'times'       :      len(till),
                    'larget'      :     TransactionsReport._fmt(till['amount'].max()) if not till.empty else 0,
                },
                "pochi":{
                    'total'       :      TransactionsReport._fmt(pochi['amount'].sum()),
                    'times'       :      len(pochi),
                    'larget'      :     TransactionsReport._fmt(pochi['amount'].max()) if not pochi.empty else 0,
                },
                "airtime":{
                    'total'       :      TransactionsReport._fmt(airtime['amount'].sum()),
                    'times'       :      len(airtime),
                    'larget'      :     TransactionsReport._fmt(airtime['amount'].max()) if not airtime.empty else 0,
                },
                'fuliza':{
                    'total_borrowed' :   TransactionsReport._fmt(fuliza['amount'].sum()),
                    'most_borrowed'  :   TransactionsReport._fmt(fuliza['amount'].max()) if not fuliza.empty else 0,
                    'times_borrowed' :   len(fuliza),
                    'total_deducted' :   TransactionsReport._fmt(fuliza_deduct['amount'].sum()),
                    'times_deducted' :   len(fuliza_deduct),
                    'highest_owed'   :   TransactionsReport._fmt(fuliza_rem['amount'].max()) if not fuliza_rem.empty else 0
                },
                'top_senders'        : top5(received),
                'top_receivers'      : top5(sent),
                'top_paybils'        : top5(paybill),
                'top_tills'          : top5(till),
                'totals':{
                    'total_in'       : TransactionsReport._fmt(total_in),
                    'total_out'      : TransactionsReport._fmt(total_out),
                    'net_flow'       : TransactionsReport._fmt(total_in - total_out)
                }

            }
                           
    
        except Exception as e:
            raise CustomException(e, sys)
    
    def _fmt(v): return f"Ksh {v:,.2f}"

    def generate_transaction_times(self, data_path):
        try:
            transactions_df = pd.read_parquet(data_path)
            transactions_times = {}
            transactions_times = transactions_df['txn_type'].value_counts()
            logging.info('number of transactions successful')

            return transactions_times
        
        except Exception as e:
            raise CustomException(e, sys)
        

    def predict_next_month(self, data_path, model_paths: dict):
        try:
            feature_engineering = FeatureEngineering()
            dfs = feature_engineering.initiate_feature_engineering(data_path)

            predictions = {}
            total       = 0
            targets     = ['money_sent', 'paybill_payment', 'till_payment',
                        'pochi_payment', 'airtime', 'withdrawal']

            for target in targets:
                target_df  = dfs[target]
                last_row   = target_df.iloc[-1]
                last_time  = target_df['timestamp'].iloc[-1]
                next_month = last_time + pd.DateOffset(months=1)

                next_features = np.array([[
                    last_row['lag1'],
                    last_row['lag2'],
                    last_row['lag3'],
                    last_row['rolling_mean_3'],
                    last_row['rolling_std_3'],
                    next_month.year,
                    next_month.month,
                    next_month.dayofweek,
                    next_month.hour,
                ]])

                # ── Load the correct model for this target ────────────
                model     = joblib.load(model_paths[target])
                next_pred = max(model.predict(next_features)[0], 0)

                print(f"{target:<20} Ksh {next_pred:>10,.2f}")

                total += next_pred
                predictions[target] = round(next_pred, 2)
                predictions['total'] = round(total, 2)
            logging.info('Predictions complete')

            return predictions
        
        except Exception as e:
            raise CustomException(e, sys)
