from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Generic


EASTERN_TZ = ZoneInfo('America/New_York')

class Campaign(SQLModel, table=True): #row in db
    __table_name__ = 'campaign'
    campaign_id: int | None = Field(default=None, primary_key=True, nullable=False) #each field attr is a col in db
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(EASTERN_TZ))

class CampaignCreated(BaseModel):
    name: str
    due_date: datetime | None 

# T = TypeVar('T')
# class Response(BaseModel,Generic[T]): #could also technically pass in 'SQLModel' but BaseModel is purely for validation purposes
class Response[T](BaseModel):
    data: T

class PaginatedResponse[T](BaseModel): 
    data: T
    prev_url: Optional[str]
    next_url: Optional[str]