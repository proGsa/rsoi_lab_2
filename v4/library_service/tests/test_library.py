from uuid import UUID
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.models import Book, Library


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_get_libraries(client, db):
    library = Library(
        id=1,
        library_uid=UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee"),
        name="Библиотека имени 7 Непьющих",
        city="Москва",
        address="2-я Бауманская ул., д.5, стр.1",
    )

    query = MagicMock()
    query.filter.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query
    query.all.return_value = [library]

    db.query.return_value = query

    response = client.get(
        "/api/v1/libraries",
        params={
            "city": "Москва",
            "page": 0,
            "size": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["library_uid"] == str(library.library_uid)
    assert data[0]["name"] == "Библиотека имени 7 Непьющих"
    assert data[0]["city"] == "Москва"
    assert data[0]["address"] == "2-я Бауманская ул., д.5, стр.1"


def test_get_libraries_empty(client, db):
    query = MagicMock()
    query.filter.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query
    query.all.return_value = []

    db.query.return_value = query

    response = client.get(
        "/api/v1/libraries",
        params={
            "city": "Санкт-Петербург",
            "page": 0,
            "size": 10,
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_books(client, db):
    library = Library(
        id=1,
        library_uid=UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee"),
        name="Библиотека имени 7 Непьющих",
        city="Москва",
        address="2-я Бауманская ул., д.5, стр.1",
    )

    book = Book(
        id=1,
        book_uid=UUID("f7cdc58f-2caf-4b15-9727-f89dcc629b27"),
        name="Краткий курс C++ в 7 томах",
        author="Бьерн Страуструп",
        genre="Научная фантастика",
        condition="EXCELLENT",
    )

    library_query = MagicMock()
    library_query.filter.return_value.first.return_value = library

    books_query = MagicMock()
    books_query.join.return_value = books_query
    books_query.filter.return_value = books_query
    books_query.offset.return_value = books_query
    books_query.limit.return_value = books_query
    books_query.all.return_value = [(book, 1)]

    db.query.side_effect = [
        library_query,
        books_query,
    ]

    response = client.get(
        f"/api/v1/libraries/{library.library_uid}/books",
        params={
            "page": 0,
            "size": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["book_uid"] == str(book.book_uid)
    assert data[0]["name"] == "Краткий курс C++ в 7 томах"
    assert data[0]["author"] == "Бьерн Страуструп"
    assert data[0]["genre"] == "Научная фантастика"
    assert data[0]["condition"] == "EXCELLENT"
    assert data[0]["availableCount"] == 1


def test_get_books_library_not_found(client, db):
    library_query = MagicMock()
    library_query.filter.return_value.first.return_value = None

    db.query.return_value = library_query

    library_uid = "83575e12-7ce0-48ee-9931-51919ff3c9ee"

    response = client.get(
        f"/api/v1/libraries/{library_uid}/books",
        params={
            "page": 0,
            "size": 10,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Library not found"

def test_get_books_show_all_false(client, db):
    library = Library(
        id=1,
        library_uid=UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee"),
        name="Библиотека имени 7 Непьющих",
        city="Москва",
        address="2-я Бауманская ул., д.5, стр.1",
    )

    library_query = MagicMock()
    library_query.filter.return_value.first.return_value = library

    books_query = MagicMock()
    books_query.join.return_value = books_query
    books_query.filter.return_value = books_query
    books_query.offset.return_value = books_query
    books_query.limit.return_value = books_query
    books_query.all.return_value = []

    db.query.side_effect = [
        library_query,
        books_query,
    ]

    response = client.get(
        f"/api/v1/libraries/{library.library_uid}/books",
        params={
            "page": 0,
            "size": 10,
            "showAll": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == []
    assert books_query.filter.called


def test_get_books_show_all_true(client, db):
    library = Library(
        id=1,
        library_uid=UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee"),
        name="Библиотека имени 7 Непьющих",
        city="Москва",
        address="2-я Бауманская ул., д.5, стр.1",
    )

    book = Book(
        id=1,
        book_uid=UUID("f7cdc58f-2caf-4b15-9727-f89dcc629b27"),
        name="Краткий курс C++ в 7 томах",
        author="Бьерн Страуструп",
        genre="Научная фантастика",
        condition="EXCELLENT",
    )

    library_query = MagicMock()
    library_query.filter.return_value.first.return_value = library

    books_query = MagicMock()
    books_query.join.return_value = books_query
    books_query.filter.return_value = books_query
    books_query.offset.return_value = books_query
    books_query.limit.return_value = books_query
    books_query.all.return_value = [(book, 0)]

    db.query.side_effect = [
        library_query,
        books_query,
    ]

    response = client.get(
        f"/api/v1/libraries/{library.library_uid}/books",
        params={"page": 0, "size": 10, "showAll": True},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["book_uid"] == str(book.book_uid)
    assert data[0]["availableCount"] == 0
