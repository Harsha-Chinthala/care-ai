import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import get_model_params

class ModelTrainer:
    def __init__(self):
        self.models = {}
        try:
            self.params = get_model_params()
        except:
            # Fallback parameters if config fails
            self.params = {'test_size': 0.2, 'random_state': 42}
    
    def train_placement_model(self, X, y):
        """Train model to predict placement likelihood"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.params['test_size'], random_state=self.params['random_state']
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=self.params['random_state'])
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Placement Model Accuracy: {accuracy:.2f}")
        
        self.models['placement'] = model
        return model
    
    def train_higher_studies_model(self, X, y):
        """Train model to predict higher studies likelihood"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.params['test_size'], random_state=self.params['random_state']
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=self.params['random_state'])
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Higher Studies Model Accuracy: {accuracy:.2f}")
        
        self.models['higher_studies'] = model
        return model
    
    def save_models(self, path):
        """Save trained models to disk"""
        os.makedirs(path, exist_ok=True)
        for name, model in self.models.items():
            joblib.dump(model, f"{path}/{name}_model.pkl")
    
    def load_models(self, path):
        """Load trained models from disk"""
        model_files = {
            'placement': f"{path}/placement_model.pkl",
            'higher_studies': f"{path}/higher_studies_model.pkl"
        }
        
        for name, filepath in model_files.items():
            try:
                self.models[name] = joblib.load(filepath)
            except FileNotFoundError:
                print(f"Model file not found: {filepath}")