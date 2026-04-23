from app.agents.github_discovery_agent import GitHubDiscoveryAgent
from app.schemas.query_plan import Budget, QueryGroup, QueryPlan


class FakeGitHubService:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search_repositories(self, query: str, limit: int = 5):
        self.queries.append(query)
        if query == "machine learning hcmus github":
            return []
        if query == "machine learning hcmus":
            return [
                {
                    "html_url": "https://github.com/example/ml-notes",
                    "full_name": "example/ml-notes",
                    "stargazers_count": 42,
                }
            ]
        return []


def test_github_discovery_agent_relaxes_queries_when_initial_query_is_too_strict() -> None:
    service = FakeGitHubService()
    agent = GitHubDiscoveryAgent(service)
    plan = QueryPlan(
        query_groups=[
            QueryGroup(
                purpose="github_coursework",
                source_type="github_repo",
                queries=["machine learning hcmus github"],
            )
        ]
    )

    results = agent.run(plan, Budget())

    assert len(results) == 1
    assert results[0].source_url == "https://github.com/example/ml-notes"
    assert service.queries[:2] == ["machine learning hcmus github", "machine learning hcmus"]
