from typing import List, Optional
from pydantic import BaseModel
import datetime
from sqlalchemy import JSON, BigInteger

from sqlalchemy.sql.expression import text


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    expires: Optional[datetime.datetime]


class Login(BaseModel):
    username: str
    password: str


class Signup(BaseModel):
    password: str
    code: str


class RuleBase(BaseModel):
    subreddit: str
    content: str


class RuleCreate(RuleBase):
    pass


class Rule(RuleBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PostBase(BaseModel):
    subreddit: str
    flair: str
    title: str
    type: str
    content: str
    url: str
    scheduled_time: datetime.datetime
    status: str
    nsfw: bool
    spoiler: bool


class PostCreate(PostBase):
    pass


class PostCancle(BaseModel):
    id: int
    pass


class PostUpdate(PostBase):
    id: int
    subreddit: str
    flair: str
    title: str
    type: str
    content: str
    url: str
    scheduled_time: datetime.datetime
    nsfw: bool
    spoiler: bool
    pass


class Post(PostBase):
    id: int
    owner_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True


class FlairBase(BaseModel):
    subreddit: str
    content: str


class FlairCreate(FlairBase):
    pass


class Flair(FlairBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ItemBase(BaseModel):
    title: str

    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    hashed_password: str
    refresh_token: str


# class UserRedditToken(UserBase):
#     refresh_token: str
#     class Config:
#         orm_mode = True


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []
    posts: List[Post] = []

    class Config:
        orm_mode = True


class LogBase():
    method: str
    content: JSON
    owner_id: int


class Log(LogBase):
    id: BigInteger
    owner_id: int

    class Config:
        orm_mode = True
