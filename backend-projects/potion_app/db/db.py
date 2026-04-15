from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    "sqlite:///potion_db.db", connect_args={"check_same_thread": False}
)


local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = local_session()

    try:
        yield db
    finally:
        db.close()
