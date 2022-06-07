from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import pytz


from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from . import models, schemas, enums
from .database import SessionLocal

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "ba4f21f65844383eb372e19196e08eb1649c40e166c8cdd521b52abef3063a13"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    db = SessionLocal()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        expires = payload.get("exp")
    except JWTError:
        raise credentials_exception
    token_data = schemas.TokenData(username=username, expires=expires)

    # validate username
    if username is None:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    # check token expiration
    if expires is None:
        raise credentials_exception
    # if datetime.utcnow() > token_data.expires:
    # raise credentials_exception

    return user


def get_token_info(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        expires = payload.get("exp")
    except JWTError:
        raise credentials_exception
    if username is None:
        raise credentials_exception
    token_data = schemas.TokenData(username=username, expires=expires)

    # check token expiration

    now = pytz.UTC.localize(datetime.utcnow())
    token_date = token_data.expires
    print("now", now)
    print("token_data.expires", token_data.expires)
    if expires is None:
        raise credentials_exception
    if now > token_date:
        print("datetime.utcnow() > token_data.expires")
    #     raise credentials_exception
    return token_data


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user["username"],
        hashed_password=user["hashed_password"],
        refresh_token=user["refresh_token"],
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_rules_by_subreddit(db: Session, subreddit: str):
    return db.query(models.Rule).filter(models.Rule.subreddit == subreddit).first()


def create_subreddit_rules(db: Session, item: schemas.RuleCreate):
    db_item = models.Rule(**item)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_subreddit_rules(db: Session, subreddit: str, item):
    print("update_subreddit_rules subreddit", subreddit)
    row = db.query(models.Rule).filter(
        models.Rule.subreddit == subreddit).first()
    row.content = item
    row.updated_at = func.now()

    db.commit()
    db.flush()
    print("updated row rules", row)


def get_flairs_by_subreddit(db: Session, subreddit: str):
    return db.query(models.Flair).filter(models.Flair.subreddit == subreddit).first()


def create_subreddit_flairs(db: Session, item: schemas.FlairCreate):
    db_item = models.Flair(**item)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_subreddit_flairs(db: Session, subreddit: str, item):
    print("update_subreddit_rules subreddit", subreddit)
    row = db.query(models.Flair).filter(
        models.Flair.subreddit == subreddit).first()
    row.content = item
    row.updated_at = func.now()

    db.commit()
    db.flush()
    print("updated row flairs", row)


def get_items(db: Session, skip: int = 0, limit: int = 100):

    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_posts(db: Session, user: schemas.User, filter: enums.PostLoadFilter, skip: int = 0, limit: int = 100):
    print('filter', filter),
    if filter == enums.PostLoadFilter.NOTCANCELED:
        print('filter NOTCANCELED !')
        return db.query(models.Post).filter(models.Post.owner_id == user.id).filter(models.Post.status != 'CANCELED').offset(skip).limit(limit).all()
    else:
        return db.query(models.Post).filter(models.Post.owner_id == user.id).offset(skip).limit(limit).all()

def get_scheduled_posts(db: Session, skip: int = 0, limit: int = 100):
    print('get_scheduled_posts')
    return db.query(models.Post).filter(models.Post.status == enums.PostLoadFilter.RESCHEDULED or models.Post.status == enums.PostLoadFilter.SCHEDULED).filter(models.Post.scheduled_time <= func.now()).offset(skip).limit(limit).all()
    


def get_post_by_id(db: Session, id: int):
    return db.query(models.Post).filter(models.Post.id == id).first()


def cancle_user_post(db: Session, id: int, user: schemas.User):
    row = db.query(models.Post).filter(
        models.Post.id == id).filter(models.Post.owner_id == user.id).first()
    row.status = enums.PostStatus.CANCELED
    row.updated_at = func.now()
    db.commit()
    db.flush()
    return


def publish_user_post(db: Session, id: int, user: schemas.User, url: str):
    row = db.query(models.Post).filter(models.Post.id == id).filter(
        models.Post.owner_id == user.id).first()
    row.status = enums.PostStatus.PUBLISHED
    row.url = url
    row.updated_at = func.now()
    db.commit()
    db.flush()
    return


def create_user_post(db: Session, post: schemas.PostCreate, user: schemas.User):
    db_post = models.Post(**post.dict(), owner_id=user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_user_post(db: Session, post: schemas.Post, user: schemas.User):
    # db_post = models.Post(**post.dict(), owner_id=user.id)
    print("update_subreddit_rules subreddit", subreddit)
    row = db.query(models.Flair).filter(
        models.Post.id == post.id).filter(models.Post.owner_id == user.id).first()
    row = models.Post(**post.dict())
    row.updated_at = func.now()

    db.commit()
    db.flush()


def add_log(db: Session, log: schemas.LogBase):
    db_log = models.Log(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
