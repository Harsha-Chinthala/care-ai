import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

class DataCleaner:
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
    
    def handle_missing_values(self, df, strategy='mean'):
        """Handle missing values in the dataset"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Fill numeric missing values
        if strategy == 'mean':
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].mean())
        elif strategy == 'median':
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].median())
                
        # Fill categorical missing values
        for col in categorical_cols:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
            
        return df
    
    def encode_categorical(self, df, columns):
        """Encode categorical variables"""
        for col in columns:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.encoders[col] = le
        return df
    
    def scale_features(self, df, columns):
        """Scale numerical features"""
        for col in columns:
            if col in df.columns:
                scaler = StandardScaler()
                df[col] = scaler.fit_transform(df[col].values.reshape(-1, 1))
                self.scalers[col] = scaler
        return df
    
    def preprocess_data(self, df, categorical_cols, numeric_cols):
        """Complete preprocessing pipeline"""
        df = self.handle_missing_values(df)
        df = self.encode_categorical(df, categorical_cols)
        df = self.scale_features(df, numeric_cols)
        return df
        