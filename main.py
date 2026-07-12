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

import base64
import json

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from typing import Optional, Any, Generic, Annotated, T


from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# EASTERN_TZ = ZoneInfo('America/New_York')

class Campaign(SQLModel, table=True): #row in db
    campaign_id: int | None = Field(default=None, primary_key=True, nullable=False) #each field attr is a col in db
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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


sqlite_file_name = 'database.db' #use sqlite3 & later
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(url=sqlite_url, echo=False, connect_args={'check_same_thread': False})

def create_db_and_table():
    SQLModel.metadata.create_all(engine) #builds table & config w/ ORM in 'database.db'

def get_session():
    with Session(engine) as session:
        yield(session)


SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    with Session(engine) as session:
        first_data = session.exec(select(Campaign)).first()
        if not first_data:
            session.add_all([ #add_all -> adds multiple objs or list of objs | else system crashes (w/ out compilation error -> worst case)
                Campaign(name='Summer Sale', due_date=datetime.now(timezone.utc)),
                Campaign(name='Summer Fest', due_date=datetime.now(timezone.utc))
            ])
            session.commit()
    yield


app = FastAPI(root_path='/apis/v3', lifespan=lifespan)

@app.get('/')
async def homepage():
    return {'Homepage welcome: ' : 'Hello World'}


def encode_cursor(value: Optional[int]) -> str:
    raw = json.dumps({'cursor_id': value}) #dumping the key-val pair {'cursor_id': value} into a new json file
    return base64.urlsafe_b64encode(raw.encode()).decode() #encodes this pair

def decode_cursor(cursor: Optional[str]) -> int:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode() #decodes this pair
    payload = json.loads(raw) #loading the key-val pair {'id': value} into a var 'payload'
    return payload['cursor_id'] #fetches dict['id'] (value)

@app.get('/campaigns', response_model=PaginatedResponse[list[Campaign]])
async def read_campaigns(request: Request, session: SessionDep, cursor: Optional[str] = Query(None), limit: int = Query(10, ge=1)):
    cursor_id = 0
    if cursor:
        cursor_id = decode_cursor(cursor)
    
    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).where(Campaign.campaign_id > cursor_id).limit(limit + 1)).all()
    # if not data:
    #     return {'No data availible to be viewed'}
    
    base_url = str(request.url).split('?')[0]

    next_url = None
    if len(data) > limit:
        next_cursor = encode_cursor(data[:limit][-1].campaign_id)
        next_url = f'{base_url}?cursor={next_cursor}&limit={limit}'

    prev_cursor = encode_cursor(max(-1, cursor_id - limit))
    prev_url = f'{base_url}?cursor={prev_cursor}&limit={limit}'

    return {
        'data': data,
        'next_url': next_url,
        'prev_url': prev_url
    }


#other crud methods finally
@app.get('/campaigns/{id}', response_model=Response[Campaign])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail=f'Campaign with ID#{id} object not found or unrecognized. Please try again.')
    
    return {'data': data}

@app.post('/campaigns', response_model=Response[Campaign])
async def post_campaign(campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign) #auto validates & return err if not formatted based on CampaignCreated 
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign) #auto updates missing attr of campaign_id & created_at

    return {'data': db_campaign}

@app.put('/campaigns/{id}', response_model=Response[Campaign])
async def update_campaign(id: int, campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail=f'Campaign with ID#{id} object not found or unrecognized. Please try again.')

    data.name = db_campaign.name
    data.due_date = db_campaign.due_date
    session.add(data)
    session.commit()
    session.refresh(data) #technically not needed, but could smooth out unexpected errs 
    
    new_data = await read_campaign(id, session) #if don't add await, encounters a compilation err -> see next line
    #unexecuted coroutine object to FastAPI, which throws a ResponseValidationError 
    # because it expects a dictionary or database object it can convert into JSON.

    return {'data': new_data} 

@app.delete('/campaign/{id}')
async def delete_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail=f'Campaign with ID#{id} object not found or unrecognized. Please try again.')
    
    session.delete(data)
    session.commit()