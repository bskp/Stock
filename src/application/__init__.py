"""
Initialize Flask app

"""
from flask import Flask 
from flask.ext.sqlalchemy import SQLAlchemy

# from flask_debugtoolbar import DebugToolbarExtension
# from werkzeug.debug import DebuggedApplication


app = Flask('application')
app.config.from_object('application.settings')
db = SQLAlchemy(app)

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

# jinja custom filter for pretty cash-amounts
def jinja_cash(amount):
    if not amount:
        return '-.-'
    big, small = str(amount).split('.')
    if small == '0':
        small = '-'
    else:
        small = '%02i' % int(small)
    return '%s,%s' % (big, small)
app.jinja_env.filters['cash'] = jinja_cash


def jinja_date(timestamp):
    pass



'''
@app.context_processor
def inject_profiler():
    return dict(profiler_includes=templatetags.profiler_includes())
'''


# A Helper function
def make_url_safe(string):
    from unidecode import unidecode
    from werkzeug.urls import url_fix
    return url_fix( unidecode( string.replace(' ', '_') ) ).lower()


# Pull in URL dispatch routes and their views
import views

'''
# Flask-DebugToolbar (only enabled when DEBUG=True)
toolbar = DebugToolbarExtension(app)

# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

# GAE Mini Profiler (only enabled on dev server)
# app.wsgi_app = profiler.ProfilerWSGIMiddleware(app.wsgi_app)
'''
