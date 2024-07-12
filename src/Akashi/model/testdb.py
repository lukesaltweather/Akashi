from sqlalchemy.orm import sessionmaker

from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.model.staff import Staff
from Akashi.util.db import Base, loadDB


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
