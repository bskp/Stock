# coding=latin-1
"""
views.py

Route handlers for HTML

"""

from flask import request, render_template, flash, url_for, redirect, send_from_directory, session
from werkzeug import secure_filename

from application import app, make_url_safe, db
from models import Item, Lend, CATEGORIES

from functools import wraps

import locale
locale.setlocale(locale.LC_ALL, 'de_CH')
import time

def pjax(template, query=None, **kwargs):
    '''Determine whether the request was made by PJAX.'''

    if not query:
        items = Item.query.all()
    else:
        items = query

    if "X-PJAX" in request.headers:
        return render_template(template, items=items, **kwargs)
    

    return render_template('base.html',
                           template = template,
                           items=items,
                           date_from=session['from'],
                           date_until=session['until'],
                           **kwargs
                           )

def login_required(f):
    ''' Wrapper for protected views. '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        '''
        if not 'logged_in' in session:
            return redirect(url_for('login', next=request.url))
        '''
        flash(u'Geschützte Aktion', 'error')
        return f(*args, **kwargs)
    return decorated_function



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
        flash(u'Kategorie ungültig!', 'error')
    query = Item.query.filter_by(category=category)
    return list(query)


@app.route('/ignore_availability')
@app.route('/available/between/<string:start>/and/<string:end>')
def set_timespan(start='', end=''):
    print "set time! from %s to %s" % (start, end)
    session['from'] = start
    session['until'] = end

    # Provide parsing to epoch-ts
    if start and end:
        def parse_date(str):
            t = time.strptime(str, '%d._%b_%Y')
            return time.mktime(t)
        session['from_ts'] = parse_date(start)
        session['until_ts'] = parse_date(end)
    else:
        session['from_ts'] = None
        session['until_ts'] = None

    return redirect(url_for('list'))


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


@app.route('/item/<id>', methods=['GET'])
def item(id):
    if request.method == 'GET':
        return pjax('detail.html',
                    item=Item.query.get_or_404(id),
                    in_cart = session.get(id),
                   ) 

@app.route('/item/<id>/edit', methods=['GET', 'POST'])
def item_edit(id):
    return item_create(id)

@app.route('/item/<id>/destroy', methods=['GET', 'POST'])
@login_required
def item_destroy(id):
    item = Item.query.get_or_404(id)

    # TODO: check dependencies

    db.session.delete(item)
    db.session.commit()

    flash(u'%s gelöscht.'%id, 'success')
    return redirect(url_for('list'))

@app.route('/item_create', methods=['GET', 'POST'])
@login_required
def item_create(replace=None):
    if replace:
        item = Item.query.get_or_404(replace)
    else:
        item = None

    # Require form
    if request.method == 'GET':
        return pjax('create_item.html', item=item)
    # else POST: save to db
    if not item:
        replace = make_url_safe(request.form.get('name'))
        item = Item(id=replace)
        db.session.add(item)
        
    item.name = request.form.get('name')
    item.description = request.form.get('description')
    item.count = int(request.form.get('count')) if request.form.get('count') else 1

    item.price_int = float(request.form.get('price_int')) if request.form.get('price_int') else -1
    item.price_ext = float(request.form.get('price_ext')) if request.form.get('price_ext') else -1
    item.price_com = float(request.form.get('price_com')) if request.form.get('price_com') else -1
    item.price_buy = float(request.form.get('price_buy')) if request.form.get('price_buy') else -1

    item.tax_per_day = True if request.form.get('tax_per_day')==1 else False
    item.category = request.form.get('category')

    db.session.commit()

    file = request.files['image']
    if file:
        import os
        from PIL import Image as i
        filename = secure_filename(replace) + '.jpg'

        image = i.open(file)
        if image.mode != "RGB":
            image = image.convert("RGB")

        image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'full', filename), "jpeg")

        w  = image.size[0]
        h = image.size[1]

        aspect = w / float(h)
        ideal_aspect = 1.0

        if aspect > ideal_aspect:  # Then crop the left and right edges:
            w_ = int(ideal_aspect * h)
            offset = (w - w_)/2
            resize = (offset, 0, w - offset, h)
        else:  # ... crop the top and bottom:
            h_ = int(w/ideal_aspect)
            offset = (h - h_)/2
            resize = (0, offset, w, h - offset)

        image = image.crop(resize).resize((140, 140), i.ANTIALIAS)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), "jpeg")

    flash('%s gesichert.'%item.name, 'success')
    return list()


@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/<path:next>', methods=['GET', 'POST'])
def login(next=''):
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            flash(u'Ungültiger Name!', 'error')
        elif request.form['password'] != app.config['PASSWORD']:
            flash(u'Ungültiges Kennwort!', 'error')
        else:
            session['logged_in'] = True
            flash('Du bist jetzt angemeldet.')
            return redirect(next)
    return pjax('login.html', next=next)


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('list'))


@app.route('/uploads/<path:filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

## Error handlers
# Handle 404 errors
'''
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
'''
