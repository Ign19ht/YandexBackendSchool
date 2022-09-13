from enum import Enum
from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime


class SystemItemType(str, Enum):
    FILE = "FILE"
    FOLDER = "FOLDER"


class SystemItem(BaseModel):
    id: str
    url: Optional[str] = None
    date: datetime
    parentId: Optional[str] = None
    type: SystemItemType
    size: Optional[int] = None
    children: Optional[List] = None


class SystemItemImport(BaseModel):
    id: str
    url: Optional[str] = None
    parentId: Optional[str] = None
    type: SystemItemType
    size: Optional[int] = None


class SystemItemImportRequest(BaseModel):
    items: Optional[List[SystemItemImport]]
    updateDate: datetime


class SystemItemHistoryUnit(BaseModel):
    id: str
    url: Optional[str] = None
    date: datetime
    parentId: Optional[str] = None
    type: SystemItemType
    size: Optional[int] = None


class SystemItemHistoryResponse(BaseModel):
    items: Optional[List[SystemItemHistoryUnit]]


class Error(BaseModel):
    code: int
    message: str
