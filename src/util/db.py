from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# TODO: Fix usage of global
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def loadDB(uri):
    engine = create_engine(uri, pool_size=20)
    return engine