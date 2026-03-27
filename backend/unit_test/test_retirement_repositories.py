"""
Property-based tests for Retirement Planning Calculator repositories

Tests data persistence, CRUD operations, and data integrity
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import json
import uuid
from datetime import datetime
import tempfile
import os

from backend.retirement_planning.repositories import (
    PlanRepository, ScenarioRepository, ActionPlanRepository, HistoryRepository
)
from backend.retirement_planning.models import (
    RetirementPlan, RetirementScenario, ActionPlanItem
)
from backend.retirement_planning.migrations import RetirementPlanningMigrations


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create tables
    RetirementPlanningMigrations.create_tables(path)
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def plan_repo(temp_db):
    """Create plan repository with temp database"""
    return PlanRepository(temp_db)


@pytest.fixture
def scenario_repo(temp_db):
    """Create scenario repository with temp database"""
    return ScenarioRepository(temp_db)


@pytest.fixture
def action_repo(temp_db):
    """Create action plan repository with temp database"""
    return ActionPlanRepository(temp_db)


@pytest.fixture
def history_repo(temp_db):
    """Create history repository with temp database"""
    return HistoryRepository(temp_db)


# Strategy for generating valid retirement plans
def retirement_plan_strategy():
    return st.builds(
        RetirementPlan,
        plan_id=st.uuids().map(str),
        user_id=st.integers(min_value=1, max_value=10000),
        plan_name=st.text(min_size=1, max_size=100),
        current_age=st.integers(min_value=18, max_value=60),
        retirement_age=st.integers(min_value=61, max_value=75),
        current_salary=st.floats(min_value=100000, max_value=10000000),
        current_monthly_expenses=st.floats(min_value=10000, max_value=500000),
        current_savings=st.floats(min_value=0, max_value=5000000),
        inflation_rate=st.floats(min_value=0.02, max_value=0.10),
        investment_return_rate=st.floats(min_value=0.05, max_value=0.15),
        life_expectancy=st.integers(min_value=75, max_value=100),
        retirement_corpus=st.floats(min_value=1000000, max_value=100000000),
        monthly_expenses_at_retirement=st.floats(min_value=10000, max_value=500000),
        required_monthly_savings=st.floats(min_value=1000, max_value=500000),
        projected_savings=st.floats(min_value=0, max_value=100000000),
        gap=st.floats(min_value=-50000000, max_value=50000000),
        gap_percentage=st.floats(min_value=-100, max_value=100),
        readiness_score=st.floats(min_value=0, max_value=100),
        readiness_classification=st.sampled_from(['critical', 'poor', 'fair', 'good', 'excellent']),
        financial_health_factor=st.floats(min_value=0, max_value=100),
        savings_adequacy_factor=st.floats(min_value=0, max_value=100),
        savings_rate_factor=st.floats(min_value=0, max_value=100),
        debt_burden_factor=st.floats(min_value=0, max_value=100),
        time_horizon_factor=st.floats(min_value=0, max_value=100),
        is_primary=st.booleans(),
        deleted_at=st.none()
    )


class TestPlanRepository:
    """Tests for PlanRepository"""
    
    @given(retirement_plan_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_and_read_plan(self, plan_repo, plan):
        """Property 20: Data Persistence - Create and read plan"""
        # Create plan
        plan_id = plan_repo.create(plan)
        assert plan_id == plan.plan_id
        
        # Read plan
        retrieved = plan_repo.read(plan_id)
        assert retrieved is not None
        assert retrieved.plan_id == plan.plan_id
        assert retrieved.user_id == plan.user_id
        assert retrieved.plan_name == plan.plan_name
        assert retrieved.current_age == plan.current_age
        assert retrieved.retirement_age == plan.retirement_age
    
    @given(retirement_plan_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_plan(self, plan_repo, plan):
        """Property 20: Data Persistence - Update plan"""
        # Create plan
        plan_repo.create(plan)
        
        # Update plan
        plan.plan_name = "Updated Plan Name"
        plan.current_salary = 500000
        plan.readiness_score = 75.5
        
        success = plan_repo.update(plan)
        assert success
        
        # Verify update
        retrieved = plan_repo.read(plan.plan_id)
        assert retrieved.plan_name == "Updated Plan Name"
        assert retrieved.current_salary == 500000
        assert retrieved.readiness_score == 75.5
    
    @given(retirement_plan_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_soft_delete_plan(self, plan_repo, plan):
        """Property 20: Data Persistence - Soft delete plan"""
        # Create plan
        plan_repo.create(plan)
        
        # Delete plan
        success = plan_repo.delete(plan.plan_id)
        assert success
        
        # Verify soft delete (should not be readable)
        retrieved = plan_repo.read(plan.plan_id)
        assert retrieved is None
    
    @given(st.lists(retirement_plan_strategy(), min_size=1, max_size=5))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_plans_by_user(self, plan_repo, plans):
        """Property 20: Data Persistence - List plans by user"""
        user_id = plans[0].user_id
        
        # Create plans for same user
        for plan in plans:
            plan.user_id = user_id
            plan_repo.create(plan)
        
        # List plans
        retrieved = plan_repo.list_by_user(user_id)
        assert len(retrieved) == len(plans)
        
        # Verify all plans are present
        retrieved_ids = {p.plan_id for p in retrieved}
        expected_ids = {p.plan_id for p in plans}
        assert retrieved_ids == expected_ids
    
    @given(retirement_plan_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_primary_plan_management(self, plan_repo, plan):
        """Property 20: Data Persistence - Primary plan management"""
        user_id = plan.user_id
        
        # Create plan
        plan_repo.create(plan)
        
        # Set as primary
        success = plan_repo.set_primary_plan(plan.plan_id, user_id)
        assert success
        
        # Verify primary
        primary = plan_repo.get_primary_plan(user_id)
        assert primary is not None
        assert primary.plan_id == plan.plan_id
        assert primary.is_primary


def scenario_strategy():
    return st.builds(
        RetirementScenario,
        scenario_id=st.uuids().map(str),
        plan_id=st.uuids().map(str),
        scenario_name=st.text(min_size=1, max_size=100),
        retirement_age=st.integers(min_value=60, max_value=75),
        monthly_savings=st.floats(min_value=1000, max_value=500000),
        investment_return_rate=st.floats(min_value=0.05, max_value=0.15),
        inflation_rate=st.floats(min_value=0.02, max_value=0.10),
        retirement_corpus=st.floats(min_value=1000000, max_value=100000000),
        required_monthly_savings=st.floats(min_value=1000, max_value=500000),
        projected_savings=st.floats(min_value=0, max_value=100000000),
        gap=st.floats(min_value=-50000000, max_value=50000000),
        readiness_score=st.floats(min_value=0, max_value=100),
        is_primary=st.booleans()
    )


class TestScenarioRepository:
    """Tests for ScenarioRepository"""
    
    @given(scenario_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_and_read_scenario(self, scenario_repo, scenario):
        """Property 20: Data Persistence - Create and read scenario"""
        # Create scenario
        scenario_id = scenario_repo.create(scenario)
        assert scenario_id == scenario.scenario_id
        
        # Read scenario
        retrieved = scenario_repo.read(scenario_id)
        assert retrieved is not None
        assert retrieved.scenario_id == scenario.scenario_id
        assert retrieved.plan_id == scenario.plan_id
        assert retrieved.scenario_name == scenario.scenario_name
    
    @given(scenario_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_scenario(self, scenario_repo, scenario):
        """Property 20: Data Persistence - Update scenario"""
        # Create scenario
        scenario_repo.create(scenario)
        
        # Update scenario
        scenario.scenario_name = "Updated Scenario"
        scenario.monthly_savings = 50000
        
        success = scenario_repo.update(scenario)
        assert success
        
        # Verify update
        retrieved = scenario_repo.read(scenario.scenario_id)
        assert retrieved.scenario_name == "Updated Scenario"
        assert retrieved.monthly_savings == 50000
    
    @given(st.lists(scenario_strategy(), min_size=1, max_size=5))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_scenarios_by_plan(self, scenario_repo, scenarios):
        """Property 20: Data Persistence - List scenarios by plan"""
        plan_id = scenarios[0].plan_id
        
        # Create scenarios for same plan
        for scenario in scenarios:
            scenario.plan_id = plan_id
            scenario_repo.create(scenario)
        
        # List scenarios
        retrieved = scenario_repo.list_by_plan(plan_id)
        assert len(retrieved) == len(scenarios)


def action_item_strategy():
    return st.builds(
        ActionPlanItem,
        action_id=st.uuids().map(str),
        priority=st.integers(min_value=1, max_value=5),
        action_type=st.sampled_from(['increase_savings', 'improve_returns', 'delay_retirement']),
        description=st.text(min_size=1, max_size=200),
        estimated_impact_on_score=st.floats(min_value=0, max_value=50),
        timeline=st.sampled_from(['immediate', 'short_term', 'long_term'])
    )


class TestActionPlanRepository:
    """Tests for ActionPlanRepository"""
    
    @given(st.lists(action_item_strategy(), min_size=1, max_size=5))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_and_read_action_plan(self, action_repo, actions):
        """Property 20: Data Persistence - Create and read action plan"""
        plan_id = str(uuid.uuid4())
        
        # Create action plan
        action_id = action_repo.create(plan_id, actions)
        assert action_id is not None
        
        # Read action plan
        retrieved = action_repo.read(action_id)
        assert retrieved is not None
        assert len(retrieved) == len(actions)
    
    @given(st.lists(action_item_strategy(), min_size=1, max_size=5))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_action_plan(self, action_repo, actions):
        """Property 20: Data Persistence - Update action plan"""
        plan_id = str(uuid.uuid4())
        
        # Create action plan
        action_id = action_repo.create(plan_id, actions)
        
        # Update action plan
        new_actions = [
            ActionPlanItem(
                action_id=str(uuid.uuid4()),
                priority=1,
                action_type='increase_savings',
                description='Updated action',
                estimated_impact_on_score=25.0,
                timeline='immediate'
            )
        ]
        
        success = action_repo.update(action_id, new_actions)
        assert success
        
        # Verify update
        retrieved = action_repo.read(action_id)
        assert len(retrieved) == 1
        assert retrieved[0].description == 'Updated action'


class TestHistoryRepository:
    """Tests for HistoryRepository"""
    
    @given(retirement_plan_strategy())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_snapshot(self, history_repo, plan):
        """Property 20: Data Persistence - Create plan snapshot"""
        # Create snapshot
        history_id = history_repo.create_snapshot(plan.plan_id, plan, "Initial creation")
        assert history_id is not None
        
        # Read snapshot
        retrieved = history_repo.get_snapshot(history_id)
        assert retrieved is not None
        assert retrieved.plan_id == plan.plan_id
    
    @given(st.lists(retirement_plan_strategy(), min_size=1, max_size=5))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_plan_history(self, history_repo, plans):
        """Property 20: Data Persistence - List plan history"""
        plan_id = plans[0].plan_id
        
        # Create multiple snapshots
        for i, plan in enumerate(plans):
            plan.plan_id = plan_id
            history_repo.create_snapshot(plan_id, plan, f"Update {i}")
        
        # List history
        history = history_repo.list_by_plan(plan_id)
        assert len(history) == len(plans)
    
    @given(st.lists(retirement_plan_strategy(), min_size=10, max_size=15))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delete_old_snapshots(self, history_repo, plans):
        """Property 20: Data Persistence - Delete old snapshots"""
        plan_id = plans[0].plan_id
        
        # Create multiple snapshots
        for i, plan in enumerate(plans):
            plan.plan_id = plan_id
            history_repo.create_snapshot(plan_id, plan, f"Update {i}")
        
        # Delete old snapshots, keep only 5
        deleted = history_repo.delete_old_snapshots(plan_id, keep_count=5)
        assert deleted == len(plans) - 5
        
        # Verify only 5 remain
        history = history_repo.list_by_plan(plan_id)
        assert len(history) == 5
