import os
import uuid
import shutil
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings

# Allowed MIME types and extensions
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def is_cloudinary_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME and
        settings.CLOUDINARY_API_KEY and
        settings.CLOUDINARY_API_SECRET
    )


async def upload_image(file: UploadFile) -> str:
    """
    Validate and upload an image.
    Uses Cloudinary if configured; otherwise safely saves to static uploads folder.
    Returns the public image URL.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type '{file.content_type}'. Supported: JPEG, PNG, WebP, GIF."
        )

    # Read file content and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit."
        )

    if is_cloudinary_configured():
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        try:
            result = cloudinary.uploader.upload(
                contents,
                folder="borrowhub/items",
                resource_type="image",
            )
            return result.get("secure_url", result.get("url"))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cloudinary upload failed: {str(e)}"
            )
    else:
        # Local upload storage fallback
        static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "static", "uploads"
        )
        os.makedirs(static_dir, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[1].lower()
        if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            ext = ".jpg" if file.content_type == "image/jpeg" else ".png"

        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(static_dir, unique_name)

        with open(target_path, "wb") as f:
            f.write(contents)

        return f"/uploads/{unique_name}"
