from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentOwner(BaseModel):
    id: int
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    file_name: str
    file_size: int
    file_type: str
    version: int
    is_deleted: bool
    owner_id: int
    owner: DocumentOwner
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
