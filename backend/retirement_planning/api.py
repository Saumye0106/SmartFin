"""
Flask API endpoints for Retirement Planning Calculator

Provides REST endpoints for:
- Plan creation and management
- Scenario analysis
- Readiness scoring
- Recommendations
- Data export
"""

from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime
import logging

from .calculation_engine import RetirementCalculationEngine
from .readiness_scoring_engine import RetirementReadinessScoringEngine
from .scenario_engine import ScenarioAnalysisEngine
from .recommendation_engine import RecommendationEngine
from .integration_manager import IntegrationManager
from .serializer import RetirementPlanSerializer
from .repositories import (
    PlanRepository, ScenarioRepository, ActionPlanRepository, HistoryRepository
)
from .models import RetirementPlan, RetirementScenario, ActionPlanItem
from .validators import RetirementPlanValidator
from .exceptions import (
    RetirementPlanningException, ValidationError, CalculationError,
    IntegrationError
)

logger = logging.getLogger(__name__)

# Create Blueprint
retirement_bp = Blueprint('retirement', __name__, url_prefix='/api/retirement')

# Initialize repositories
plan_repo = PlanRepository()
scenario_repo = ScenarioRepository()
action_repo = ActionPlanRepository()
history_repo = HistoryRepository()

# Initialize engines
calc_engine = RetirementCalculationEngine()
scoring_engine = RetirementReadinessScoringEngine()
scenario_engine = ScenarioAnalysisEngine()
recommendation_engine = RecommendationEngine()
integration_manager = IntegrationManager()
serializer = RetirementPlanSerializer()
validator = RetirementPlanValidator()


@retirement_bp.route('/calculate', methods=['POST'])
def calculate_retirement_plan():
    """Calculate retirement plan from input parameters"""
    try:
        data = request.get_json()
        logger.info(f"Calculating retirement plan for user {data.get('user_id')}")
        
        # Validate input
        validator.validate_plan_inputs(data)
        
        # Create plan object
        plan_id = str(uuid.uuid4())
        user_id = data.get('user_id')
        
        plan = RetirementPlan(
            plan_id=plan_id,
            user_id=user_id,
            plan_name=data.get('plan_name', f'Plan {datetime.now().strftime("%Y-%m-%d")}'),
            current_age=data['current_age'],
            retirement_age=data['retirement_age'],
            current_salary=data['current_salary'],
            current_monthly_expenses=data['current_monthly_expenses'],
            current_savings=data['current_savings'],
            inflation_rate=data.get('inflation_rate', 0.06),
            investment_return_rate=data.get('investment_return_rate', 0.10),
            life_expectancy=data.get('life_expectancy', 85),
            desired_retirement_lifestyle=data.get('desired_retirement_lifestyle')
        )
        
        # Calculate retirement corpus
        # Use desired_retirement_lifestyle if provided, otherwise use current_monthly_expenses
        corpus_calculation_expense = plan.desired_retirement_lifestyle if plan.desired_retirement_lifestyle else plan.current_monthly_expenses
        
        retirement_corpus_result = calc_engine.calculate_retirement_corpus(
            plan.current_age, plan.retirement_age, corpus_calculation_expense,
            plan.inflation_rate, plan.life_expectancy
        )
        plan.retirement_corpus, plan.monthly_expenses_at_retirement = retirement_corpus_result
        
        # Calculate actual monthly savings (income minus expenses)
        actual_monthly_savings = max(0, (plan.current_salary / 12) - plan.current_monthly_expenses)
        
        # Calculate projected savings based on ACTUAL current savings behavior
        plan.projected_savings = calc_engine.calculate_projected_savings(
            current_savings=plan.current_savings,
            monthly_savings=actual_monthly_savings,
            current_age=plan.current_age,
            retirement_age=plan.retirement_age,
            return_rate=plan.investment_return_rate
        )
        
        # Calculate gap
        plan.gap = plan.retirement_corpus - plan.projected_savings
        plan.gap_percentage = (plan.gap / plan.retirement_corpus * 100) if plan.retirement_corpus > 0 else 0
        
        # Calculate required monthly savings to close the gap
        plan.required_monthly_savings = calc_engine.calculate_required_monthly_savings(
            current_savings=plan.current_savings,
            corpus_target=plan.retirement_corpus,
            current_age=plan.current_age,
            retirement_age=plan.retirement_age,
            return_rate=plan.investment_return_rate
        )
        
        # Get financial health score
        try:
            financial_health_score = integration_manager.get_financial_health_score(user_id)
        except IntegrationError:
            financial_health_score = 50.0
        
        # Calculate readiness score using full assessment
        readiness = scoring_engine.calculate_full_assessment(
            current_age=plan.current_age,
            retirement_age=plan.retirement_age,
            # Use projected savings for adequacy so readiness reflects
            # whether current savings behavior can reach the target corpus.
            current_savings=plan.projected_savings,
            corpus_target=plan.retirement_corpus,
            required_monthly_savings=plan.required_monthly_savings,
            current_monthly_income=plan.current_salary / 12,
            total_loan_amount=0,  # TODO: Get from loan history
            annual_salary=plan.current_salary,
            financial_health_score=financial_health_score
        )
        
        plan.readiness_score = readiness.readiness_score
        plan.readiness_classification = readiness.classification
        plan.financial_health_factor = readiness.financial_health_factor
        plan.savings_adequacy_factor = readiness.savings_adequacy_factor
        plan.savings_rate_factor = readiness.savings_rate_factor
        plan.debt_burden_factor = readiness.debt_burden_factor
        plan.time_horizon_factor = readiness.time_horizon_factor
        
        # Save plan
        plan_repo.create(plan)
        
        # Create history snapshot
        history_repo.create_snapshot(plan_id, plan, "Plan created")
        
        serialized_plan = serializer.serialize_plan(plan)
        # Include actual monthly savings in response for frontend display
        serialized_plan['actual_monthly_savings'] = actual_monthly_savings
        logger.info(f"Plan {plan_id} created successfully for user {user_id}")
        
        return jsonify({
            'success': True,
            'plan_id': plan_id,
            'plan': serialized_plan
        }), 201
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except CalculationError as e:
        logger.error(f"Calculation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        import traceback
        logger.error(f"Error calculating plan: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Internal server error', 'debug': str(e)}), 500


@retirement_bp.route('/plans', methods=['POST'])
def create_plan():
    """Create new retirement plan"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        # Validate input
        validator.validate_plan_inputs(data)
        
        # Create plan
        plan_id = str(uuid.uuid4())
        plan = RetirementPlan(
            plan_id=plan_id,
            user_id=user_id,
            plan_name=data.get('plan_name', f'Plan {datetime.now().strftime("%Y-%m-%d")}'),
            current_age=data['current_age'],
            retirement_age=data['retirement_age'],
            current_salary=data['current_salary'],
            current_monthly_expenses=data['current_monthly_expenses'],
            current_savings=data['current_savings'],
            inflation_rate=data.get('inflation_rate', 0.06),
            investment_return_rate=data.get('investment_return_rate', 0.10),
            life_expectancy=data.get('life_expectancy', 85)
        )
        
        plan_repo.create(plan)
        history_repo.create_snapshot(plan_id, plan, "Plan created")
        
        return jsonify({
            'success': True,
            'plan_id': plan_id,
            'plan': serializer.serialize_plan(plan)
        }), 201
    
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/plans/<user_id>', methods=['GET'])
def get_user_plans(user_id):
    """Get all plans for a user"""
    try:
        user_id = int(user_id)
        plans = plan_repo.list_by_user(user_id)
        
        return jsonify({
            'success': True,
            'plans': [serializer.serialize_plan(p) for p in plans]
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving plans: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Get specific retirement plan"""
    try:
        plan = plan_repo.read(plan_id)
        
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        return jsonify({
            'success': True,
            'plan': serializer.serialize_plan(plan)
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving plan: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/plans/<plan_id>', methods=['PUT'])
def update_plan(plan_id):
    """Update retirement plan"""
    try:
        plan = plan_repo.read(plan_id)
        
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'plan_name' in data:
            plan.plan_name = data['plan_name']
        if 'current_age' in data:
            plan.current_age = data['current_age']
        if 'retirement_age' in data:
            plan.retirement_age = data['retirement_age']
        if 'current_salary' in data:
            plan.current_salary = data['current_salary']
        if 'current_monthly_expenses' in data:
            plan.current_monthly_expenses = data['current_monthly_expenses']
        if 'current_savings' in data:
            plan.current_savings = data['current_savings']
        if 'inflation_rate' in data:
            plan.inflation_rate = data['inflation_rate']
        if 'investment_return_rate' in data:
            plan.investment_return_rate = data['investment_return_rate']
        
        plan.update_timestamp()
        plan_repo.update(plan)
        history_repo.create_snapshot(plan_id, plan, "Plan updated")
        
        return jsonify({
            'success': True,
            'plan': serializer.serialize_plan(plan)
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating plan: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/plans/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    """Delete retirement plan"""
    try:
        plan = plan_repo.read(plan_id)
        
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        plan_repo.delete(plan_id)
        
        return jsonify({'success': True, 'message': 'Plan deleted'}), 200
    
    except Exception as e:
        logger.error(f"Error deleting plan: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/scenarios', methods=['POST'])
def create_scenario():
    """Create scenario for a plan"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        
        # Get base plan
        plan = plan_repo.read(plan_id)
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        # Create scenario
        scenario_id = str(uuid.uuid4())
        scenario = RetirementScenario(
            scenario_id=scenario_id,
            plan_id=plan_id,
            scenario_name=data.get('scenario_name', f'Scenario {datetime.now().strftime("%Y-%m-%d")}'),
            retirement_age=data.get('retirement_age', plan.retirement_age),
            monthly_savings=data.get('monthly_savings', plan.required_monthly_savings),
            investment_return_rate=data.get('investment_return_rate', plan.investment_return_rate),
            inflation_rate=data.get('inflation_rate', plan.inflation_rate),
            desired_retirement_lifestyle=data.get('desired_retirement_lifestyle')
        )
        
        # Calculate scenario results
        corpus_result = calc_engine.calculate_retirement_corpus(
            plan.current_age, scenario.retirement_age, plan.current_monthly_expenses,
            scenario.inflation_rate, plan.life_expectancy
        )
        scenario.retirement_corpus = corpus_result[0]  # (corpus, monthly_expenses_at_retirement)
        
        scenario.projected_savings = calc_engine.calculate_projected_savings(
            plan.current_savings, scenario.monthly_savings,
            plan.current_age, scenario.retirement_age,
            scenario.investment_return_rate
        )
        
        scenario.gap = scenario.retirement_corpus - scenario.projected_savings
        
        scenario_repo.create(scenario)
        
        return jsonify({
            'success': True,
            'scenario_id': scenario_id,
            'scenario': {
                'scenario_id': scenario.scenario_id,
                'plan_id': scenario.plan_id,
                'scenario_name': scenario.scenario_name,
                'retirement_age': scenario.retirement_age,
                'monthly_savings': scenario.monthly_savings,
                'retirement_corpus': scenario.retirement_corpus,
                'projected_savings': scenario.projected_savings,
                'gap': scenario.gap
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating scenario: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/scenarios/<plan_id>', methods=['GET'])
def get_scenarios(plan_id):
    """Get all scenarios for a plan"""
    try:
        scenarios = scenario_repo.list_by_plan(plan_id)
        
        return jsonify({
            'success': True,
            'scenarios': [
                {
                    'scenario_id': s.scenario_id,
                    'plan_id': s.plan_id,
                    'scenario_name': s.scenario_name,
                    'retirement_age': s.retirement_age,
                    'monthly_savings': s.monthly_savings,
                    'retirement_corpus': s.retirement_corpus,
                    'projected_savings': s.projected_savings,
                    'gap': s.gap,
                    'readiness_score': s.readiness_score
                }
                for s in scenarios
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving scenarios: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/readiness', methods=['POST'])
def calculate_readiness():
    """Calculate retirement readiness score"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        
        plan = plan_repo.read(plan_id)
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        # Get financial health score
        try:
            financial_health_score = integration_manager.get_financial_health_score(plan.user_id)
        except IntegrationError:
            financial_health_score = 50.0
        
        # Calculate readiness using full assessment
        readiness = scoring_engine.calculate_full_assessment(
            current_age=plan.current_age,
            retirement_age=plan.retirement_age,
            # Reuse projected savings so readiness remains aligned with
            # the main plan calculation pathway.
            current_savings=plan.projected_savings,
            corpus_target=plan.retirement_corpus,
            required_monthly_savings=plan.required_monthly_savings,
            current_monthly_income=plan.current_salary / 12,
            total_loan_amount=0,
            annual_salary=plan.current_salary,
            financial_health_score=financial_health_score
        )
        
        return jsonify({
            'success': True,
            'readiness_score': readiness.readiness_score,
            'classification': readiness.classification,
            'factors': {
                'financial_health': readiness.financial_health_factor,
                'savings_adequacy': readiness.savings_adequacy_factor,
                'savings_rate': readiness.savings_rate_factor,
                'debt_burden': readiness.debt_burden_factor,
                'time_horizon': readiness.time_horizon_factor
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error calculating readiness: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/recommendations/<plan_id>', methods=['GET'])
def get_recommendations(plan_id):
    """Get action plan recommendations for a plan"""
    try:
        plan = plan_repo.read(plan_id)
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        # Get existing action plan or generate new one
        actions = action_repo.get_by_plan(plan_id)
        
        if not actions:
            # Generate new recommendations
            generated = recommendation_engine.generate_action_plan(
                readiness_score=plan.readiness_score,
                financial_health_factor=plan.financial_health_factor,
                savings_adequacy_factor=plan.savings_adequacy_factor,
                savings_rate_factor=plan.savings_rate_factor,
                debt_burden_factor=plan.debt_burden_factor,
                time_horizon_factor=plan.time_horizon_factor,
                current_age=plan.current_age,
                retirement_age=plan.retirement_age,
                required_monthly_savings=plan.required_monthly_savings,
                current_monthly_income=plan.current_salary / 12,
                total_loan_amount=0,
                annual_salary=plan.current_salary,
                gap=plan.gap,
                corpus_target=plan.retirement_corpus
            )
            
            # Convert dicts to ActionPlanItem objects and save
            action_items = [ActionPlanItem(**d) for d in generated]
            action_repo.create(plan_id, action_items)
            
            # Re-fetch as ActionPlanItem objects
            actions = action_repo.get_by_plan(plan_id)
        
        return jsonify({
            'success': True,
            'recommendations': [
                {
                    'action_id': a.action_id,
                    'priority': a.priority,
                    'action_type': a.action_type,
                    'description': a.description,
                    'estimated_impact': a.estimated_impact_on_score,
                    'timeline': a.timeline
                }
                for a in actions
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@retirement_bp.route('/export', methods=['POST'])
def export_plan():
    """Export retirement plan as JSON"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        
        plan = plan_repo.read(plan_id)
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        # Serialize plan
        plan_json = serializer.serialize_plan(plan)
        
        return jsonify({
            'success': True,
            'plan': plan_json
        }), 200
    
    except Exception as e:
        logger.error(f"Error exporting plan: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
