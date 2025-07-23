from flask import Flask
import os

def create_app():
    # Tell Flask to look for templates in "../templates"
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, '..', 'templates')

    app = Flask(__name__, template_folder=template_path)
    app.config.from_object('config.Config')

    # Register Blueprints
    from .routes import main
    app.register_blueprint(main)

    from . import db
    app.teardown_appcontext(db.close_db)
    
    @app.cli.command('init-db')
    def init_db_command():
        """Clear existing data and create new tables."""
        db.init_db()
        print('Initialized the database.')

    return app

