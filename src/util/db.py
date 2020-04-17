from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# TODO: Fix usage of global
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def loadDB():
    engine = create_engine('postgresql://Akashi:CWyYxRCvRg5hs@54.37.74.196:5432', pool_size=20)
    return engine