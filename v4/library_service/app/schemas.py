from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LibraryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    library_uid: UUID = Field(alias="libraryUid")
    name: str
    city: str
    address: str

class BookResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    book_uid: UUID = Field(alias="bookUid")
    name: str
    author: str | None
    genre: str | None
    condition: str
    availableCount: int = Field(alias="availableCount")

class BooksResponse(BaseModel):
    items: list[BookResponse]