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

from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, Session, select
from datetime import datetime

from CRUDs.database import engine #import lowest lvl before mid lvl files in modular design
from CRUDs.models import Campaign, EASTERN_TZ
from CRUDs.endpoints import router #mid lvl file

#must be in main.py
def create_db_and_table():
    SQLModel.metadata.create_all(engine) #builds table & config w/ ORM in 'database.db'

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    with Session(engine) as session:
        first_data = session.exec(select(Campaign)).first()
        if not first_data:
            session.add_all([ #add_all -> adds multiple objs or list of objs | else system crashes (w/ out compilation error -> worst case)
                Campaign(name='Summer Sale', due_date=datetime.now(EASTERN_TZ)),
                Campaign(name='Summer Fest', due_date=datetime.now(EASTERN_TZ))
            ])
            session.commit()
    yield


app = FastAPI(root_path='/apis/v3', lifespan=lifespan)
app.include_router(router=router)