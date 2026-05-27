import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.utils.jwt_handler import create_access_token, hash_password
from api.v1.models.property import Property
from api.v1.models.users import User


def _property_payload(name: str, location: str, extra: Optional[dict] = None) -> dict:
    payload = {
        "name": name,
        "type": "studio",
        "location": location,
        "description": "Clean and quiet space",
        "beds": 2,
        "baths": 2,
        "guests": {"adults": 2, "children": 1},
        "price": 120000.0,
        "photos": ["https://example.com/p1.jpg"],
        "amenities": ["wifi", "pool"],
        "payout_account": "0123456789",
        "payout_bank": "Demo Bank",
        "payout_name": "Host User",
    }
    if extra:
        payload.update(extra)
    return payload


async def _create_user(
    session: AsyncSession,
    *,
    email: str,
    role: str,
    vendor_verified: bool = False,
) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        username=email.split("@")[0],
        hashed_password=hash_password("Password123!"),
        is_active=True,
        is_verified=True,
        role=role,
        vendor_verified=vendor_verified,
        phone_number="+1234567890",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def _auth_headers(user_id: str) -> dict:
    token = create_access_token(data={"sub": user_id})
    return {"Authorization": f"Bearer {token}"}


async def _insert_property(
    session: AsyncSession,
    *,
    owner_id: str,
    name: str,
    location: str,
    status: str,
) -> Property:
    prop = Property(
        user_id=owner_id,
        name=name,
        type="studio",
        location=location,
        description="desc",
        beds=1,
        baths=1,
        guests={"adults": 1},
        price=1000.0,
        photos=["https://example.com/a.jpg"],
        amenities=["wifi"],
        payout_account="0123456789",
        payout_bank="Demo Bank",
        payout_name="Host User",
        status=status,
    )
    session.add(prop)
    await session.commit()
    await session.refresh(prop)
    return prop


@pytest_asyncio.fixture
async def vendor_user(session: AsyncSession) -> User:
    return await _create_user(
        session, email="vendor@example.com", role="vendor", vendor_verified=True
    )


@pytest_asyncio.fixture
async def superadmin_user(session: AsyncSession) -> User:
    return await _create_user(
        session, email="superadmin@example.com", role="superadmin", vendor_verified=False
    )


@pytest.mark.asyncio
async def test_property_create_defaults_to_pending_approval(
    client: AsyncClient,
    vendor_user: User,
):
    payload = _property_payload(
        name="Pending Villa",
        location="Ikeja, Lagos",
        extra={"status": "active"},
    )
    response = await client.post(
        "/api/v1/properties",
        json=payload,
        headers=_auth_headers(vendor_user.id),
    )

    assert response.status_code == 201
    listing = response.json()["data"]
    assert listing["status"] == "pending_approval"
    assert listing["admin_notes"] is None


@pytest.mark.asyncio
async def test_public_properties_exclude_non_active_statuses(
    client: AsyncClient,
    session: AsyncSession,
    vendor_user: User,
):
    active = await _insert_property(
        session,
        owner_id=vendor_user.id,
        name="Active Home",
        location="Lekki, Lagos",
        status="active",
    )
    await _insert_property(
        session,
        owner_id=vendor_user.id,
        name="Pending Home",
        location="Yaba, Lagos",
        status="pending_approval",
    )
    await _insert_property(
        session,
        owner_id=vendor_user.id,
        name="Rejected Home",
        location="Ajah, Lagos",
        status="rejected",
    )
    await _insert_property(
        session,
        owner_id=vendor_user.id,
        name="Suspended Home",
        location="Ikoyi, Lagos",
        status="suspended",
    )

    response = await client.get("/api/v1/properties/public")

    assert response.status_code == 200
    properties = response.json()["data"]["properties"]
    assert len(properties) == 1
    assert properties[0]["id"] == active.id
    assert properties[0]["status"] == "active"


@pytest.mark.asyncio
async def test_admin_approve_makes_property_public(
    client: AsyncClient,
    vendor_user: User,
    superadmin_user: User,
):
    create_response = await client.post(
        "/api/v1/properties",
        json=_property_payload(name="Approval Test Home", location="Asokoro, Abuja"),
        headers=_auth_headers(vendor_user.id),
    )
    assert create_response.status_code == 201
    property_id = create_response.json()["data"]["id"]

    approve_response = await client.patch(
        f"/api/v1/admin/listings/properties/{property_id}/status",
        json={"status": "active", "admin_notes": "Looks good"},
        headers=_auth_headers(superadmin_user.id),
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["status"] == "active"
    assert approve_response.json()["data"]["admin_notes"] == "Looks good"

    public_response = await client.get("/api/v1/properties/public")
    assert public_response.status_code == 200
    public_ids = {item["id"] for item in public_response.json()["data"]["properties"]}
    assert property_id in public_ids


@pytest.mark.asyncio
async def test_admin_decline_keeps_property_hidden(
    client: AsyncClient,
    vendor_user: User,
    superadmin_user: User,
):
    create_response = await client.post(
        "/api/v1/properties",
        json=_property_payload(name="Decline Test Home", location="Gwarinpa, Abuja"),
        headers=_auth_headers(vendor_user.id),
    )
    assert create_response.status_code == 201
    property_id = create_response.json()["data"]["id"]

    reject_response = await client.patch(
        f"/api/v1/admin/listings/properties/{property_id}/status",
        json={"status": "rejected", "admin_notes": "Incomplete information"},
        headers=_auth_headers(superadmin_user.id),
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["data"]["status"] == "rejected"
    assert reject_response.json()["data"]["admin_notes"] == "Incomplete information"

    public_response = await client.get("/api/v1/properties/public")
    assert public_response.status_code == 200
    public_ids = {item["id"] for item in public_response.json()["data"]["properties"]}
    assert property_id not in public_ids

    vendor_response = await client.get(
        "/api/v1/properties", headers=_auth_headers(vendor_user.id)
    )
    assert vendor_response.status_code == 200
    vendor_properties = vendor_response.json()["data"]["properties"]
    declined = next((item for item in vendor_properties if item["id"] == property_id), None)
    assert declined is not None
    assert declined["status"] == "rejected"
    assert declined["admin_notes"] == "Incomplete information"


@pytest.mark.asyncio
async def test_property_status_persists_in_database_after_admin_update(
    client: AsyncClient,
    vendor_user: User,
    superadmin_user: User,
    session: AsyncSession,
):
    create_response = await client.post(
        "/api/v1/properties",
        json=_property_payload(name="Persist Test Home", location="Maitama, Abuja"),
        headers=_auth_headers(vendor_user.id),
    )
    assert create_response.status_code == 201
    property_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/admin/listings/properties/{property_id}/status",
        json={"status": "active", "admin_notes": "Approved and live"},
        headers=_auth_headers(superadmin_user.id),
    )
    assert update_response.status_code == 200

    db_property = (
        await session.execute(select(Property).filter(Property.id == property_id))
    ).scalars().first()
    assert db_property is not None
    assert db_property.status == "active"
    assert db_property.admin_notes == "Approved and live"
