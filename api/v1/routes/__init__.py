from fastapi import APIRouter
from api.v1.routes.auth_route import auth
from api.v1.routes.booking_route import booking
from api.v1.routes.review_route import review
from api.v1.routes.car_rental_route import car_rental
from api.v1.routes.favorite_route import favorites
from api.v1.routes.payment_route import payment
from api.v1.routes.payment_method_route import payment_method

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(booking)
api_version_one.include_router(review)
api_version_one.include_router(car_rental)
api_version_one.include_router(favorites)
api_version_one.include_router(payment)
api_version_one.include_router(payment_method)