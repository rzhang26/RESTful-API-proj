from sqlmodel import Session, create_engine
from fastapi import Depends
from typing import Annotated

sqlite_file_name = 'database.db' #use sqlite3 & later
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(url=sqlite_url, echo=False, connect_args={'check_same_thread': False}) #sqlmodel ORM instance | thing that does the python-SQL minipulation

def get_session():
    with Session(engine) as session:
        yield(session)

SessionDep = Annotated[Session, Depends(get_session)]
