from sqlalchemy.orm import sessionmaker

from src.model.chapter import Chapter
from src.util.db import Base, loadDB
from src.model.staff import Staff
from src.model.project import Project


async def create():
    engine = loadDB()

    Base.metadata.create_all(engine)


async def createtables():
    engine = loadDB()
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    session = Session()

    luke = Staff(358244935041810443, "lukesaltweather")
    wordref = Staff(345845639663583252, "wordref")
    yankee = Project("Yankee-kun", "active", "https://google.com", "Yankee")
    chapter = Chapter(24, "https://google.com")

    chapter.translator = wordref
    chapter.proofreader = wordref
    chapter.project = yankee
    yankee.typesetter = luke

    session.add(luke)
    session.add(wordref)
    session.add(yankee)
    session.add(chapter)

    session.commit()
    session.close()
