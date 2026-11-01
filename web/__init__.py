from flask import Flask
from flask_login import LoginManager, login_user, logout_user, login_required
from playhouse.db_url import connect 
from .database import db
from .models import User, Animal, Image, Admin
from .config import Config, DATABASE_PATH

import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + DATABASE_PATH)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    from .api.routes import app1
    login = LoginManager(app)

    @login.user_loader
    def load_user(admin_id):
        return Admin.get_or_none(Admin.id == admin_id)

    supabase_db = connect(DATABASE_URL)
    db.initialize(supabase_db)
    # ---------------------------------

    @app.before_request
    def before_request():
        db.connect(reuse_if_open=True)

    @app.teardown_appcontext
    def teardown(exc):
        if not db.is_closed():
            db.close()

    app.register_blueprint(app1)

    with db:
        db.create_tables([User, Animal, Image, Admin], safe=True)

    return app