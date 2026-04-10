import pandas as pd
import numpy as np

class CareerPredictor:
    def __init__(self, model_trainer):
        self.trainer = model_trainer
    
    def predict_placement(self, student_data):
        """Predict placement likelihood for a student"""
        if 'placement' not in self.trainer.models:
            raise ValueError("Placement model not trained or loaded")
        
        model = self.trainer.models['placement']
        return model.predict_proba(student_data)
    
    def predict_higher_studies(self, student_data):
        """Predict higher studies likelihood for a student"""
        if 'higher_studies' not in self.trainer.models:
            raise ValueError("Higher studies model not trained or loaded")
        
        model = self.trainer.models['higher_studies']
        return model.predict_proba(student_data)
    
    def predict_entrepreneurship(self, student_data, student_skills=None):
        """Estimate entrepreneurship potential on a 0-10 scale"""
        if isinstance(student_data, pd.DataFrame):
            cgpa = float(student_data['cgpa'].iloc[0]) if 'cgpa' in student_data.columns else 7.0
            aptitude = float(student_data['aptitude_score'].iloc[0]) if 'aptitude_score' in student_data.columns else 70.0
            internship = float(student_data['internship_duration'].iloc[0]) if 'internship_duration' in student_data.columns else 0.0
            arrears = float(student_data['arrears_count'].iloc[0]) if 'arrears_count' in student_data.columns else 0.0
        else:
            cgpa = float(student_data.get('cgpa', 7.0))
            aptitude = float(student_data.get('aptitude_score', 70.0))
            internship = float(student_data.get('internship_duration', 0.0))
            arrears = float(student_data.get('arrears_count', 0.0))

        student_skills = student_skills or {}

        leadership = float(student_skills.get('leadership', 5))
        innovation = float(student_skills.get('innovation', 5))
        risk_management = float(student_skills.get('risk_management', 5))
        networking = float(student_skills.get('networking', 5))
        communication = float(student_skills.get('communication', 5))

        # Entrepreneurship should be driven more by entrepreneurial traits
        # than by pure academic strength.
        skill_signal = (
            leadership * 0.26 +
            innovation * 0.30 +
            risk_management * 0.18 +
            networking * 0.16 +
            communication * 0.10
        ) / 10.0

        academic_signal = (
            (cgpa / 10.0) * 0.45 +
            (aptitude / 100.0) * 0.35 +
            min(internship, 12.0) / 12.0 * 0.20
        )

        resilience_penalty = min(0.18, arrears * 0.05)

        entrepreneurship_probability = (
            skill_signal * 0.7 +
            academic_signal * 0.3 -
            resilience_penalty
        )

        entrepreneurship_probability = min(1.0, max(0.0, entrepreneurship_probability))
        return entrepreneurship_probability * 10.0
    
    def get_comprehensive_prediction(self, student_data, student_skills=None):
        """Get all predictions for a student"""
        try:
            placement_prob = self.predict_placement(student_data)
            higher_studies_prob = self.predict_higher_studies(student_data)
            entrepreneurship_score = self.predict_entrepreneurship(student_data, student_skills)
            
            return {
                'placement_probability': float(placement_prob[0][1]) if len(placement_prob[0]) > 1 else 0.5,
                'higher_studies_probability': float(higher_studies_prob[0][1]) if len(higher_studies_prob[0]) > 1 else 0.5,
                'entrepreneurship_score': float(entrepreneurship_score)
            }
        except Exception as e:
            print(f"Error in prediction: {e}")
            # Return default predictions if error occurs
            return {
                'placement_probability': 0.5,
                'higher_studies_probability': 0.5,
                'entrepreneurship_score': 5.0
            }
