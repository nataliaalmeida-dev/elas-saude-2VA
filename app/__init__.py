import os, re
from flask import Flask, session, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

from . import models
from .routes import bp as main_bp, seed_db


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///elas_saude.db'
)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(main_bp)


    @app.context_processor
    def utility_processor():

        def get_avatar_url(cpf):
            cpf_limpo = re.sub(r'\D', '', cpf) if cpf else ''
            filename = f'assets/usuario/{cpf_limpo}.png' if cpf_limpo else 'assets/usuario/.png'
            path = os.path.join(app.root_path, '..', 'static', filename)
            
            if os.path.exists(path):
                mtime = int(os.path.getmtime(path))
                return url_for('static', filename=filename, v=mtime)
            return url_for('static', filename='assets/usuario/usuario.png')
            
        def get_prof_foto_url(foto_url):
            if not foto_url: return url_for('static', filename='assets/usuario/usuario.png')
            path = os.path.join(app.root_path, '..', 'static', foto_url)
            if os.path.exists(path):
                mtime = int(os.path.getmtime(path))
                return url_for('static', filename=foto_url, v=mtime)
            return url_for('static', filename='assets/usuario/usuario.png')
            
        ctx = dict(get_avatar_url=get_avatar_url, get_prof_foto_url=get_prof_foto_url)
        if 'usuario_id' in session:
            user = models.User.query.get(session['usuario_id'])
            ctx['current_user'] = user
        else:
            ctx['current_user'] = None
        return ctx
        
    @app.after_request
    def add_header(response):
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    with app.app_context():
        db.create_all()
        seed_db()

    return app
