"""
The flask application package.
"""
from pypyodbc import *
from flask import Flask

app = Flask(__name__)
app.secret_key = 'uniq'

from FlaskWebProject1 import views

