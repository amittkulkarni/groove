from flask_migrate import Migrate
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///groove.sqlite3'
app.config['SECRET_KEY'] = 'secret_development_key'

db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app, db)


def create_tables():
    db.create_all()


from groove import routes
