"""
Tests for RiskAssessmentService
Includes property-based tests and unit tests
"""

import sys
from hypothesis import given, strategies as st, assume
from risk_assessment_service import RiskAssessmentService


def test_property_risk_score_range():
    """
    Property 11: Risk score within valid range
    Validates: Requirements 3.2
    
    For any valid set of answers, the calculated risk score must be between 1 and 10.
    """
    print("\nProperty 11: Risk score within valid range (100 examples)...")
    
    service = RiskAssessmentService()
    
    # Generate 100 random valid answer sets
    @given(
        q1=st.integers(min_value=1, max_value=5),
        q2=st.integers(min_value=1, max_value=3),
        q3=st.integers(min_value=1, max_value=3),
        q4=st.integers(min_value=1, max_value=4),
        q5=st.integers(min_value=1, max_value=5)
    )
    def property_test(q1, q2, q3, q4, q5):
        answers = {1: q1, 2: q2, 3: q3, 4: q4, 5: q5}
        score = service.calculate_risk_score(answers)
        
        # Score must be in valid range
        assert 1 <= score <= 10, f"Score {score} out of range for answers {answers}"
        
        # Score must be an integer
        assert isinstance(score, int), f"Score must be integer, got {type(score)}"
    
    property_test()
    print("✓ PASSED")


def test_property_incomplete_assessment_rejection():
    """
    Property 13: Incomplete assessment rejection
    Validates: Requirements 3.5
    
    Any assessment with missing answers must be rejected with a clear error.
    """
    print("\nProperty 13: Incomplete assessment rejection...")
    
    service = RiskAssessmentService()
    
    # Test various incomplete answer sets
    @given(
        q1=st.integers(min_value=1, max_value=5),
        q2=st.integers(min_value=1, max_value=3),
        q3=st.integers(min_value=1, max_value=3),
        q4=st.integers(min_value=1, max_value=4),
        missing_question=st.integers(min_value=1, max_value=5)
    )
    def property_test(q1, q2, q3, q4, missing_question):
        # Create complete answers then remove one
        answers = {1: q1, 2: q2, 3: q3, 4: q4, 5: 3}
        del answers[missing_question]
        
        # Should raise ValueError
        try:
            service.calculate_risk_score(answers)
            assert False, f"Should reject incomplete answers: {answers}"
        except ValueError as e:
            assert "Incomplete assessment" in str(e)
            assert str(missing_question) in str(e)
    
    property_test()
    print("✓ PASSED")


def test_unit_conservative_answers():
    """
    Unit test: All conservative answers should give low score (1-3)
    Validates: Requirements 3.2
    """
    print("\nUnit test: Conservative answers...")
    
    service = RiskAssessmentService()
    
    # Most conservative answers
    answers = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
    score = service.calculate_risk_score(answers)
    category = service.get_risk_category(score)
    
    assert 1 <= score <= 3, f"Conservative answers should give score 1-3, got {score}"
    assert category == "Conservative", f"Expected Conservative, got {category}"
    print(f"  Conservative answers → Score: {score}, Category: {category}")
    print("✓ PASSED")


def test_unit_aggressive_answers():
    """
    Unit test: All aggressive answers should give high score (7-10)
    Validates: Requirements 3.2
    """
    print("\nUnit test: Aggressive answers...")
    
    service = RiskAssessmentService()
    
    # Most aggressive answers
    answers = {1: 5, 2: 3, 3: 3, 4: 4, 5: 5}
    score = service.calculate_risk_score(answers)
    category = service.get_risk_category(score)
    
    assert 7 <= score <= 10, f"Aggressive answers should give score 7-10, got {score}"
    assert category == "Aggressive", f"Expected Aggressive, got {category}"
    print(f"  Aggressive answers → Score: {score}, Category: {category}")
    print("✓ PASSED")


def test_unit_moderate_answers():
    """
    Unit test: Mixed answers should give moderate score (4-6)
    Validates: Requirements 3.2
    """
    print("\nUnit test: Moderate answers...")
    
    service = RiskAssessmentService()
    
    # Moderate/mixed answers
    answers = {1: 3, 2: 2, 3: 2, 4: 2, 5: 3}
    score = service.calculate_risk_score(answers)
    category = service.get_risk_category(score)
    
    assert 4 <= score <= 6, f"Moderate answers should give score 4-6, got {score}"
    assert category == "Moderate", f"Expected Moderate, got {category}"
    print(f"  Moderate answers → Score: {score}, Category: {category}")
    print("✓ PASSED")


def test_unit_incomplete_answers():
    """
    Unit test: Incomplete answers should be rejected
    Validates: Requirements 3.5
    """
    print("\nUnit test: Incomplete answers rejection...")
    
    service = RiskAssessmentService()
    
    # Missing question 5
    answers = {1: 3, 2: 2, 3: 2, 4: 2}
    
    try:
        service.calculate_risk_score(answers)
        assert False, "Should reject incomplete answers"
    except ValueError as e:
        assert "Incomplete assessment" in str(e)
        assert "5" in str(e)
        print(f"  Correctly rejected: {e}")
    
    print("✓ PASSED")


def test_unit_invalid_answer_values():
    """
    Unit test: Invalid answer values should be rejected
    Validates: Requirements 3.5
    """
    print("\nUnit test: Invalid answer values...")
    
    service = RiskAssessmentService()
    
    # Answer out of range for question 1 (max is 5)
    answers = {1: 6, 2: 2, 3: 2, 4: 2, 5: 3}
    
    try:
        service.calculate_risk_score(answers)
        assert False, "Should reject invalid answer value"
    except ValueError as e:
        assert "Invalid answer" in str(e)
        print(f"  Correctly rejected out-of-range: {e}")
    
    # Answer below minimum
    answers = {1: 0, 2: 2, 3: 2, 4: 2, 5: 3}
    
    try:
        service.calculate_risk_score(answers)
        assert False, "Should reject invalid answer value"
    except ValueError as e:
        assert "Invalid answer" in str(e)
        print(f"  Correctly rejected below minimum: {e}")
    
    print("✓ PASSED")


def test_unit_validation_method():
    """
    Unit test: validate_assessment method
    """
    print("\nUnit test: validate_assessment method...")
    
    service = RiskAssessmentService()
    
    # Valid answers
    answers = {1: 3, 2: 2, 3: 2, 4: 2, 5: 3}
    is_valid, error = service.validate_assessment(answers)
    assert is_valid, f"Valid answers should pass: {error}"
    assert error is None
    
    # Invalid answers (missing question)
    answers = {1: 3, 2: 2, 3: 2, 4: 2}
    is_valid, error = service.validate_assessment(answers)
    assert not is_valid, "Incomplete answers should fail"
    assert error is not None
    assert "Incomplete" in error
    
    print("✓ PASSED")


def test_unit_risk_categories():
    """
    Unit test: Risk category labels
    """
    print("\nUnit test: Risk category labels...")
    
    service = RiskAssessmentService()
    
    # Test all score ranges
    assert service.get_risk_category(1) == "Conservative"
    assert service.get_risk_category(2) == "Conservative"
    assert service.get_risk_category(3) == "Conservative"
    assert service.get_risk_category(4) == "Moderate"
    assert service.get_risk_category(5) == "Moderate"
    assert service.get_risk_category(6) == "Moderate"
    assert service.get_risk_category(7) == "Aggressive"
    assert service.get_risk_category(8) == "Aggressive"
    assert service.get_risk_category(9) == "Aggressive"
    assert service.get_risk_category(10) == "Aggressive"
    
    # Test invalid scores
    try:
        service.get_risk_category(0)
        assert False, "Should reject score 0"
    except ValueError:
        pass
    
    try:
        service.get_risk_category(11)
        assert False, "Should reject score 11"
    except ValueError:
        pass
    
    print("✓ PASSED")


def test_unit_get_questions():
    """
    Unit test: get_questions returns all questions
    """
    print("\nUnit test: get_questions method...")
    
    service = RiskAssessmentService()
    questions = service.get_questions()
    
    assert len(questions) == 5, "Should have 5 questions"
    
    for q_id in range(1, 6):
        assert q_id in questions, f"Missing question {q_id}"
        assert "text" in questions[q_id]
        assert "type" in questions[q_id]
        assert "weight" in questions[q_id]
        assert "options" in questions[q_id]
    
    print("✓ PASSED")


if __name__ == '__main__':
    print("Running RiskAssessmentService property-based tests...")
    
    try:
        test_property_risk_score_range()
        test_property_incomplete_assessment_rejection()
        test_unit_conservative_answers()
        test_unit_aggressive_answers()
        test_unit_moderate_answers()
        test_unit_incomplete_answers()
        test_unit_invalid_answer_values()
        test_unit_validation_method()
        test_unit_risk_categories()
        test_unit_get_questions()
        
        print("\n✅ All RiskAssessmentService tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
