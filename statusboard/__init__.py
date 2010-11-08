import os.path

from flask import Flask
from flaskext.celery import Celery
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'statusboard.db')
app.config['BROKER_BACKEND'] = 'sqlakombu.transport.Transport'
app.config['BROKER_HOST'] = app.config['SQLALCHEMY_DATABASE_URI']
app.config['CELERY_RESULT_BACKEND'] = 'database'
app.config['CELERY_RESULT_DBURI'] = app.config['SQLALCHEMY_DATABASE_URI']
app.config['CELERYBEAT_SCHEDULER'] = 'statusboard.schedulers.DatabaseScheduler'
app.config['CELERYBEAT_SCHEDULE_FILENAME'] = app.config['SQLALCHEMY_DATABASE_URI']
#app.config['CELERY_ALWAYS_EAGER'] = True
app.config['CELERYD_PREFETCH_MULTIPLIER'] = 0
app.secret_key = 'SEKRIT'
db = SQLAlchemy(app)
celery = Celery(app)
