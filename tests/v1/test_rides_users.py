import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from api.v1.models.users import User
from api.v1.models.rides import Ride, RideType, RideStatus
from api.utils.jwt_handler import create_access_token, hash_password
from unittest.mock import patch
import json

@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    user = User(
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("Password123!"),
        is_active=True,
        is_verified=True,
        phone_number="+1234567890"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_headers(test_user: User):
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_get_user_profile(client: AsyncClient, test_user: User, auth_headers: dict):
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == test_user.email
    assert data["first_name"] == "Test"

@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient, test_user: User, auth_headers: dict, session: AsyncSession):
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    response = await client.put("/api/v1/users/update", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"

@pytest.mark.asyncio
@patch("api.utils.cloudinary_service.cloudinary_service.upload_media")
async def test_upload_avatar(mock_upload, client: AsyncClient, auth_headers: dict):
    mock_upload.return_value = {"url": "https://res.cloudinary.com/demo/image/upload/v1234/test.jpg", "public_id": "test"}
    files = {"file": ("test.jpg", b"dummy image data", "image/jpeg")}
    response = await client.post("/api/v1/users/upload-avatar", files=files, headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
@patch("api.utils.cloudinary_service.cloudinary_service.upload_media")
async def test_create_valid_ride(mock_upload, client: AsyncClient, auth_headers: dict, session: AsyncSession):
    mock_upload.return_value = {"url": "https://res.cloudinary.com/demo/image/upload/v1/car.jpg", "public_id": "car"}
    
    form_data = {
        "ride_type": "sedan",
        "seat_count": "4",
        "door_count": "4",
        "pickup_location": "Airport",
        "adult_passenger_count": "2",
        "children_passenger_count": "1",
        "infant_passenger_count": "0",
        "price": "10000",
        "currency": "NGN",
        "features": json.dumps(["Air Conditioning", "Wi-Fi"])
    }
    files = [("files", ("car.jpg", b"image data", "image/jpeg"))]
    
    response = await client.post("/api/v1/rides", data=form_data, files=files, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["ride_type"] == "sedan"
    assert data["total_passenger_count"] == 3
    assert len(data["media"]) == 1
    assert data["media"][0]["url"] == "https://res.cloudinary.com/demo/image/upload/v1/car.jpg"

@pytest.mark.asyncio
async def test_create_ride_no_photos(client: AsyncClient, auth_headers: dict):
    form_data = {
        "ride_type": "sedan",
        "seat_count": "4",
        "door_count": "4",
        "pickup_location": "Airport",
        "adult_passenger_count": "2",
        "children_passenger_count": "0",
        "infant_passenger_count": "0",
        "price": "10000"
    }
    # No files
    response = await client.post("/api/v1/rides", data=form_data, headers=auth_headers)
    assert response.status_code == 400 # Service throws 400 when images are missing

@pytest.mark.asyncio
async def test_passenger_count_exceeds_seats(client: AsyncClient, auth_headers: dict):
    form_data = {
        "ride_type": "suv",
        "seat_count": "4",
        "door_count": "4",
        "pickup_location": "Downtown",
        "adult_passenger_count": "3",
        "children_passenger_count": "2",
        "infant_passenger_count": "0",
        "price": "10000"
    }
    files = [("files", ("car.jpg", b"image data", "image/jpeg"))]
    
    response = await client.post("/api/v1/rides", data=form_data, files=files, headers=auth_headers)
    assert response.status_code == 422
    assert "exceed seat count" in response.json()["message"] or "exceed seat count" in response.text

@pytest.mark.asyncio
async def test_invalid_price(client: AsyncClient, auth_headers: dict):
    form_data = {
        "ride_type": "suv",
        "seat_count": "4",
        "door_count": "4",
        "pickup_location": "Downtown",
        "adult_passenger_count": "1",
        "children_passenger_count": "0",
        "infant_passenger_count": "0",
        "price": "-500"
    }
    files = [("files", ("car.jpg", b"image data", "image/jpeg"))]
    
    response = await client.post("/api/v1/rides", data=form_data, files=files, headers=auth_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
@patch("api.utils.cloudinary_service.cloudinary_service.upload_media")
async def test_create_duplicate_ride(mock_upload, client: AsyncClient, auth_headers: dict, test_user: User, session: AsyncSession):
    mock_upload.return_value = {"url": "https://res.cloudinary.com/demo/image/upload/v1/car.jpg", "public_id": "car"}
    
    form_data = {
        "ride_type": "van",
        "seat_count": "7",
        "door_count": "5",
        "pickup_location": "Hotel",
        "adult_passenger_count": "4",
        "children_passenger_count": "0",
        "infant_passenger_count": "0",
        "price": "20000"
    }
    files = [("files", ("car.jpg", b"image data", "image/jpeg"))]
    
    res1 = await client.post("/api/v1/rides", data=form_data, files=files, headers=auth_headers)
    assert res1.status_code == 201
    
    # Try creating again
    files2 = [("files", ("car.jpg", b"image data", "image/jpeg"))]
    res2 = await client.post("/api/v1/rides", data=form_data, files=files2, headers=auth_headers)
    assert res2.status_code == 409
    assert "already listed" in res2.text

@pytest.mark.asyncio
async def test_upload_too_many_photos(client: AsyncClient, auth_headers: dict):
    form_data = {
        "ride_type": "sedan",
        "seat_count": "4",
        "door_count": "4",
        "pickup_location": "Airport",
        "adult_passenger_count": "2",
        "children_passenger_count": "0",
        "infant_passenger_count": "0",
        "price": "10000"
    }
    files = [("files", (f"car{i}.jpg", b"image data", "image/jpeg")) for i in range(6)]
    
    response = await client.post("/api/v1/rides", data=form_data, files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "Maximum of 5 photos allowed" in response.text

@pytest.mark.asyncio
async def test_upload_invalid_media_format(client: AsyncClient, auth_headers: dict):
    form_data = {
        "ride_type": "sedan",
        "seat_count": "4",
        "door_count": "4",
        "pickup_location": "Airport",
        "adult_passenger_count": "2",
        "children_passenger_count": "0",
        "infant_passenger_count": "0",
        "price": "10000"
    }
    files = [("files", ("document.pdf", b"pdf data", "application/pdf"))]
    
    response = await client.post("/api/v1/rides", data=form_data, files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid file format" in response.text
