from sqlmodel import Session, create_engine
from fastapi import Depends
from typing import Annotated


sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
connect_args = {'check_same_thread': False}

engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield(session)

SessionDep = Annotated[Session, Depends(get_session)]


