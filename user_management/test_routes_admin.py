import pytest
from fastapi.testclient import TestClient

from user_management.dao import UsersDAO


from .test_routes import client


@pytest.fixture
def setup_users():
    with UsersDAO() as users_dao:
        # Create an admin user
        admin_user_id = users_dao.add_user(
            "adminuser", "password", "admintoken", "Admin User"
        )
        users_dao.update_user(admin_user_id, True, "admin")

        # Create a regular user
        regular_user_id = users_dao.add_user(
            "regularuser", "password", "regulartoken", "Regular User"
        )
        users_dao.update_user(regular_user_id, True, "user")

        # Create a target user whose details will be updated
        target_user_id = users_dao.add_user(
            "targetuser", "password", "targettoken", "Target User"
        )

        return admin_user_id, regular_user_id, target_user_id


def test_update_user_by_admin_success(client: TestClient, setup_users):
    admin_user_id, _, target_user_id = setup_users

    # Assuming the admin is logged in and their session is valid
    client.cookies.set("session_token", "admintoken")
    client.cookies.set("username", "adminuser")

    response = client.post(
        f"/admin/update_user/{target_user_id}",
        data={"has_access": "false", "role": "userx"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"User {target_user_id} updated successfully"}
    with UsersDAO() as users_dao:
        target_username = users_dao.get_username(target_user_id)
        target_user = users_dao.get_user(target_username)
        assert not target_user.has_access
        assert target_user.role == "userx"


def test_update_user_by_non_admin_failure(client: TestClient, setup_users):
    _, regular_user_id, target_user_id = setup_users

    client.cookies.set("session_token", "regulartoken")
    client.cookies.set("username", "regularuser")

    response = client.post(
        f"/admin/update_user/{target_user_id}",
        data={"has_access": "true", "role": "user"},
    )

    assert response.status_code == 403
    assert (
        "Not authorized for /admin/update_user/{user_id} with role 'user'"
        in response.json().get("detail", "")
    )


def test_update_user_no_login(client: TestClient, setup_users):
    _, _, target_user_id = setup_users

    response = client.post(
        f"/admin/update_user/{target_user_id}",
        data={"has_access": "true", "role": "user"},
    )

    assert response.status_code == 401
    assert "Not authenticated for /admin/update_user/{user_id}" in response.json().get(
        "detail", ""
    )
