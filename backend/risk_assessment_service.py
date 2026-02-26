"""
Risk Assessment Service for SmartFin 2.0
Calculates user risk tolerance based on questionnaire responses
"""

import sqlite3
from typing import Dict, List, Optional, Tuple


class RiskAssessmentService:
    """Service for calculating and managing risk tolerance assessments"""
    
    # Risk assessment questions with their weights
    QUESTIONS = {
        1: {
            "text": "How would you react to a 20% drop in your investment portfolio?",
            "type": "scale",
            "weight": 0.25,
            "options": {
                1: "Sell everything immediately",
                2: "Sell some investments",
                3: "Hold steady",
                4: "Buy a little more",
                5: "Buy significantly more"
            }
        },
        2: {
            "text": "What is your primary financial goal timeline?",
            "type": "choice",
            "weight": 0.20,
            "options": {
                1: "Short-term (< 3 years)",
                2: "Medium-term (3-10 years)",
                3: "Long-term (> 10 years)"
            }
        },
        3: {
            "text": "How much investment experience do you have?",
            "type": "choice",
            "weight": 0.15,
            "options": {
                1: "None - I'm just starting",
                2: "Some - I've invested before",
                3: "Extensive - I'm very experienced"
            }
        },
        4: {
            "text": "What percentage of your income can you afford to lose?",
            "type": "choice",
            "weight": 0.25,
            "options": {
                1: "0-5% - Very little",
                2: "5-10% - Some",
                3: "10-20% - A moderate amount",
                4: "20%+ - A significant amount"
            }
        },
        5: {
            "text": "How do you feel about market volatility?",
            "type": "scale",
            "weight": 0.15,
            "options": {
                1: "Very uncomfortable",
                2: "Somewhat uncomfortable",
                3: "Neutral",
                4: "Somewhat comfortable",
                5: "Very comfortable"
            }
        }
    }
    
    def __init__(self, db_path: str = 'auth.db'):
        """Initialize the service with database path"""
        self.db_path = db_path
    
    def calculate_risk_score(self, answers: Dict[int, int]) -> int:
        """
        Calculate risk tolerance score from questionnaire answers.
        
        Args:
            answers: Dictionary mapping question_id to answer value
                    Example: {1: 3, 2: 2, 3: 1, 4: 2, 5: 4}
        
        Returns:
            Risk score from 1-10 (1=Conservative, 10=Aggressive)
        
        Raises:
            ValueError: If answers are incomplete or invalid
        """
        # Validate that all questions are answered
        if not self._is_complete(answers):
            missing = set(self.QUESTIONS.keys()) - set(answers.keys())
            raise ValueError(f"Incomplete assessment. Missing questions: {missing}")
        
        # Validate answer values
        for q_id, answer in answers.items():
            if q_id not in self.QUESTIONS:
                raise ValueError(f"Invalid question ID: {q_id}")
            
            max_value = max(self.QUESTIONS[q_id]["options"].keys())
            if not isinstance(answer, int) or answer < 1 or answer > max_value:
                raise ValueError(
                    f"Invalid answer for question {q_id}. "
                    f"Must be integer between 1 and {max_value}"
                )
        
        # Calculate weighted score
        weighted_sum = 0.0
        max_possible = 0.0
        
        for q_id, answer in answers.items():
            question = self.QUESTIONS[q_id]
            weight = question["weight"]
            max_answer = max(question["options"].keys())
            
            # Normalize answer to 0-1 scale, then apply weight
            normalized = (answer - 1) / (max_answer - 1) if max_answer > 1 else 0
            weighted_sum += normalized * weight
            max_possible += weight
        
        # Normalize to 1-10 scale
        # weighted_sum is now between 0 and 1
        risk_score = int(round(weighted_sum * 9 + 1))
        
        # Ensure score is within bounds
        return max(1, min(10, risk_score))
    
    def _is_complete(self, answers: Dict[int, int]) -> bool:
        """Check if all required questions have been answered"""
        return all(q_id in answers for q_id in self.QUESTIONS.keys())
    
    def validate_assessment(self, answers: Dict[int, int]) -> Tuple[bool, Optional[str]]:
        """
        Validate assessment answers without calculating score.
        
        Args:
            answers: Dictionary mapping question_id to answer value
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check completeness
            if not self._is_complete(answers):
                missing = set(self.QUESTIONS.keys()) - set(answers.keys())
                return False, f"Incomplete assessment. Missing questions: {sorted(missing)}"
            
            # Validate each answer
            for q_id, answer in answers.items():
                if q_id not in self.QUESTIONS:
                    return False, f"Invalid question ID: {q_id}"
                
                max_value = max(self.QUESTIONS[q_id]["options"].keys())
                if not isinstance(answer, int) or answer < 1 or answer > max_value:
                    return False, f"Invalid answer for question {q_id}"
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_risk_category(self, risk_score: int) -> str:
        """
        Get risk category label from numeric score.
        
        Args:
            risk_score: Risk tolerance score (1-10)
        
        Returns:
            Category string: 'Conservative', 'Moderate', or 'Aggressive'
        """
        if risk_score < 1 or risk_score > 10:
            raise ValueError(f"Risk score must be between 1 and 10, got {risk_score}")
        
        if risk_score <= 3:
            return "Conservative"
        elif risk_score <= 6:
            return "Moderate"
        else:
            return "Aggressive"
    
    def get_questions(self) -> Dict:
        """Return all assessment questions for frontend display"""
        return self.QUESTIONS
