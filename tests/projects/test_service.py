from src.projects import service


def test_auth_pm():
    assert service.auth_pm()
