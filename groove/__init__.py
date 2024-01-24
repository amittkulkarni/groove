from flask_migrate import Migrate
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///groove.sqlite3'
app.config['SECRET_KEY'] = 'secret_development_key'

db = SQLAlchemy(app)  # Initializing database using flask-sqlalchemy
app.app_context().push()
migrate = Migrate(app, db)   # Flask DB migration using Flask-Migrate


def create_tables():
    db.create_all()


from groove import routes
