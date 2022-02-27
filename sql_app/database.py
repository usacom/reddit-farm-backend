try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser(".config/db/config.cfg")])
conf = dict(config.items("postgres"))
print('db config', conf)
# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = "postgresql://" + \
    conf['user']+":"+conf['password']+"@"+conf['host']+"/"+conf['db']

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
