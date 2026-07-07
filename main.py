'''
Simple Proj Outline: RESTFul API for Campaign CRUDing

main imports:
- SQLModel for ORM 
- FastAPI for web app deployment
- Pydantic for I/O (mostly input) validation (BaseModel)
- Typing & annotated_types for type hinting

output response formatting models + connection to db
- Campaign
- CampaignCreated
- Special Cases requiring generic type T
    - Response
    - RaginatedResponse --> try w/ out [Optional[Campaign]] when passed in decorators as params

db 'routing' and config
- sqlite db 
- SQLModel for ORM 
- create_db_and_table() for db initialization

session dependency & logic
- SessionDep 
- get_session(知我)
- async decorator for lifetime()

webapp instance initialization (FastAPI)
- app = FastAPI(root_path, lifespan)

cursor encode/decede methods using base64 

CRUD implementations
'''

import json
import base64

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Generic, Optional, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, create_engine, select


class Campaign(SQLModel, table=True): #row in db
    campaign_id: int | None = Field(default=None, primary_key=True) #each field attr is a col in db
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CampaignCreated(SQLModel):
    name: str
    due_date: datetime | None

# T = TypeVar('T') #1st look -> 20 push-ups
# class Response(BaseModel,Generic[T]): #could also technically pass in 'SQLModel' but BaseModel is purely for validation purposes
class Response[T](BaseModel):
    data: T

class PaginatedResponse[T](BaseModel):
    data: T
    next_url: Optional[str]
    prev_url: Optional[str]


sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(url=sqlite_url, echo=True, connect_args={'check_same_thread': False})

def create_db_and_table(): #2nd look -> +20 push-ups
    SQLModel.metadata.create_all(engine) #builds the db table in 'database.db'

def get_session():
    with Session(engine) as session:
        yield(session)

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    with Session(engine) as session:
        first_data = session.exec(select(Campaign)).first() #3rd look -> +20 push-ups
        if not first_data:
            session.add([
                Campaign(name='Summer Sale', due_date=datetime.now(timezone.utc)), # 4th look -> +20 push-ups
                Campaign(name='Summer Stale', due_date=datetime.now(timezone.utc))
            ])
            session.commit()
    yield


app = FastAPI(root_path='/apis/v1', lifespan=lifespan)


def encode_cursor(value: Optional[int]) -> str:#5th look -> +10 push-ups
    raw = json.dumps({'id': value}) #dumping the key-val pair {'id': value} into a new json file
    return base64.urlsafe_b64encode(raw.encode()).decode() #encodes this pair

def decode_cursor(cursor: Optional[str]) -> int:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode() #decodes this pair
    payload = json.loads(raw) #loading the key-val pair {'id': value} into a var 'payload'
    return payload['id'] #geting dict['id'] (value)



@app.get('/')
async def homepage():
    return {'Homepage': 'Hello World'}

@app.get('/campaigns', response_model=PaginatedResponse[list[Campaign]]) #[list[Campaign]]
async def read_campaigns(request: Request, session: SessionDep, cursor: Optional[str] = Query(None), limit: int = Query(10, ge=1)):
    cursor_id = 0
    if cursor:
        cursor_id = decode_cursor(cursor)

    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).where(Campaign.campaign_id > cursor_id).limit(limit + 1)).all()
    # if not data:
    #     raise HTTPException(status_code=404)
    
    base_url = str(request.url).split('?')[0]
    next_url = None
    if len(data) > limit:
        next_cursor = encode_cursor(data[:limit][-1].campaign_id)
        next_url = f'{base_url}?cursor={next_cursor}&limit={limit}'

    comparison = max(-1, cursor_id - limit)
    prev_url = f'{base_url}?cursor={encode_cursor(comparison)}&limit={limit}'


    return {
        'data': data,
        'next_url': next_url,
        'prev_url': prev_url
    }
    
@app.get('/campaigns/{id}', response_model=Response[Campaign])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    return {'data': data}

@app.post('/campaigns', response_model=Response[Campaign])
async def post_campaign(campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign) #validate using CampaignCreated class
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign) #auto updates missing attr of campaign_id & created_at

    return {'data': db_campaign}

@app.put('/campaigns/{id}', response_model=Response[Campaign])
async def update_campaign(id: int, campaign: CampaignCreated, session: SessionDep):
    db_campaign = CampaignCreated.model_validate(campaign) 
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    data.name = db_campaign.name
    data.due_date = db_campaign.due_date
    session.add(data)
    session.commit()
    session.refresh(data) #technically not needed, but could smooth out unexpected errs 
    return {'data': db_campaign}

@app.delete('/campaigns/{id}') #response_model=Response[Campaign]
async def delete_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    session.delete(data)
    session.commit()
    
    
