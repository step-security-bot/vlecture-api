from tests.utils.test_db import client


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
