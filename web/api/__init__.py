from flask import Flask
from ..models import db, User, Animal, Image

def create_app():
    app = Flask(__name__)

  
    from web.api.routes import app1 
    app.register_blueprint(app1)


    with db:
        db.create_tables([User, Animal, Image])
        
    return app