"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
from google.appengine.api import users
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError


from flask import request, render_template, flash, url_for, redirect

from flask_cache import Cache

from application import app, render, make_url_safe
from decorators import login_required, admin_required
# from forms import ExampleForm
from models import Item, Lend, ndb, CATEGORIES


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


@app.route('/')
def home():
    return 'help...'
    

@app.route('/list')
def list(query=None):
    ''' Generic listing function, called by every other pre-filtering
    listers (see below).'''
    
    if not query:
        query = Item.query()

    return render({'list': query.fetch()}, 200)


@app.route('/list/<string:category>')
def list_cat(category):
    if not category in CATEGORIES:
        return render({'error': 'category invalid'}, 400)
    query = Item.query(Item.category == category)
    return list(query)


@app.route('/list/between/<int:start>/and/<int:end>')
def list_date(start, end):
    pass


@app.route('/item', methods=['POST', 'GET'])
def item_create():
    url_safe_name = make_url_safe(request.form.get('name'))
    item = Item(id = url_safe_name,
                name = request.form.get('name'),
                description = request.form.get('description'),
                count = int(request.form.get('count')) if request.form.get('count') else 1,
                prices = [float(request.form.get('price_int')) if request.form.get('price_int') else 0,
                          float(request.form.get('price_ext')) if request.form.get('price_ext') else 0,
                          float(request.form.get('price_com')) if request.form.get('price_com') else 0,
                          float(request.form.get('price_buy')) if request.form.get('price_buy') else 0,
                          ],
                tax_per_day = True if request.form.get('tax_per_day') else False,
                category = request.form.get('category'),
                )
    id = item.put().id()
    return render({'created': id}, 200)



'''
def home():
    return redirect(url_for('list_examples'))


def say_hello(username):
    """Contrived example to demonstrate Flask's url routing capabilities"""
    return 'Hello %s' % username


@login_required
def list_examples():
    """List all examples"""
    examples = ExampleModel.query()
    form = ExampleForm()
    if form.validate_on_submit():
        example = ExampleModel(
            example_name=form.example_name.data,
            example_description=form.example_description.data,
            added_by=users.get_current_user()
        )
        try:
            example.put()
            example_id = example.key.id()
            flash(u'Example %s successfully saved.' % example_id, 'success')
            return redirect(url_for('list_examples'))
        except CapabilityDisabledError:
            flash(u'App Engine Datastore is currently in read-only mode.', 'info')
            return redirect(url_for('list_examples'))
    return render_template('list_examples.html', examples=examples, form=form)


@login_required
def edit_example(example_id):
    example = ExampleModel.get_by_id(example_id)
    form = ExampleForm(obj=example)
    if request.method == "POST":
        if form.validate_on_submit():
            example.example_name = form.data.get('example_name')
            example.example_description = form.data.get('example_description')
            example.put()
            flash(u'Example %s successfully saved.' % example_id, 'success')
            return redirect(url_for('list_examples'))
    return render_template('edit_example.html', example=example, form=form)


@login_required
def delete_example(example_id):
    """Delete an example object"""
    example = ExampleModel.get_by_id(example_id)
    try:
        example.key.delete()
        flash(u'Example %s successfully deleted.' % example_id, 'success')
        return redirect(url_for('list_examples'))
    except CapabilityDisabledError:
        flash(u'App Engine Datastore is currently in read-only mode.', 'info')
        return redirect(url_for('list_examples'))


@admin_required
def admin_only():
    """This view requires an admin account"""
    return 'Super-seekrit admin page.'
'''


@cache.cached(timeout=60)
def cached_examples():
    """This view should be cached for 60 sec"""
    examples = ExampleModel.query()
    return render_template('list_examples_cached.html', examples=examples)


def warmup():
    """App Engine warmup handler
    See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests

    """
    return ''


# App Engine warm up handler
# See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests
app.add_url_rule('/_ah/warmup', 'warmup', view_func=warmup)

## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
