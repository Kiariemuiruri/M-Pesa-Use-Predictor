import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from dataclasses import dataclass

from pipeline.feature_engineering import FeatureEngineering
from src.logger import logging
from src.exception import CustomException


@dataclass 
class ModelTrainerConfig:
    model_path = os.path.join('artifacts', 'model.pkl')


class ModelTrainer:
    def __init__(self):
        self.trainer_config = ModelTrainerConfig()


    def r2_safe(y_true, y_pred):
        """
        R² that never returns NaN.
        Falls back to MAE-based score when R² is undefined. 
        """
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)

        if len(y_true) < 2:
            return None # truly can't score 1 sample
        
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - y_true.mean()) ** 2)

        if ss_tot == 0:
            # All test values identical — score based on how close predictions are
            # 1.0 = perfect, 0.0 = off by the mean 
            mean_val = y_true.mean()
            if mean_val == 0:
                    return 1.0 if ss_res == 0 else 0.0
            return max(0,1 - (np.sqrt(ss_res / len(y_true)) / mean_val))
        
        return 1 - (ss_res / ss_tot)
    
    