from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
from hashlib import sha256
import json

se = json.loads(open('./secret1.json').read())
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, nullable=True)
    pw = Column(String, nullable=True, unique=True)


def encryption(password: str) -> str:
    return sha256(password.encode()).hexdigest()


def dbConnect(db: str):
    URL = f"postgresql://{se.get('ID')}:{se.get('PW')}@{se.get('HOST')}:{se.get('PORT')}/{db}"
    engine = create_engine(URL, echo=False)
    session = sessionmaker(autocommit=False, autoflush=True, bind=engine)()
    return engine, session


if __name__ == "__main__":
    # engine, db = dbConnect("users")
    # data = User(id="admin", pw=encryption("qwer1234"))
    # db.add(data)
    # db.commit()
    # db.close()
    pass
