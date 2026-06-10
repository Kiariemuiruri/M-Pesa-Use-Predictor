import sys
import os
import pandas as pd
import re 
import pyarrow
from dataclasses import dataclass

from src.logger import logging
from src.exception import CustomException


@dataclass
class DataParsingConfig:
    data_path = os.path.join('artifacts', 'parsed.parquet')



class DataParsing:
    def __init__(self):
        self.transformation_config = DataParsingConfig()


    
    def is_business(self, name:str) -> bool:
        #logging.info('Match heuristic business names to paybill payments')

        # Simple heuristic: business names contain these patterns
        business_indicators = [
                'LTD', 'LIMITED', 'AGENCY', 'STORE', 'SHOP', 'HOTEL', 'PETROL', 'STATION', 'MARKET', 'SUPERMARKET',
                'PHARMACY', 'HOSPITAL', 'CLINIC', 'SCHOOL', 'COLLEGE', 'UNIVERSITY', 'BANK', 'SACCO', 'INTERNET', 'WIRELESS',
                'INVESTMENTS', 'INV', 'ENTERPRISE', 'SERVICES', 'GROUP', 'HARDWARE', 'GARAGE', 'WINES', 'SPIRITS', 
                'BUTCHERY', 'SALON', 'CYBER', 'AGENT', 'MAMA', 'TRADERS', 'CLUB', 'PUB', 'MART'
            ]
        name_upper = name.upper()
        if any(word in name_upper for word in business_indicators):
            return True
        
        # has numbers (till numbers at times include them)
        if re.search(r'\d', name):
            return True
        
        #more than 3 names likely a business name
        if len(name.split()) > 3:
            return True
        return False
    
    def extract(self, body) -> dict:
                
        #logging.info('Started Regular Expression mapping')
        try:

            # regular expression to parse the data
            patterns = {

                # P2P sent — with or without phone number
                'sent': re.compile(
                    r'Confirmed\.\s*Ksh\s*([\d,]+\.?\d*)\s+sent to\s+(.+?)\s+(\d{9,12})?\s*on\s+[\d/]+\s+at\s+[\d:]+\s*[AP]M.*?New M-PESA balance is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE | re.DOTALL
                ),

                # Paybill with account number
                'paybill': re.compile(
                    r'Confirmed\.\s*Ksh\s*([\d,]+\.?\d*)\s+sent to\s+(.+?)\s+for account\s+([\w\d]+)\s+on\s+[\d/]+\s+at\s+[\d:]+\s*[AP]M.*?New M-PESA balance is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE | re.DOTALL
                ),

                # Till number payment — business name, no account number
                'till': re.compile(
                    r'Confirmed\.\s*Ksh\s*([\d,]+\.?\d*)\s+paid to\s+([A-Z0-9&\s\-]+?)\.\s+on\s+[\d/]+\s+at\s+[\d:]+\s*[AP]M.*?New M-PESA balance is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE | re.DOTALL
                ),

                # Pochi la Biashara — paid to a person's name (no phone, no account)
                'pochi': re.compile(
                    r'Confirmed\.\s*Ksh\s*([\d,]+\.?\d*)\s+paid to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\.\s+on\s+[\d/]+\s+at\s+[\d:]+\s*[AP]M.*?New M-PESA balance is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE | re.DOTALL
                ),

                # Received money
                'received': re.compile(
                    r'Confirmed\.You have received\s+Ksh\s*([\d,]+\.?\d*)\s+from\s+(.+?)\s+(\d{9,12})?\s*on.*?New M-PESA balance is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE | re.DOTALL
                ),
                # Fuliza borrowed
                'fuliza_borrowed': re.compile(
                    r'Fuliza M-PESA amount is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE
                ),
                # Fuliza deducted
                'fuliza_deducted': re.compile(
                    r'Ksh\s*([\d,]+\.?\d*)\s+from your M-PESA has been used to.*?Fuliza',
                    re.IGNORECASE | re.DOTALL
                ),

                # Fuliza reminder / balance notice
                'fuliza_reminder': re.compile(
                    r'outstanding Fuliza M-PESA amount is Ksh\s*([\d,]+\.?\d*)',
                    re.IGNORECASE
                ),

                # Airtime
                'airtime': re.compile(
                    r'Ksh\s*([\d,]+\.?\d*)\s+(of airtime | SAFARICOM DATA BUNDLES)',
                    re.IGNORECASE
                ),

                # Withdrawal
                'withdrawal': re.compile(
                    r'Withdraw Ksh\s*([\d,]+\.?\d*)\s+from',
                    re.IGNORECASE
                ),

                # transaction id
                'transaction_id': re.compile(
                    r'\b([A-Z]{2,3}[0-9A-Z]{7,10})\b',
                    re.IGNORECASE
                )
            }
    
            result = {
                'transaction_id': None,
                'txn_type': None,
                'amount': None,
                'number': None, 
                'balance': None
            }

            # IMPORTANT: check paybill BEFORE sent - both use 'sent to'
            # and check till/pochi carefullly
            order = ['paybill', 'sent', 'till', 'pochi', 'received', 'fuliza_borrowed', 'fuliza_deducted', 
                    'fuliza_reminder', 'airtime', 'withdrawal']
            
            for txn_type in order:
                pattern = patterns[txn_type]
                m = pattern.search(body)
                if not m:
                    continue

                result['txn_type'] = txn_type
                g = m.groups()

                if txn_type ==  'sent':
                    result['amount']  = float(g[0].replace(',', ''))
                    result['name']    = g[1].strip().title()
                    result['number']  = g[2].strip() if g[2] else None
                    result['balance'] = float(g[3].replace(',', ''))

                elif txn_type == 'received':
                    result['amount']  = float(g[0].replace(',', ''))
                    result['name']    = g[1].strip().title()
                    result['number']  = g[2].strip() if g[2] else None
                    result['balance'] = float(g[3].replace(',', ''))

                elif txn_type == 'paybill':
                    result['amount']  = float(g[0].replace(',', ''))
                    result['name']    = g[1].strip().title()
                    result['number']  = g[2].strip()
                    result['balance'] = float(g[3].replace(',', ''))

                elif txn_type in ('till', 'pochi'):
                    amount  = float(g[0].replace(',', ''))
                    name    = g[1].title()
                    balance = float(g[2].replace(',', ''))

                    # re-classify: if name looks like a business -> till, else -> pochi
                    if txn_type == 'pochi' and self.is_business(name):
                        result['txn_type'] = 'till'
                    elif txn_type == 'till' and not self.is_business(name):
                        result['txn_type'] = 'pochi'
                    
                    result['amount'] = amount
                    result['name'] = name
                    result['balance'] = balance
                
                elif txn_type in ('fuliza_borrowed', 'fuliza_reminder', 'fuliza_deducted', 
                                'airtime', 'withdrawal'):
                    result['amount'] = float(g[0].rstrip('.').replace(',', ''))

                break # stop at first match
            tid = patterns['transaction_id'].search(body)
            result['transaction_id'] = tid.group(1) if tid else None
            
            #logging.info('Data transformation complete')
            return result
        
        except Exception as e:
            raise CustomException(e, sys)
        
    def initiate_data_parsing(self, data):
        logging.info('Entered data transformation object')

        try:
            #data = pd.read_parquet(data_path, engine='pyarrow')
            extracted = data['body'].apply(self.extract)
            df = data.join(pd.DataFrame(extracted.tolist()))
            df = df.dropna(subset=['txn_type'])
            #print(f"time {df['timestamp'].dtype}")
            os.makedirs(os.path.dirname(self.transformation_config.data_path), exist_ok=True)
            #df.to_parquet(self.transformation_config.data_path, index=False, engine='pyarrow')
            print(f" ✔️  Extracted {len(df)} transactions")  
            #print(df['txn_type'].value_counts())
            logging.info('Data parsing complete')

            return df # self.transformation_config.data_path   

        except Exception as e:
            raise CustomException(e, sys)
            