"""Tests for /csrf and /me."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.chat.models import Conversation
from apps.geo.models import District
from conftest import make_user

pytestmark = pytest.mark.django_db


def test_csrf_sets_cookie(api: APIClient) -> None:
    """GET /csrf returns 204 and sets csrftoken."""
    response = api.get("/api/v1/csrf")
    assert response.status_code == 204
    assert "csrftoken" in response.cookies


def test_me_requires_login(api: APIClient) -> None:
    """Anonymous: 401 not_authenticated problem."""
    response = api.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_me_shape(auth_api: APIClient, user: User, district: District) -> None:
    """GET /me matches the contract's Me object."""
    body = auth_api.get("/api/v1/me?lang=ru").json()
    assert body == {
        "id": str(user.id),
        "email": "user@example.com",
        "email_verified": True,
        "has_password": True,
        "display_name": None,
        "ui_language": "uz-Latn",
        "region": {"id": district.region_id, "name": "Тестовая область"},
        "district": {"id": district.id, "name": "Тестовый район"},
        "profile_complete": True,
        "quota": {"hour_limit": 20, "hour_used": 0, "day_limit": 100, "day_used": 0},
    }


def test_unverified_user_flag(api: APIClient) -> None:
    """An unverified email shows ``email_verified: false``."""
    api.force_authenticate(make_user("u2@example.com", verified=False))
    assert api.get("/api/v1/me").json()["email_verified"] is False


def test_patch_language_and_name(auth_api: APIClient) -> None:
    """Language and display name update; blank name becomes null."""
    body = auth_api.patch("/api/v1/me", {"ui_language": "en", "display_name": "Ali"}).json()
    assert (body["ui_language"], body["display_name"]) == ("en", "Ali")
    assert auth_api.patch("/api/v1/me", {"display_name": ""}).json()["display_name"] is None


def test_patch_rejects_district_outside_region(
    auth_api: APIClient, district: District, other_district: District
) -> None:
    """district_id must belong to region_id."""
    response = auth_api.patch(
        "/api/v1/me", {"region_id": district.region_id, "district_id": other_district.id}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "district_id" in response.json()["errors"]


def test_patch_rejects_district_outside_current_region(
    auth_api: APIClient, other_district: District
) -> None:
    """Without region_id, the district must match the current region."""
    response = auth_api.patch("/api/v1/me", {"district_id": other_district.id})
    assert response.status_code == 400


def test_patch_region_without_district_is_rejected(
    auth_api: APIClient, other_district: District
) -> None:
    """Changing only the region would leave a district from another region: 400."""
    response = auth_api.patch("/api/v1/me", {"region_id": other_district.region_id})
    assert response.status_code == 400
    assert "district_id" in response.json()["errors"]


def test_patch_same_region_without_district_is_fine(auth_api: APIClient, user: User) -> None:
    """Re-sending the current region alone is accepted."""
    assert auth_api.patch("/api/v1/me", {"region_id": user.region_id}).status_code == 200


def test_patch_region_and_district_together(auth_api: APIClient, other_district: District) -> None:
    """Moving to another region works when the district comes along."""
    body = {"region_id": other_district.region_id, "district_id": other_district.id}
    assert auth_api.patch("/api/v1/me", body).json()["district"]["id"] == other_district.id


def test_patch_unknown_ids(auth_api: APIClient) -> None:
    """Unknown SOATO ids are validation errors."""
    response = auth_api.patch("/api/v1/me", {"region_id": 1, "district_id": 2})
    assert response.status_code == 400
    assert set(response.json()["errors"]) == {"region_id", "district_id"}


def test_delete_requires_confirm(auth_api: APIClient) -> None:
    """DELETE /me without confirm=true is refused."""
    response = auth_api.delete("/api/v1/me", {"confirm": False}, format="json")
    assert response.status_code == 400


def test_delete_removes_account_and_conversations(auth_api: APIClient, user: User) -> None:
    """DELETE /me with confirm deletes the user and their conversations."""
    Conversation.objects.create(user=user, title="x")
    response = auth_api.delete("/api/v1/me", {"confirm": True}, format="json")
    assert response.status_code == 204
    assert not User.objects.filter(id=user.id).exists()
    assert not Conversation.objects.exists()


def test_create_user_requires_email() -> None:
    """The manager refuses an empty email."""
    with pytest.raises(ValueError, match="Email"):
        User.objects.create_user("")


def test_create_superuser() -> None:
    """Superusers are staff."""
    admin = User.objects.create_superuser("root@example.com", "pw-12345678")
    assert admin.is_staff
    assert admin.is_superuser
    assert str(admin) == "root@example.com"


def test_google_only_user_has_no_password(api: APIClient) -> None:
    """An account without a usable password reports ``has_password: false``."""
    social = make_user("g@example.com")
    social.set_unusable_password()
    social.save()
    api.force_authenticate(social)
    assert api.get("/api/v1/me").json()["has_password"] is False
