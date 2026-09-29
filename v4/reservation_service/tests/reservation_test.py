from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db


client = TestClient(app)


def create_reservation_mock(status="RENTED", till_date=None):
    reservation = MagicMock()
    reservation.reservation_uid = uuid4()
    reservation.library_uid = uuid4()
    reservation.book_uid = uuid4()
    reservation.username = "test_user"
    reservation.status = status
    reservation.start_date = datetime(2026, 9, 27, 10, 0, 0)
    reservation.till_date = till_date or datetime(
        2026, 9, 28, 12, 0, 0
    )
    return reservation


def create_db_mock(reservation):
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .all.return_value
    ) = [reservation]

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = reservation

    (
        db.query.return_value
        .filter.return_value
        .count.return_value
    ) = 0

    return db

@patch("app.main.httpx.get")
def test_get_reservations(mock_get):
    reservation = create_reservation_mock()
    db = create_db_mock(reservation)

    library_response = MagicMock()
    library_response.status_code = 200
    library_response.json.return_value = {
        "libraryUid": str(reservation.library_uid),
        "name": "Тестовая библиотека",
        "address": "Тестовый адрес",
        "city": "Москва",
    }

    books_response = MagicMock()
    books_response.status_code = 200
    books_response.json.return_value = [
        {
            "bookUid": str(reservation.book_uid),
            "name": "Тестовая книга",
            "author": "Тестовый автор",
            "genre": "Фантастика",
            "condition": "EXCELLENT",
            "availableCount": 1,
        }
    ]

    mock_get.side_effect = [
        library_response,
        books_response,
    ]

    app.dependency_overrides[get_db] = lambda: db

    response = client.get(
        "/api/v1/reservations",
        headers={"X-User-Name": "test_user"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["reservationUid"] == str(
        reservation.reservation_uid
    )
    assert data[0]["status"] == "RENTED"
    assert data[0]["book"]["bookUid"] == str(
        reservation.book_uid
    )
    assert data[0]["book"]["name"] == "Тестовая книга"
    assert data[0]["library"]["libraryUid"] == str(
        reservation.library_uid
    )
    assert data[0]["library"]["city"] == "Москва"


def test_get_reservations_empty():
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .all.return_value
    ) = []

    app.dependency_overrides[get_db] = lambda: db

    response = client.get(
        "/api/v1/reservations",
        headers={"X-User-Name": "test_user"},
    )

    assert response.status_code == 200
    assert response.json() == []

@patch("app.main.httpx.post")
@patch("app.main.httpx.get")
def test_create_reservation(mock_get, mock_post):
    reservation = create_reservation_mock()

    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .count.return_value
    ) = 0

    library_response = MagicMock()
    library_response.status_code = 200
    library_response.json.return_value = {
        "libraryUid": str(reservation.library_uid),
        "name": "Тестовая библиотека",
        "address": "Тестовый адрес",
        "city": "Москва",
    }

    books_response = MagicMock()
    books_response.status_code = 200
    books_response.json.return_value = [
        {
            "bookUid": str(reservation.book_uid),
            "name": "Тестовая книга",
            "author": "Тестовый автор",
            "genre": "Фантастика",
            "condition": "EXCELLENT",
            "availableCount": 1,
        }
    ]

    mock_get.side_effect = [
        library_response,
        books_response,
    ]

    take_response = MagicMock()
    take_response.status_code = 200
    take_response.json.return_value = {
        "bookUid": str(reservation.book_uid),
        "libraryUid": str(reservation.library_uid),
        "availableCount": 0,
    }

    mock_post.return_value = take_response

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        "/api/v1/reservations",
        headers={"X-User-Name": "test_user"},
        json={
            "bookUid": str(reservation.book_uid),
            "libraryUid": str(reservation.library_uid),
            "tillDate": "2026-09-28T12:00:00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "RENTED"
    assert data["book"]["bookUid"] == str(
        reservation.book_uid
    )
    assert data["book"]["name"] == "Тестовая книга"
    assert data["library"]["libraryUid"] == str(
        reservation.library_uid
    )
    assert data["rating"]["stars"] == 75

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()

    mock_post.assert_called_once()


@patch("app.main.httpx.get")
def test_create_reservation_book_unavailable(mock_get):
    reservation = create_reservation_mock()

    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .count.return_value
    ) = 0

    library_response = MagicMock()
    library_response.status_code = 200
    library_response.json.return_value = {
        "libraryUid": str(reservation.library_uid),
        "name": "Тестовая библиотека",
        "address": "Тестовый адрес",
        "city": "Москва",
    }

    books_response = MagicMock()
    books_response.status_code = 200
    books_response.json.return_value = [
        {
            "bookUid": str(reservation.book_uid),
            "name": "Тестовая книга",
            "author": "Тестовый автор",
            "genre": "Фантастика",
            "condition": "EXCELLENT",
            "availableCount": 0,
        }
    ]

    mock_get.side_effect = [
        library_response,
        books_response,
    ]

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        "/api/v1/reservations",
        headers={"X-User-Name": "test_user"},
        json={
            "bookUid": str(reservation.book_uid),
            "libraryUid": str(reservation.library_uid),
            "tillDate": "2026-09-28T12:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Book is not available"

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_reservation_past_date():
    reservation = create_reservation_mock()

    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .count.return_value
    ) = 0

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        "/api/v1/reservations",
        headers={"X-User-Name": "test_user"},
        json={
            "bookUid": str(reservation.book_uid),
            "libraryUid": str(reservation.library_uid),
            "tillDate": "2020-01-01T12:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Till date must be in the future"
    )

    db.add.assert_not_called()
    db.commit.assert_not_called()

@patch("app.main.httpx.post")
def test_return_reservation_on_time(mock_post):
    reservation = create_reservation_mock(
        till_date=datetime(2026, 9, 28, 12, 0, 0)
    )

    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = reservation

    library_response = MagicMock()
    library_response.status_code = 200

    mock_post.return_value = library_response

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        f"/api/v1/reservations/"
        f"{reservation.reservation_uid}/return",
        json={
            "condition": "EXCELLENT",
            "date": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RETURNED"
    assert reservation.status == "RETURNED"

    mock_post.assert_called_once()
    db.commit.assert_called_once()


@patch("app.main.httpx.post")
def test_return_reservation_expired(mock_post):
    reservation = create_reservation_mock(
        till_date=datetime(2026, 9, 28, 12, 0, 0)
    )

    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = reservation

    library_response = MagicMock()
    library_response.status_code = 200

    mock_post.return_value = library_response

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        f"/api/v1/reservations/"
        f"{reservation.reservation_uid}/return",
        json={
            "condition": "EXCELLENT",
            "date": "2026-09-28T15:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "EXPIRED"
    assert reservation.status == "EXPIRED"

    mock_post.assert_called_once()
    db.commit.assert_called_once()


def test_return_reservation_not_found():
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = None

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        f"/api/v1/reservations/{uuid4()}/return",
        json={
            "condition": "EXCELLENT",
            "date": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_return_reservation_already_returned():
    reservation = create_reservation_mock(
        status="RETURNED",
        till_date=datetime(2026, 9, 28, 12, 0, 0),
    )

    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = reservation

    app.dependency_overrides[get_db] = lambda: db

    response = client.post(
        f"/api/v1/reservations/"
        f"{reservation.reservation_uid}/return",
        json={
            "condition": "EXCELLENT",
            "date": "2026-09-28T10:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Reservation is not active")

    db.commit.assert_not_called()
