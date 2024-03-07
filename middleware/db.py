from sqlalchemy import create_engine, Column, String, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from hashlib import sha256
import json
from sqlalchemy.exc import DatabaseError
se = json.loads(open('./secret1.json').read())
Base = declarative_base()

# Login


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, nullable=True)
    pw = Column(String, nullable=True, unique=True)


def encryption(password: str) -> str:
    return sha256(password.encode()).hexdigest()

# data Upload


class BMeal(Base):
    __tablename__ = "breakfast"
    date = Column(DateTime, primary_key=True, unique=True, nullable=False)
    weekday = Column(String, nullable=False)
    b_diners = Column(String, nullable=False)
    event = Column(String, nullable=False)
    menu1 = Column(String, nullable=False)
    menu2 = Column(String, nullable=False)


class LMeal(Base):
    __tablename__ = "lunch"
    date = Column(DateTime, primary_key=True, unique=True, nullable=False)
    weekday = Column(String, nullable=False)
    l_diners = Column(String, nullable=False)
    event = Column(String, nullable=False)
    menu1 = Column(String, nullable=False)
    menu2 = Column(String, nullable=False)


class DMeal(Base):
    __tablename__ = "dinner"
    date = Column(DateTime, primary_key=True, unique=True, nullable=False)
    weekday = Column(String, nullable=False)
    d_diners = Column(String, nullable=False)
    event = Column(String, nullable=False)
    menu1 = Column(String, nullable=False)
    menu2 = Column(String, nullable=False)


class Weather(Base):
    __tablename__ = "weather"
    date = Column(DateTime, primary_key=True, unique=True, nullable=False)
    rainfall = Column(Float, nullable=False)
    avg_rh = Column(Float, nullable=False)
    max_temp = Column(Float, nullable=False)
    min_temp = Column(Float, nullable=False)
    avg_temp = Column(Float, nullable=False)
    di_b = Column(String, nullable=False)
    di_l = Column(String, nullable=False)
    di_d = Column(String, nullable=False)


def dbConnect(db: str, port: int):
    URL = f"postgresql://{se.get('ID')}:{se.get('PW')}@{se.get('HOST')}:{port}/{db}"
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
