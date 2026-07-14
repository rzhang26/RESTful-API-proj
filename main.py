from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Session, select

from CRUDs.database import engine
from CRUDs.models import Campaign, EASTERN_TZ
from CRUDs.router import router

def create_db_and_table():
    SQLModel.metadata.create_all(bind=engine, tables=None, checkfirst=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    with Session(engine) as session:
        first_data = session.exec(select(Campaign)).first()
        if not first_data:
            session.add_all([ #add_all -> adds multiple objs or list of objs | else system crashes (w/ out compilation error -> worst case)
                Campaign(name='Summer Sale', due_date=datetime.now(EASTERN_TZ)),
                Campaign(name='Summer Stale', due_date=datetime.now(EASTERN_TZ))
            ])
            session.commit()
    yield

app = FastAPI(root_path='/api/v4', lifespan=lifespan)
app.include_router(router=router)

# if __name__ == '__main__':
#     app.run()

