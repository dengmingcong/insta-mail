from src.projects import service


def test_auth_ops():
    assert service.auth_pm()
