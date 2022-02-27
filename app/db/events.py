try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import os
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import asyncpg
from fastapi import FastAPI

from app.core.settings.app import AppSettings


async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    logger.info("Connecting to {0}", repr(settings.database_url))

    app.state.pool = await asyncpg.create_pool(
        str(settings.database_url),
        min_size=settings.min_connection_count,
        max_size=settings.max_connection_count,
    )

    logger.info("Connection established")


async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    await app.state.pool.close()

    logger.info("Connection closed")
