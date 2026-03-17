import os # lets us read env variables injected at runtime
from dotenv import load_dotenv # import ability to load env vars from the env file
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # ability to connect to postgres database asynchronously
from sqlalchemy.orm import sessionmaker, DeclarativeBase # import factory for creating sessions, and the template class for the database definitions

load_dotenv() # opens the env file and loads the env vars 
DATABASE_URL = os.getenv("DATABASE_URL") # fetch database url 
engine = create_async_engine(DATABASE_URL, echo = True) # create async connection to database, true for testing

# set up for session factory
AsyncSessionLocal = sessionmaker(
    bind=engine, # use the database connection created
    class_=AsyncSession, # make async sessions so can work for different requests
    expire_on_commit=False # keep data in local session memory during request
)

# base class for database table defn.
# inherits from SQLAlchemy DeclarativeBase
class Base(DeclarativeBase):
    pass # don't need additional columns right now