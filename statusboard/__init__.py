import os.path

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'statusboard.db')
db = SQLAlchemy(app)
