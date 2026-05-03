from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    text = Column(Text)
    result = Column(String)   # Fake / Real / Suspicious
    score = Column(Integer)
    reason = Column(Text)
    advice = Column(Text)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(Text, unique=True, index=True)
    password = Column(Text)   
    role = Column(Text)
