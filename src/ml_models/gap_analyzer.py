import pandas as pd
import numpy as np

class GapAnalyzer:
    def __init__(self, skill_requirements):
        self.skill_requirements = skill_requirements
    
    def analyze_skill_gaps(self, student_skills, career_path):
        """Analyze skill gaps for a student based on their chosen career path"""
        required_skills = self.skill_requirements.get(career_path, {})
        gaps = {}
        
        for skill, required_level in required_skills.items():
            student_level = student_skills.get(skill, 0)
            gap = max(0, required_level - student_level)
            if gap > 0:
                gaps[skill] = {
                    'current_level': student_level,
                    'required_level': required_level,
                    'gap': gap
                }
        
        return gaps
    
    def generate_recommendations(self, gaps):
        """Generate recommendations based on skill gaps"""
        recommendations = []
        
        for skill, gap_info in gaps.items():
            rec = {
                'skill': skill,
                'current_level': gap_info['current_level'],
                'required_level': gap_info['required_level'],
                'recommendation': self.get_training_recommendation(skill, gap_info['gap'])
            }
            recommendations.append(rec)
        
        return recommendations
    
    def get_training_recommendation(self, skill, gap):
        """Get specific training recommendations for a skill gap"""
        training_map = {
            'programming': {
                'small': "Complete Codecademy Python course",
                'medium': "Complete Coursera Python specialization",
                'large': "Enroll in advanced algorithms course and build portfolio projects"
            },
            'communication': {
                'small': "Join Toastmasters club",
                'medium': "Take business communication course",
                'large': "Enroll in professional communication certification"
            },
            # Add more skills and recommendations as needed
        }
        
        if gap <= 2:
            gap_size = 'small'
        elif gap <= 4:
            gap_size = 'medium'
        else:
            gap_size = 'large'
        
        return training_map.get(skill, {}).get(gap_size, "Seek personalized coaching")
        