from fastapi import APIRouter, Depends, UploadFile, File

from fastapi_limiter.depends import RateLimiter

from sqlalchemy.ext.asyncio import AsyncSession

import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.entity.models import User
from src.repository import users as repositories_users
from src.schemas.user import UserResponseSchema
from src.services.auth import auth_serviсe
from src.conf.config import settings
from src.schemas.user import UserDb


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponseSchema,
    description="No more than 2 requests per 10 seconds",
    dependencies=[Depends(RateLimiter(times=2, seconds=10))],
)
async def get_current_user(user: User = Depends(auth_serviсe.get_current_user)):
    """
    Retrieves the current authenticated user's information.

    Parameters:
    - user (User): The authenticated user object obtained from the auth_service.

    Returns:
    - UserResponseSchema: The current authenticated user's information in the specified response model format.

    This endpoint is protected by a rate limiter that allows no more than 2 requests per 10 seconds.
    """
    return user


@router.patch("/avatar", response_model=UserDb)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(auth_serviсe.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the avatar of the current authenticated user.

    Parameters:
    - file (UploadFile): The file to be uploaded as the new avatar.
    - current_user (User): The authenticated user object obtained from the auth_service.
    - db (AsyncSession): The database session to be used for the operation.

    Returns:
    - UserDb: The updated user object with the new avatar URL.

    This method uses Cloudinary to upload the new avatar file and update the user's avatar URL in the database.
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    cloudinary.uploader.upload(
        file.file, public_id=f"ContactsApp/{current_user.username}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(
        f"ContactsApp/{current_user.username}"
    ).build_url(width=250, height=250, crop="fill")
    user = await repositories_users.update_avatar(current_user.email, src_url, db)
    return user
