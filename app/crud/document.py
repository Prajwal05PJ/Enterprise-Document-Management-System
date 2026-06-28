from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentUpdate


def create_document(db: Session, *, title: str, description: Optional[str], category: Optional[str],
                    file_name: str, stored_file_name: str, file_path: str,
                    file_size: int, file_type: str, checksum: str, owner_id: int) -> Document:
    doc = Document(
        title=title,
        description=description,
        category=category,
        file_name=file_name,
        stored_file_name=stored_file_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        checksum=checksum,
        owner_id=owner_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()


def get_all_documents(db: Session, *, page: int, limit: int,
                      category: Optional[str], owner_id: Optional[int],
                      search: Optional[str]) -> List[Document]:
    query = db.query(Document).filter(Document.is_deleted == False)

    if category:
        query = query.filter(Document.category == category)
    if owner_id:
        query = query.filter(Document.owner_id == owner_id)
    if search:
        query = query.filter(
            Document.title.ilike(f"%{search}%") |
            Document.description.ilike(f"%{search}%") |
            Document.file_name.ilike(f"%{search}%")
        )

    return query.offset((page - 1) * limit).limit(limit).all()


def update_document(db: Session, document: Document, data: DocumentUpdate) -> Document:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(document, field, value)
    db.commit()
    db.refresh(document)
    return document


def soft_delete_document(db: Session, document: Document) -> Document:
    document.is_deleted = True
    db.commit()
    db.refresh(document)
    return document


def create_new_version(db: Session, original: Document, *, file_name: str, stored_file_name: str,
                       file_path: str, file_size: int, file_type: str, checksum: str) -> Document:
    new_version = Document(
        title=original.title,
        description=original.description,
        category=original.category,
        file_name=file_name,
        stored_file_name=stored_file_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        checksum=checksum,
        version=original.version + 1,
        owner_id=original.owner_id,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


def get_document_versions(db: Session, title: str, owner_id: int) -> List[Document]:
    return (
        db.query(Document)
        .filter(Document.title == title, Document.owner_id == owner_id)
        .order_by(Document.version)
        .all()
    )
