from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.core.security import get_current_user
from app.crud.document import (
    create_document,
    create_new_version,
    get_all_documents,
    get_document,
    get_document_versions,
    soft_delete_document,
    update_document,
)
from app.database.database import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentUpdate
from app.services.storage import compute_checksum, resolve_safe_path, save_file, validate_file

api_router = APIRouter()

# ── Auth & Users ──────────────────────────────────────────────────────────────
api_router.include_router(auth_router)
api_router.include_router(users_router)

# ── Documents ─────────────────────────────────────────────────────────────────
documents_router = APIRouter(prefix="/documents", tags=["Documents"])


def _get_doc_or_404(document_id: int, db: Session):
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def _require_owner_or_admin(document_id: int, db: Session, current_user: User):
    doc = _get_doc_or_404(document_id, db)
    if doc.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return doc


@documents_router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    validate_file(file, content)  # checks MIME type + extension + size
    checksum = compute_checksum(content)
    stored_file_name, file_path = save_file(file, content)  # UUID filename, path-traversal safe

    return create_document(
        db,
        title=title,
        description=description,
        category=category,
        file_name=file.filename,
        stored_file_name=stored_file_name,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        checksum=checksum,
        owner_id=current_user.id,
    )


@documents_router.get("/", response_model=List[DocumentResponse])
def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_documents(db, page=page, limit=limit, category=category, owner_id=owner_id, search=search)


@documents_router.get("/{document_id}", response_model=DocumentResponse)
def get_document_metadata(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_doc_or_404(document_id, db)


@documents_router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_doc_or_404(document_id, db)
    safe_path = resolve_safe_path(doc.file_path)  # prevents path traversal on stored path
    if not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    return FileResponse(path=str(safe_path), filename=doc.file_name, media_type=doc.file_type)


@documents_router.put("/{document_id}", response_model=DocumentResponse)
def update_document_metadata(
    document_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _require_owner_or_admin(document_id, db, current_user)
    return update_document(db, doc, data)


@documents_router.delete("/{document_id}", response_model=DocumentResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _require_owner_or_admin(document_id, db, current_user)
    return soft_delete_document(db, doc)


@documents_router.post("/{document_id}/version", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_new_version(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _require_owner_or_admin(document_id, db, current_user)
    content = await file.read()
    validate_file(file, content)
    checksum = compute_checksum(content)
    stored_file_name, file_path = save_file(file, content)

    return create_new_version(
        db, doc,
        file_name=file.filename,
        stored_file_name=stored_file_name,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        checksum=checksum,
    )


@documents_router.get("/{document_id}/versions", response_model=List[DocumentResponse])
def list_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_doc_or_404(document_id, db)
    return get_document_versions(db, title=doc.title, owner_id=doc.owner_id)


api_router.include_router(documents_router)
