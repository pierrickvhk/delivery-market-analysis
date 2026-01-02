from pathlib import Path

def test_repo_structure_exists() -> None:
    assert Path("src").exists()
    assert Path("app").exists()
    assert Path("sql").exists()
