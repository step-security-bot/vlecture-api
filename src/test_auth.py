from fastapi.testclient import TestClient

from src.main import app
from src.utils.db import get_db


def override_get_db(test_db_session):
    try:
        yield test_db_session
    finally:
        test_db_session.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

## Authentication Tests ##

# Positive Cases


def test_register_positive(test_db_session):
    response = client.post(
        "/register",
        json={
            "email": "positive@example.com",
            "first_name": "Positive",
            "middle_name": "Test",
            "last_name": "Case",
            "password": "positivepassword",
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "positive@example.com"


def test_login_positive(test_db_session):
    # Assuming a user "positive@example.com" already exists from the register test
    response = client.post(
        "/login", json={"email": "positive@example.com", "password": "positivepassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


# Negative Cases


def test_register_missing_fields(test_db_session):
    response = client.post(
        "/register",
        json={
            # Omitting required fields like 'email', 'first_name', etc.
        },
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_register_user_already_exists(test_db_session):
    # Assuming a user "positive@example.com" already exists from the register test
    response = client.post(
        "/register",
        json={
            "email": "positive@example.com",
            "first_name": "Positive",
            "middle_name": "Test",
            "last_name": "Case",
            "password": "positivepassword",
        },
    )
    assert response.status_code == 409


def test_register_with_invalid_email(test_db_session):
    response = client.post(
        "/register",
        json={
            "email": "notanemail",
            "first_name": "Invalid",
            "middle_name": "Test",
            "last_name": "Email",
            "password": "invalidemail",
        },
    )
    assert response.status_code == 422  # Invalid email format


def test_register_with_special_characters_in_name(test_db_session):
    response = client.post(
        "/register",
        json={
            "email": "specialchar@example.com",
            "first_name": "Speci@l",
            "middle_name": "@wesome",
            "last_name": "Ch@r",
            "password": "specialpassword",
        },
    )
    assert response.status_code == 200


def test_register_identical_emails_with_different_cases(test_db_session):
    # Testing case sensitivity in email uniqueness
    response1 = client.post(
        "/register",
        json={
            "email": "CaseSensitiveEmail@example.com",
            "first_name": "Case",
            "middle_name": "Character",
            "last_name": "Sensitive",
            "password": "casesensitive",
        },
    )
    response2 = client.post(
        "/register",
        json={
            "email": "casesensitiveemail@example.com",  # Same email in different case
            "first_name": "Case",
            "middle_name": "Character",
            "last_name": "Insensitive",
            "password": "caseinsensitive",
        },
    )
    assert response1.status_code == 200
    assert response2.status_code == 400


def test_login_user_not_found(test_db_session):
    response = client.post(
        "/login", json={"email": "nonexistent@example.com", "password": "any"}
    )
    assert response.status_code == 404  # Not Found


def test_login_wrong_password(test_db_session):
    # Assuming a user "positive@example.com" already exists from the register test
    response = client.post(
        "/login", json={"email": "positive@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401  # Unauthorized


def test_register_with_long_values(test_db_session):
    long_string = "a" * 256  # Testing with exceeding the maximum length of 255
    response = client.post(
        "/register",
        json={
            "email": f"{long_string}@example.com",
            "first_name": long_string,
            "middle_name": long_string,
            "last_name": long_string,
            "password": long_string,
        },
    )
    assert response.status_code == 422  # Data too long for one or more fields


# Edge Cases


def test_register_edge_case_email_formats(test_db_session):
    # Testing with unusual but technically valid email formats
    emails = [
        "email@[123.123.123.123]",
        '"email"@example.com',
        "user.name+tag+sorting@example.com",
    ]
    for email in emails:
        response = client.post(
            "/register",
            json={
                "email": email,
                "first_name": "Edge",
                "middle_name": "Test",
                "last_name": "Case",
                "password": "edgecasepassword",
            },
        )
        assert response.status_code == 200


def test_login_edge_case_sensitive_email(test_db_session):
    # Assuming emails are case-insensitive
    response = client.post(
        "/login",
        json={"email": "TESTlogin@example.com", "password": "loginpassword123"},
    )
    assert response.status_code == 200


def test_register_edge_case_boundary_values(test_db_session):
    # Testing boundary values for fields like 'first_name' and 'last_name'
    response = client.post(
        "/register",
        json={
            "email": "boundary@example.com",
            "first_name": "",  # Empty string
            "middle_name": "Boundary Test Case",
            "last_name": "B" * 255,  # Testing the max length
            "password": "boundarypassword",
        },
    )
    assert (
        response.status_code == 422
    )  # Assuming empty 'first_name' is invalid and 'last_name' length is validated
