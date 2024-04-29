from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class FileInfo(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None

class CommitData(BaseModel):
    author: str
    message: str
    date: str
    url: str
    commit_id: str
    files: List[FileInfo]
