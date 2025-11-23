from dataclasses import dataclass
from typing import List




@dataclass
class NoteModel:
    id: int | None
    title: str
    content: str
    created_at: str
    updated_at: str
    tags: List[str] | None = None


    @classmethod
    def create_from_row(cls, row, tags=None):
        return cls(id=row[0], title=row[1], content=row[2], created_at=row[3], updated_at=row[4], tags=tags or [])


    def to_db_tuple(self):
        return (self.title, self.content, self.created_at, self.updated_at)