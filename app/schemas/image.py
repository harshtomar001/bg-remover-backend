from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ImageResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    status: str
    model_used: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageHistoryResponse(BaseModel):
    items: list[ImageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int