# coding=latin-1
"""
views.py

Route handlers for HTML

"""

from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from flask import request, render_template, flash, url_for, redirect, send_from_directory, session
from werkzeug import secure_filename

from flask_cache import Cache

from application import app, make_url_safe
from decorators import login_required, admin_required
from models import Item, Lend, ndb, CATEGORIES


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


def pjax(template, query=None, **kwargs):
    """Determine whether the request was made by PJAX."""

    if not query:
        query = Item.query()

    if "X-PJAX" in request.headers:
        return render_template(template, items=query.fetch(), **kwargs)
    
    return render_template('base.html',
                           template = template,
                           items = query.fetch(),
                           **kwargs
                           )

@app.route('/')
def home():
    return redirect(url_for('list'))


@app.route('/list')
def list(query=None):
    ''' Generic listing function, called by every other pre-filtering
    listers (see below).'''
    
    return pjax('content.html', query)


@app.route('/list/<string:category>')
def list_cat(category):
    if not category in CATEGORIES:
        return pjax('flash.html', 'error', 'Invalid category')
    query = Item.query(Item.category == category)
    return list(query)


@app.route('/lend/between/<int:start>/and/<int:end>')
def set_timespan(start, end):
    session['from'] = start
    session['until'] = end
    return redirect(url_for('list'))


@app.route('/item/<id>', methods=['GET'])
def item(id):
    key = ndb.Key('Item', id) 
    if request.method == 'GET':
        return pjax('detail.html',
                    item=key.get(),
                    in_cart = session.get(id),
                   ) 


@app.route('/item/<id>/edit')
def item_edit(id):
    return item_create(ndb.Key('Item', id))

@app.route('/item/<id>/take')
@app.route('/item/<id>/take/<int:count>')
def item_take(id, count=1):
    if not id in session:
        session[id] = 0
    session[id] += count;
    flash('%s eingepackt.'%id, 'success')
    return item(id)

@app.route('/item/<id>/put')
@app.route('/item/<id>/put/<int:count>')
def item_put(id, count=1):
    if not id in session:
        session[id] = 0
    session[id] -= count;
    if session[id] < 0:
        session[id] = 0
    flash('%s zurueckgelegt.'%id, 'success')
    return item(id)

@app.route('/item_create', methods=['GET', 'POST'])
def item_create(replace_key=None):
    if replace_key:
        item = replace_key.get()
    else:
        item = None

    if request.method == 'GET':
        return pjax('create_item.html', item=item)

    # Else POST: save to db
    if not item:
        url_safe_name = make_url_safe(request.form.get('name'))
        item = Item(id = url_safe_name)
        
    item.populate(
        name = request.form.get('name'),
        description = request.form.get('description'),
        count = int(request.form.get('count')) if request.form.get('count') else 1,

        price_int = float(request.form.get('price_int')) if request.form.get('price_int') else -1,
        price_ext = float(request.form.get('price_ext')) if request.form.get('price_ext') else -1,
        price_com = float(request.form.get('price_com')) if request.form.get('price_com') else -1,
        price_buy = float(request.form.get('price_buy')) if request.form.get('price_buy') else -1,

        tax_per_day = True if request.form.get('tax_per_day')==1 else False,
        category = request.form.get('category'),
        )
    id = item.put().id()
    '''
    import pdb
    pdb.set_trace()
    file = request.files['image']
    if file:
        import os
        filename = secure_filename(id)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'originals', filename))
        import Image as i
        image = i.open(file)
        image.thumbnail((140,140),True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), "jpg")

    '''
    flash('%s gesichert.'%item.name, 'success')
    return list()


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            flash(u'Ungültiger Name!', 'error')
        elif request.form['password'] != app.config['PASSWORD']:
            flash(u'Ungültiges Kennwort!', 'error')
        else:
            session['logged_in'] = True
            flash('Du bist jetzt angemeldet.')
            return redirect(url_for('show_things'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('show_things'))




def warmup():
    """App Engine warmup handler
    See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests

    """
    return ''


# App Engine warm up handler
# See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests
app.add_url_rule('/_ah/warmup', 'warmup', view_func=warmup)

'''
## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
'''
