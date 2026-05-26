import pandas as pd
import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime

from dataclasses import dataclass
from src.logger import logging
from src.exception import CustomException
from data_parsing import DataParsing
from src.pipeline.feature_engineering import FeatureEngineering


# data is in an xml file, we parse with xml parser
@dataclass
class DataIngestionConfig:
    raw_data_path = os.path.join('notebook', 'sms-20260520144009.xml')
    parsed_data_path = os.path.join('artifacts', 'data.csv')

class DataIngestion:
    def __init__(self):
        self.ingestion_config = DataIngestionConfig()

    def initiate_data_ingestion(self):
        logging.info('Entered data ingestion method')
        try:
            tree = ET.parse(self.ingestion_config.raw_data_path)
            root = tree.getroot()

            records = []
            for sms in root.findall('sms'):
                body = sms.get('body', '')
                date_sms = int(sms.get('date', 0))

                if 'M-PESA' not in body.upper():
                    continue

                records.append({
                    'body': body,
                    'timestamp': datetime.fromtimestamp(date_sms / 1000)

                })
            
            df = pd.DataFrame(records)
            print(f"✔️  Found {len(records)} M-pesa SMSes")
            #print(f"time {df['timestamp'].dtype}")
            logging.info('Data parsing successful')

            os.makedirs(os.path.dirname(self.ingestion_config.parsed_data_path), exist_ok=True)
            df.to_csv(self.ingestion_config.parsed_data_path, index=False, header=True)
            
            logging.info('Data Ingestion complete!')

            return self.ingestion_config.parsed_data_path
        
        except Exception as e:
            raise CustomException(e, sys)
    

if __name__ == '__main__':
    ingestion_obj = DataIngestion()
    data_path = ingestion_obj.initiate_data_ingestion()

    transform_obj = DataParsing()
    df_path = transform_obj.initiate_data_parsing(data_path=data_path)

    engineer_obj = FeatureEngineering()
    engineer_obj.initiate_feature_engineering(df_path=df_path)
