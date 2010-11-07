from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from celery import conf
from celery.utils.compat import defaultdict

QueueModelBase = declarative_base()

_SETUP = defaultdict(lambda: False)
_ENGINES = {}


def get_engine(dburi, **kwargs):
    if dburi not in _ENGINES:
        _ENGINES[dburi] = create_engine(dburi, **kwargs)
    return _ENGINES[dburi]


def create_session(dburi, **kwargs):
    engine = get_engine(dburi, **kwargs)
    return engine, sessionmaker(bind=engine)


def setup_queue(engine):
    if not _SETUP["queue"]:
        QueueModelBase.metadata.create_all(engine)
        _SETUP["queue"] = True


def QueueSession(dburi=conf.RESULT_DBURI, **kwargs):
    engine, session = create_session(dburi, **kwargs)
    setup_queue(engine)
    return session()
 