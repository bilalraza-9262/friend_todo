# fastapi_neon/main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from .setting import DATABASE_URL
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

class Todo(SQLModel, BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    status: bool = False


# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
connection_string = str(DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


# recycle connections after 5 minutes
# to correspond with the compute scale down
engine = create_engine(
    connection_string
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB")

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/todos/", response_model=list[Todo])
def read_todos(session: Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    return todos


@app.post("/createtodo/", response_model=list[Todo])
def create_todo(todo: Todo, session: Annotated[Session, Depends(get_session)]):
    user_todo = Todo(content=todo.content)
    session.add(user_todo)
    session.commit()
    all_todos = session.exec(select(Todo)).all()
    return all_todos


@app.delete("/deletetodo/", response_model=list[Todo])
def delete_todo(todo_id: int, session: Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id == todo_id)).one()
    session.delete(todo)
    session.commit()
    all_todos = session.exec(select(Todo)).all()
    return all_todos
