import re
from typing import *
import typing
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.sql.expression import false
from sqlalchemy.sql.sqltypes import String

from server import Server

from sqlalchemy.orm import Session

from sql_app import crud, models, schemas, enums
from sql_app.database import SessionLocal, engine

from fastapi.security import OAuth2PasswordBearer

ACCESS_TOKEN_EXPIRE_MINUTES = 120

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


tags_metadata = [
    {"name": "login", "description": "Получение ссылки для авторазации через reddit", },
    {
        "name": "main",
        "description": "Заглушка для получения кода авторизации после редиректа с reddit",
    },
    {"name": "signup", "description": "Регистрация после получения кода от reddit", },
    {
        "name": "posts",
        "description": "Получение последних 100 постов авторизированого пользователя",
    },
    {
        "name": "token",
        "description": "Внутренняя авторизация. Получение токена для работы с API.",
    },
    {
        "name": "user-me",
        "description": "Получение данных об авторизированном пользователе",
    },
    {
        "name": "user-subreddits",
        "description": "Получение списка сабредитов пользователя (без пользователей)",
    },
    {
        "name": "post-subreddit-info",
        "description": "Загрузка данных о сабредите необходимых для создания публикации",
    },
    {
        "name": "post-subreddits-info",
        "description": "Загрузка данных по сабредитам необходимых для создания публикации. Минимум 1, максимум 50",
    },
]

app = FastAPI(title="Reddit farm API", openapi_tags=tags_metadata)
server = Server()

origins = [
    "*",
    # "http://localhost",
    # "http://localhost:8080",
    # "http://localhost:8000",
    # "http://reddit-farm.test/",
    # "http://app.reddit-farm.test/",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/login", tags=["login"])
def get_link_to_auth():
    return server.get_link_to_auth()


# @app.get("/", tags=["main"])
# def read_auth_code(state: typing.Optional[str] = None, code: typing.Optional[str] = None, db: Session = Depends(get_db)):
#     if state != None and code != None:
#         print('code', code)
#     return {"state": state, "code": code}


@app.post("/signup/", tags=["signup"])
async def create_new_user(request: schemas.Signup, db: Session = Depends(get_db)):
    print("create_new_user")
    password = request.password
    code = request.code
    print("code", code)
    print("password", password)
    user_data = server.get_user_data(code)
    print("user_data", user_data)
    db_user = crud.get_user_by_username(db, username=user_data["username"])
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username already registered")
    hashed_password = crud.get_password_hash(password)
    print("hashed_password", hashed_password)
    user = crud.create_user(
        db=db,
        user={
            "username": user_data["username"],
            "hashed_password": hashed_password,
            "refresh_token": user_data["refresh_token"],
        },
    )
    return user


@app.post("/token", response_model=schemas.Token, tags=["token"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    print(form_data)
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    print({"access_token": access_token, "token_type": "bearer"})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/status")
def get_token_status(
    current_satus: schemas.User = Depends(crud.get_token_info),
    db: Session = Depends(get_db),
):
    print(current_satus)
    return current_satus


@app.get("/posts", tags=["posts"])
def get_user_posts(
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username
    user_data = crud.get_user_by_username(db, username)
    print("username", username)
    print("user_data", user_data)
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    # return user_data
    return server.get_user_posts(user_data.refresh_token)


@app.get("/posts/schedule", tags=["posts"])
def get_schedule_posts(
    filter=enums.PostLoadFilter.NOTCANCELED,
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username
    user_data = crud.get_user_by_username(db, username)
    print("username", username)
    print("user_data", user_data)
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_posts(db, user_data, filter=filter)
    # return server.get_user_posts(user_data.refresh_token)


@app.post("/post/", tags=["post"])
def create_post(
    response_model: schemas.PostCreate,
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_post(db, response_model, current_user)


@app.post("/posts/", tags=["post"])
def create_posts(
    response_model: List[schemas.PostCreate],
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    posts = []
    for post in response_model:
        print(post)
        posts.append(crud.create_user_post(db, post, current_user))

    return posts
    # return crud.create_user_post(db, response_model, current_user)


@app.post("/post/cancle/{post_id}")
def update_post(
        post_id,
        current_user: schemas.User = Depends(crud.get_current_user),
        db: Session = Depends(get_db),):
    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    post = crud.get_post_by_id(db, post_id)
    if post.status == 'PUBLISHED':
        raise HTTPException(status_code=400, detail="Post be a published")
    crud.cancle_user_post(db, post_id, current_user)
    post = crud.get_post_by_id(db, post_id)
    return post


@app.get("/users/me/", response_model=schemas.User, tags=["user-me"])
async def read_users_me(current_user: schemas.User = Depends(crud.get_current_user)):
    return current_user


@app.get("/users/subreddits/", tags=["user-subreddits"])
def get_users_subs(
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username
    user_data = crud.get_user_by_username(db, username)
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    return server.get_users_subsreddits(user_data.refresh_token)


@app.get("/post/subreddit-info/", tags=["post-subreddit-info"])
def get_sub_info(
    subreddit: str,
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username
    user_data = crud.get_user_by_username(db, username)
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    return server.get_subsreddit_info(user_data.refresh_token, subreddit)


@app.post("/post/subreddits-info/", tags=["post-subreddits-info"])
def get_subs_info(
    subreddits: List[str],
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username
    user_data = crud.get_user_by_username(db, username)
    print("count of subreddits: ", len(subreddits))
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    # if len(subreddits) > 50 or len(subreddits) == 0 is None:
    # raise HTTPException(status_code=400, detail="Wrong count of subreddits")
    return server.get_subsreddits_info(db, user_data.refresh_token, subreddits)


@app.post("/post/manual/{post_id}")
def publish_post_manual(
    post_id: int,
    current_user: schemas.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username
    user_data = crud.get_user_by_username(db, username)
    print("post_id: ", post_id)
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")

    post = crud.get_post_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.status == 'PUBLISHED' or post.status == 'CANCELED':
        raise HTTPException(
            status_code=400, detail="Post be a published or canceled")

    return server.create_user_post(db, user_data, post)


# @app.post("/post/subreddits-info-test/", tags=["post-subreddits-info"])
# def get_subs_info(
#     subreddits: List[str],
#     current_user: schemas.User = Depends(crud.get_current_user),
#     db: Session = Depends(get_db),
# ):
#     username = current_user.username
#     user_data = crud.get_user_by_username(db, username)
#     print("count of subreddits: ", len(subreddits))
#     if user_data is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     # if len(subreddits) > 50 or len(subreddits) == 0 is None:
#     # raise HTTPException(status_code=400, detail="Wrong count of subreddits")
#     return server.test_load_to_base_rules(db, user_data.refresh_token, subreddits)
