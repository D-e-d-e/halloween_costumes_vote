from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv() # Carica le variabili da .env

app = Flask(__name__) # <-- 'app' viene definito qui
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///site.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "un_secret_di_default_molto_debole")

db = SQLAlchemy(app) # <-- 'db' viene definito qui

# Queste importazioni DEVONO stare DOPO la definizione di 'app' e 'db'
# altrimenti, quando models.py o routes.py tentano di usare 'app' o 'db',
# potrebbero trovarli ancora non definiti o parzialmente definiti, causando l'errore.
from app import routes, models