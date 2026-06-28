import hashlib
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status

STORAGE_DIR = Path("storage/uploads/documents").resolve()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "image/png",
    "image/jpeg",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".png", ".jpg", ".jpeg"}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def validate_file(file: UploadFile, content: bytes) -> None:
    extension = Path(file.filename).suffix.lower()
    if file.content_type not in ALLOWED_MIME_TYPES or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' or extension '{extension}' is not allowed.",
        )
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 20 MB limit.",
        )


def compute_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def save_file(file: UploadFile, content: bytes) -> Tuple[str, str]:
    """Save file to disk. Returns (stored_file_name, file_path)."""
    extension = Path(file.filename).suffix.lower()
    stored_file_name = f"{uuid.uuid4().hex}{extension}"
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = STORAGE_DIR / stored_file_name
    # Prevent path traversal — ensure resolved path stays inside STORAGE_DIR
    if not str(file_path.resolve()).startswith(str(STORAGE_DIR)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    file_path.write_bytes(content)
    return stored_file_name, str(file_path)


def resolve_safe_path(file_path: str) -> Path:
    """Resolve a stored file path and verify it is inside STORAGE_DIR."""
    resolved = Path(file_path).resolve()
    if not str(resolved).startswith(str(STORAGE_DIR)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
    return resolved


def delete_file(file_path: str) -> None:
    path = resolve_safe_path(file_path)
    if path.exists():
        path.unlink()
