import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class StudentProfiler:
    def __init__(self, predictor, gap_analyzer):
        self.predictor = predictor
        self.gap_analyzer = gap_analyzer
    
    def generate_student_profile(self, student_data, student_skills):
        """Generate comprehensive student profile"""
        # Get predictions
        predictions = self.predictor.get_comprehensive_prediction(student_data, student_skills)

        recommended_focus_path = self.get_recommended_focus_path(predictions)
        most_likely_path = self.get_most_likely_path(student_data, student_skills, predictions, recommended_focus_path)

        # If the student needs training first, generate skill gaps against the
        # best-fit focus path rather than against a generic "needs training" label.
        analysis_path = recommended_focus_path if most_likely_path == 'needs_training' else most_likely_path
        skill_gaps = self.gap_analyzer.analyze_skill_gaps(student_skills, analysis_path)
        recommendations = self.gap_analyzer.generate_recommendations(skill_gaps)
        
        profile = {
            'predictions': predictions,
            'most_likely_path': most_likely_path,
            'recommended_focus_path': recommended_focus_path,
            'skill_gaps': skill_gaps,
            'recommendations': recommendations
        }
        
        return profile
    
    def get_recommended_focus_path(self, predictions):
        """Determine the strongest-fit track from normalized scores."""
        normalized_scores = self.get_normalized_scores(predictions)
        return max(normalized_scores, key=normalized_scores.get)

    def get_most_likely_path(self, student_data, student_skills, predictions, recommended_focus_path):
        """Classify the student's current outcome, including needs_training."""
        normalized_scores = self.get_normalized_scores(predictions)
        top_score = normalized_scores.get(recommended_focus_path, 0.0)
        skill_readiness = self.get_skill_readiness(student_skills, recommended_focus_path)
        high_risk = self.is_high_risk_student(student_data)

        # If overall confidence is weak or the student is high-risk without a
        # strong enough signal, direct them to training first.
        if top_score < 0.55:
            return 'needs_training'

        if high_risk and top_score < 0.70:
            return 'needs_training'

        if skill_readiness < 0.50:
            return 'needs_training'

        return recommended_focus_path

    def get_normalized_scores(self, predictions):
        return {
            'placement': float(predictions.get('placement_probability', 0.0)),
            'higher_studies': float(predictions.get('higher_studies_probability', 0.0)),
            'entrepreneurship': float(predictions.get('entrepreneurship_score', 0.0)) / 10.0
        }

    def get_skill_readiness(self, student_skills, path):
        skill_map = {
            'placement': ['programming', 'communication', 'problem_solving', 'teamwork'],
            'higher_studies': ['research', 'analytical_thinking', 'writing', 'subject_knowledge'],
            'entrepreneurship': ['leadership', 'innovation', 'risk_management', 'networking', 'communication']
        }

        selected_skills = skill_map.get(path, [])
        if not selected_skills:
            return 0.0

        scores = [float(student_skills.get(skill, 0)) for skill in selected_skills]
        return sum(scores) / (len(scores) * 10.0)

    def is_high_risk_student(self, student_data):
        if isinstance(student_data, pd.DataFrame):
            cgpa = float(student_data['cgpa'].iloc[0]) if 'cgpa' in student_data.columns else 0.0
            aptitude = float(student_data['aptitude_score'].iloc[0]) if 'aptitude_score' in student_data.columns else 0.0
            arrears = float(student_data['arrears_count'].iloc[0]) if 'arrears_count' in student_data.columns else 0.0
        else:
            cgpa = float(student_data.get('cgpa', 0.0))
            aptitude = float(student_data.get('aptitude_score', 0.0))
            arrears = float(student_data.get('arrears_count', 0.0))

        return cgpa < 6.0 or aptitude < 40.0 or arrears > 2.0
    
    def create_visualization(self, profile):
        """Create visualization for student profile"""
        # Create radar chart for skills assessment
        skills = list(profile['skill_gaps'].keys())
        current_levels = [gap['current_level'] for gap in profile['skill_gaps'].values()]
        required_levels = [gap['required_level'] for gap in profile['skill_gaps'].values()]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=current_levels,
            theta=skills,
            fill='toself',
            name='Current Skills'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=required_levels,
            theta=skills,
            fill='toself',
            name='Required Skills'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title="Skill Assessment Radar Chart"
        )
        
        return fig
        
