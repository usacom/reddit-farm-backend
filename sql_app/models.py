from praw.reddit import Subreddit
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, func, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP, JSON

from .enums import PostStatus
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    refresh_token = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")
    posts = relationship("Post", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="items")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    subreddit = Column(String, index=True)
    content = Column(JSON)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), server_onupdate=func.now()
    )


class Flair(Base):
    __tablename__ = "flairs"

    id = Column(Integer, primary_key=True, index=True)
    subreddit = Column(String, index=True)
    content = Column(JSON)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), server_onupdate=func.now()
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    subreddit = Column(String, index=True, nullable=False,)
    flair = Column(String)
    title = Column(String, nullable=False,)
    type = Column(String, nullable=False,)
    content = Column(JSON)
    scheduled_time = Column(String)
    url = Column(String)
    status = Column(Enum(PostStatus))
    nsfw = Column(Boolean)
    spoiler = Column(Boolean)
    owner_id = Column(Integer, ForeignKey("users.id"),
                      nullable=False, index=True)
    owner = relationship("User", back_populates="posts")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), server_onupdate=func.now()
    )


class Log():
    __tablename__ = "logs"
    id = Column(BigInteger, primary_key=True, index=True)
    method = Column(String)
    content = Column(JSON)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

