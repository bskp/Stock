# coding=utf-8
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


def session_or_empty(key):
    if key in session:
        return session[key]
    return ''


def available_between(item):
    # TODO filter out unavailable items
    return True


def pjax(template, **kwargs):
    '''Determine whether the request was made by PJAX.'''

    if 'category' in session:
        items = Item.query.filter_by(category=session['category'])
    else:
        items = Item.query.all()


    if 'from_ts' and 'until_ts' in session:
        start = session['from_ts']
        end = session['until_ts']

        items = filter(available_between, items)

    buy = session_or_empty('buy')
    buy = sum(buy.values()) if buy else 0
    lend = session_or_empty('lend')
    lend = sum(lend.values()) if lend else 0
    kwargs['n_in_cart'] = lend+buy

    date_from = session_or_empty('from')
    date_until = session_or_empty('until')

    if "X-PJAX" in request.headers:
        return render_template(template, items=items, date_from=date_from, date_until=date_until, **kwargs)
    
    return render_template('base.html',
                           template = template,
                           items=items,
                           date_from=date_from,
                           date_until=date_until,
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
def list():
    ''' Generic listing function, called by every other pre-filtering
    listers (see below).'''

    return pjax('content.html')


@app.route('/filter/category/<string:category>')
def cat_filter(category):
    if not category in CATEGORIES:
        flash(u'Kategorie ungültig!', 'error')
    session['category'] = category
    if category == 'all':
        session.pop('category')
    return list()


@app.route('/filter/between/<string:start>/and/<string:end>')
def date_filter(start='', end=''):
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
    return list()


@app.route('/filter/none')
def clear_filter():
    session.pop('from', None)
    session.pop('from_ts', None)
    session.pop('until', None)
    session.pop('until_ts', None)
    session.pop('category', None)

    #return redirect(url_for('list'))
    return list()


@app.route('/item/<id>/lend')
def item_lend(id):
    if not 'lend' in session:
        session['lend'] = {}
    if not id in session['lend']:
        session['lend'][id] = 0
    session['lend'][id] += 1
    flash('%s eingepackt.'%id, 'success')
    return item(id)
    

@app.route('/item/<id>/buy')
def item_buy(id):
    if not 'buy' in session:
        session['buy'] = {}
    if not id in session['buy']:
        session['buy'][id] = 0
    session['buy'][id] += 1
    flash('%s eingepackt.'%id, 'success')
    return item(id)


@app.route('/item/<id>/unlend')
def item_unlend(id):
    if not 'lend' in session:
        session['lend'] = {}
    session['lend'][id] -= 1
    if session['lend'][id] < 0:
        session['lend'][id] = 0
    return item(id)


@app.route('/item/<id>/unbuy')
def item_unbuy(id):
    if not 'buy' in session:
        session['buy'] = {}
    session['buy'][id] -= 1
    if session['buy'][id] < 0:
        session['buy'][id] = 0
    return item(id)
    

@app.route('/cart/empty')
def cart_empty():
    session.pop('buy', None)
    session.pop('lend', None)
    return list()


@app.route('/cart/checkout')
def cart_checkout():
    lend = session_or_empty('lend')
    buy = session_or_empty('buy')
    if not 'from' in session and lend and sum(lend.values()):
        flash(u'Gib einen Zeitraum für deine Bestellung an ("verfügbar vom…")', 'error')
        return list()
    
    items = Item.query.all()
    items = {i.id: i for i in items}

    lend = {items[i]: lend[i] for i in lend if lend[i]>0}
    buy  = {items[i]: buy[i] for i in buy if buy[i]>0}

    sum_lend = sum( [i.price_int*lend[i] for i in lend] )
    sum_buy = sum( [i.price_buy*buy[i] for i in buy] )

    return pjax('checkout.html',
                lend=lend,
                buy=buy,
                sum_lend=sum_lend,
                sum_buy=sum_buy,
                )

@app.route('/cart/submit', methods=['POST'])
def cart_submit():
    flash(u'Danke für deine Bestellung!')
    return list()
    #return pjax('.html')
    


@app.route('/item/<id>', methods=['GET'])
def item(id):
    return pjax('detail.html',
                item=Item.query.get_or_404(id),
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
