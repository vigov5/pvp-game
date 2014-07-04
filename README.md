fctf
====
###### some experiments with Flask framework
### Create virtualenv
- create virtualenv, folder flask
- install packages

argparse (1.2.1)  
Babel (1.3)  
blinker (1.3)  
decorator (3.4.0)  
Flask (0.10.1)  
Flask-Babel (0.9)  
Flask-Login (0.2.11)  
Flask-Mail (0.9.0)  
Flask-OpenID (1.2.1)  
Flask-SQLAlchemy (1.0)  
Flask-WhooshAlchemy (0.55)  
Flask-WTF (0.9.5)  
flup (1.0.2)  
itsdangerous (0.24)  
Jinja2 (2.7.3)  
MarkupSafe (0.23)  
MySQL-python (1.2.5)  
pbr (0.8.2)  
pip (1.5.2)  
python-openid (2.2.5)  
pytz (2014.4)  
setuptools (2.1)  
six (1.7.3)  
speaklater (1.3)  
SQLAlchemy (0.9.6)  
sqlalchemy-migrate (0.9.1)  
Tempita (0.5.2)  
Werkzeug (0.9.6)  
Whoosh (2.6.0)  
wsgiref (0.1.2)  
WTForms (1.0.5)  

### Config with mod_wsgi
- Ensure that libapache2-mod-wsgi is installed
- add following to /etc/apache2/sites-available/default

`WSGIDaemonProcess ctf python-path=/path-to-repo/fctf:/path-to-repo/flask/lib/python2.7/site-packages`

`WSGIProcessGroup ctf`

`WSGIScriptAlias / /path-to-repo/fctf/run.py`
