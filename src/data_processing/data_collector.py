import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import get_data_paths

class DataCollector:
    def __init__(self):
        try:
            self.paths = get_data_paths()
        except:
            # Fallback paths if config fails
            self.paths = {
                'raw_path': 'data/raw/',
                'processed_path': 'data/processed/',
                'models_path': 'data/models/'
            }
        
    def load_academic_data(self, filename="academic_records.csv"):
        """Load academic records from CSV file"""
        filepath = os.path.join(self.paths['raw_path'], filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Academic data file not found: {filepath}")
        return pd.read_csv(filepath)
    
    def load_career_data(self, filename="career_choices.csv"):
        """Load career choice data"""
        filepath = os.path.join(self.paths['raw_path'], filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Career data file not found: {filepath}")
        return pd.read_csv(filepath)
    
    def load_psychometric_data(self, filename="psychometric_scores.csv"):
        """Load psychometric test results"""
        filepath = os.path.join(self.paths['raw_path'], filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Psychometric data file not found: {filepath}")
        return pd.read_csv(filepath)
    
    def merge_datasets(self, academic_df, career_df, psychometric_df):
        """Merge all datasets on student ID"""
        merged_df = academic_df.merge(career_df, on='student_id', how='left')
        merged_df = merged_df.merge(psychometric_df, on='student_id', how='left')
        return merged_df