import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'mysql://pvp_admin:pvp_admin@localhost/pvp_db'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

CSRF_ENABLED = True
SECRET_KEY = 'kjgad86o!Jj0y1-3!^-{JNdGlada;!T#*!&#!DMSA(!^#_!'
