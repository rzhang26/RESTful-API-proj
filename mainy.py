'''
imports orm, api framework, type hinting, generic, encode/decode, validation

response validation & db models Campaign, CampaignCreate, PaginatedResponse

connection to db
helper methods for starting/closing session

sessionDep management for webapp instance

webapp instance

generic typing

encode/decode cursor methods

HTTP methods
'''

import base64
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from annotated_types import T
from typing import Annotated, Generic, TypeVar, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlmodel import Field, SQLModel, Session, create_engine, select
from pydantic import BaseModel


class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True, nullable=True)

class CampaignCreated(SQLModel):
    name: str 
    due_date: datetime | None = None
    
#learn deeper
sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
connect_args = {'check_same_thread': True}

engine = create_engine(sqlite_url, connect_args=connect_args)

def create_table_and_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield(session)        
#learn deeper

#learn deeper
SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table_and_db()
    with Session(engine) as session:
        if not session.exec(select(Campaign)).first():
            session.add([
                Campaign(name='Summer Sale', due_date=datetime.now(timezone.utc)),
                Campaign(name='Winter Break', due_date=datetime.now(timezone.utc))
            ])
            session.commit()    
    yield
#learn deeper


app = FastAPI(root_path='/api/v1', lifespan=lifespan)

T = TypeVar('T')
class PaginatedResponse(BaseModel, Generic[T]):
    data: T
    next_url: Optional[str]
    prev_url: Optional[str]

class Response(BaseModel, Generic[T]):
    data: T

def encode_cursor(value) -> str:
    raw = json.dumps({'id': value})
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor) -> int:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    payload = json.loads(raw)
    return payload.get('id')


#understand deeper
@app.get('/campaigns', response_model=PaginatedResponse[list[Campaign]])
async def get_campaigns(request: Request, session: SessionDep, cursor: Optional[str] = Query(None), limit: Optional[int] = Query(10, ge=0)):
    cursor_id = 0
    if cursor:
        cursor_id = decode_cursor(cursor)

    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).where(Campaign.campaign_id > cursor_id).limit(limit + 1)).all()
    base_url = str(request.url).split('?')[0]

    next_url = None
    if len(data) > cursor_id:
        next_cursor = encode_cursor(data[:limit][-1].campaign_id)
        next_url = f'{base_url}?cursor={next_cursor}&limit={limit}'

    comparison = encode_cursor(max(0, cursor_id - limit))
    prev_url = f'{base_url}?cursor={comparison}&limit={limit}'

    return {
        'data': data,
        'next_url': next_url,
        'prev_url': prev_url
    }

@app.get('/campaigns/{id}', response_model=Response[Optional[Campaign]])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    return {'data': data}

@app.post('/campaigns', response_model=Response[Campaign])
async def post_campaign(campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)

    return {'data': campaign}

@app.put('/campaigns/{id}', response_model=Response[Campaign])
async def update_campaign(id: int, campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)

    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    data.name = db_campaign.name
    data.due_date = db_campaign.due_date
    session.add(data)
    session.commit()
    session.refresh(db_campaign)

    return {'data': data}

@app.delete('/campaigns/{id}', response_model=Response[Campaign])
async def delete_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    session.delete(data)
    session.commit()
    