from typing import List, Dict
from .models import Vacancy, JobScore

class JobScoringService:
    @staticmethod
    def calculate_salary_score(vacancy: Vacancy) -> float:
        """Calculate score based on salary range"""
        if not vacancy.salary_min or not vacancy.salary_max:
            return 0.0
            
        # Define salary thresholds (in EUR)
        thresholds = {
            'low': 2000,
            'medium': 4000,
            'high': 6000
        }
        
        avg_salary = (vacancy.salary_min + vacancy.salary_max) / 2
        
        if avg_salary >= thresholds['high']:
            return 1.0
        elif avg_salary >= thresholds['medium']:
            return 0.7
        elif avg_salary >= thresholds['low']:
            return 0.4
        else:
            return 0.2

    @staticmethod
    def calculate_relevance_score(vacancy: Vacancy, keywords: List[str]) -> float:
        """Calculate relevance score based on keywords in title and description"""
        score = 0.0
        text = f"{vacancy.title.lower()} {vacancy.description.lower()}"
        
        for keyword in keywords:
            if keyword.lower() in text:
                score += 0.2  # Each keyword match adds 0.2 to the score
                
        return min(score, 1.0)  # Cap at 1.0

    @staticmethod
    def calculate_company_score(vacancy: Vacancy, company_data: Dict) -> float:
        """Calculate company score based on company data"""
        # This is a placeholder - in real implementation, you would use actual company data
        # For example: company size, rating, age, etc.
        return 0.5  # Default middle score

    @classmethod
    def score_vacancy(cls, vacancy: Vacancy, keywords: List[str], company_data: Dict = None) -> JobScore:
        """Score a vacancy and create/update its JobScore"""
        score, created = JobScore.objects.get_or_create(vacancy=vacancy)
        
        score.salary_score = cls.calculate_salary_score(vacancy)
        score.relevance_score = cls.calculate_relevance_score(vacancy, keywords)
        score.company_score = cls.calculate_company_score(vacancy, company_data or {})
        
        score.calculate_total_score()
        return score 