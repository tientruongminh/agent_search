from app.core.budget import BudgetController
from app.schemas.intent import SearchGoal


def test_budget_controller_respects_goal_and_override() -> None:
    budget = BudgetController().init_budget(SearchGoal.EXAM_PREPARATION, institution_strict=True, max_downloads=7)
    assert budget.max_queries_per_job >= 6
    assert budget.max_downloads == 7
    assert budget.max_reflection_loops == 1

