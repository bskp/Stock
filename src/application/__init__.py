"""
Initialize Flask app

"""
from flask import Flask, request, render_template, jsonify

from flask_debugtoolbar import DebugToolbarExtension
from gae_mini_profiler import profiler, templatetags
from werkzeug.debug import DebuggedApplication


app = Flask('application')
app.config.from_object('application.settings')

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')


@app.context_processor
def inject_profiler():
    return dict(profiler_includes=templatetags.profiler_includes())


def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def render(data, status=200):
    if not request_wants_json():
        # on loading the app, the current resource will be re-requested with
        # a json-requesting header
        return render_template('app.html')

    response = jsonify(data)
    response.status_code = status

    return response


def make_url_safe(string):
    from unidecode import unidecode
    from werkzeug.urls import url_fix
    return url_fix( unidecode( string ) )


# Pull in URL dispatch routes and their views
import views

# Flask-DebugToolbar (only enabled when DEBUG=True)
toolbar = DebugToolbarExtension(app)

# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

# GAE Mini Profiler (only enabled on dev server)
app.wsgi_app = profiler.ProfilerWSGIMiddleware(app.wsgi_app)
