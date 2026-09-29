from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

client = TestClient(app)


def test_get_rating():
    rating = MagicMock()
    rating.username = "test_user"
    rating.stars = 75

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = rating

    app.dependency_overrides[get_db] = lambda: db

    response = client.get("/api/v1/rating", headers={"X-User-Name": "test_user"})

    assert response.status_code == 200
    assert response.json() == {"stars": 75}

    db.query.assert_called_once()


def test_get_rating_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: db

    response = client.get("/api/v1/rating", headers={"X-User-Name": "unknown_user"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Rating not found"