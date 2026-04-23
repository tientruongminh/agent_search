from app.services.github_api import GitHubService


def test_github_asset_priority_prefers_document_like_paths() -> None:
    items = [
        "src/utils/helpers.py",
        "week1/lecture-notes.md",
        "slides/deep-learning.pdf",
        "README.md",
    ]

    ordered = sorted(items, key=GitHubService._asset_priority, reverse=True)

    assert ordered[0] == "slides/deep-learning.pdf"
    assert ordered[1] == "week1/lecture-notes.md"
