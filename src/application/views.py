# coding=utf-8
"""
views.py

Route handlers for HTML

"""

from flask import request, render_template, flash, url_for, redirect, send_from_directory, session, g
from werkzeug import secure_filename

from application import app, make_url_safe, db
from models import Item, Transaction, Buy, Lend, CATEGORIES, PROGRESS

from functools import wraps

import datetime
import uuid


'''
def cleanup_g():
    '' Deletes old transaction instances in g ''

    if not 'transactions' in g:
        return

    now = datetime.datetime.utcnow()
    for tr_hash in g.transactions:
        ta = g.transactions[tr_hash]
        print '%s: %s' % (tr_hash, now-ta.date)

        if (now-ta.date).days > 3:
            g.transactions.pop(tr_hash)
'''

@app.before_request
def fetch_transaction():
    from flask import session

    if not 'tr_hash' in session \
    or not hasattr(app, 'transactions') \
    or not session['tr_hash'] in app.transactions:
        tr_hash = uuid.uuid4()
        session['tr_hash'] = tr_hash

        if not hasattr(app, 'transactions'):
            app.transactions = {}

        app.transactions[tr_hash] = Transaction()
        print 'Added transaction hash %s' % tr_hash
        flash(u'New transaction', 'notice')
    else:
        print 'Fetched transaction %s' % session['tr_hash']

    g.ta = app.transactions[session['tr_hash']]

    from pprint import pprint
    pprint(g.ta.lend)
    pprint(g.ta.buy)

def available_between(item):
    # TODO filter out unavailable items
    return True


def pjax(template, **kwargs):
    '''Determine whether the request was made by PJAX.'''

    category=''
    if 'category' in session:
        category = session['category']
        items = Item.query.filter_by(category=category)
    else:
        items = Item.query.order_by('name').all()


    ta = g.ta

    if ta.group:
        items = filter(lambda i: i.buyable() or i.lendable(), items)

    if ta.date_start and ta.date_end:
        items = filter(available_between, items)

    kwargs['logged_in'] = hasattr(session, 'logged_in')

    if "X-PJAX" in request.headers:
        return render_template(template, items=items, ta=ta, **kwargs)
    
    return render_template('base.html',
                           template = template,
                           items=items,
                           category=category,
                           ta=ta,
                           **kwargs
                           )


def login_required(f):
    ''' Wrapper for protected views. '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'logged_in' in session:
            flash(u'Du bist nicht angemeldet!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def list():
    ''' Generic listing function, called by every other pre-filtering
    listers (see below).'''

    return pjax('content.html')


@app.route('/filter/category/<string:category>')
def cat_filter(category):
    if category == 'all':
        session.pop('category')
        return list()
    if not category in CATEGORIES:
        flash(u'Kategorie ungültig!', 'error')
    session['category'] = category
    return list()


@app.route('/filter/group/<string:group>')
def group_filter(group):
    session['transaction'].group = group
    return list()


@app.route('/filter/between/<string:start>/and/<string:end>')
def date_filter(start, end):
    ta = g.ta

    # Provide parsing to epoch-ts
    def parse_date(string):
        return datetime.datetime.strptime(string, '%d._%b_%Y')

    ta.date_start = parse_date(start)
    ta.date_end = parse_date(end)

    # Apply causality
    if ta.date_start > ta.date_end:
        ta.date_start, ta.date_end = ta.date_end, ta.date_start

    return list()


@app.route('/filter/none')
def clear_filter():
    session.pop('category', None)
    ta = g.ta
    ta.date_start = None
    ta.date_end = None
    
    #return redirect(url_for('list'))
    return list()


@app.route('/item/<id>/lend')
def item_lend(id):
    ta = g.ta

    if id in ta.lend:
        ta.lend[id].amount += 1

    else:
        it= Item.query.get(id)
        ta.lend[id] = Lend(it)

    flash('%s eingepackt.'%id, 'success')
    return item(id)
    

@app.route('/item/<id>/buy')
def item_buy(id):
    ta = g.ta

    if id in ta.buy:
        ta.buy[id].amount += 1

    else:
        it= Item.query.get(id)
        ta.buy[id] = Buy(it)

    flash('%s eingepackt.'%id, 'success')
    return item(id)


@app.route('/item/<id>/unlend')
def item_unlend(id):
    ta = g.ta

    if not id in ta.lend or ta.lend[id].amount < 1:
        flash('%s nicht eingepackt', 'error')
        return item(id)

    ta.lend[id].amount -= 1
    return item(id)


@app.route('/item/<id>/unbuy')
def item_unbuy(id):
    ta = g.ta

    if not id in ta.buy or ta.buy[id].amount < 1:
        flash('%s nicht eingepackt', 'error')
        return item(id)

    ta.buy[id].amount -= 1
    return item(id)
    

@app.route('/cart/empty')
def cart_empty():
    ta = g.ta
    ta.lend = {}
    ta.buy = {}

    return list()


@app.route('/cart/checkout')
def cart_checkout():

    # read and set a cookie for 
    # name, address, email, phone, group

    '''
    lend = session_or_empty('lend')
    buy = session_or_empty('buy')

    days=0
    weeks=0
    if 'from' in session:
        # Calculate lend duration
        from datetime import date
        from math import ceil
        start = date.fromtimestamp(session['from_ts'])
        end = date.fromtimestamp(session['until_ts'])
        days = (end-start).days+1
        weeks = int(ceil(days/7.0))

    elif lend and sum(lend.values()):
        flash(u'Gib einen Zeitraum für deine Bestellung an ("verfügbar vom…")', 'error')
        return list()
    
    items = Item.query.all()
    items = {i.id: i for i in items}

    lend = {items[i]: lend[i] for i in lend if lend[i]>0}
    buy  = {items[i]: buy[i] for i in buy if buy[i]>0}

    sum_lend = sum( [i.price_lend(days)*lend[i] for i in lend] )
    sum_buy = sum( [i.price_buy*buy[i] for i in buy] )
    total = sum_lend+sum_buy

    return pjax('checkout.html',
                lend=lend,
                buy=buy,
                total=total,
                days=days,
                weeks=weeks
                )
    '''
    ta = g.ta

    if ta.lend and not ta.date_start and not ta.date_end:
        flash(u'Gib einen Zeitraum für deine Bestellung an ("verfügbar vom…")', 'error')
        return list()

    return pjax('checkout.html')


@app.route('/cart/submit', methods=['POST'])
def cart_submit():
    # TODO rewrite!
    '''
    lend = session_or_empty('lend')
    buy = session_or_empty('buy')

    ta = Transaction()
    db.session.add(ta)
    
    ta.name = request.form.get('name')
    ta.email = request.form.get('email')
    ta.tel = request.form.get('tel')
    ta.payment = request.form.get('payment')
    ta.delivery = request.form.get('delivery')
    ta.remarks = request.form.get('remarks')

    ta.date_start = datetime.date.fromtimestamp(session['from_ts'])
    ta.date_end = datetime.date.fromtimestamp(session['until_ts'])
    ta.date = datetime.datetime.now()

    items = Item.query.all()
    items = {i.id: i for i in items}

    ta.lend = [Lend(lend[id], items[id]) for id in lend]
    ta.buy = [Buy(buy[id], items[id]) for id in buy]

    db.session.commit()

    '''
    flash(u'Danke für deine Bestellung!')
    return list()
    #return pjax('.html')
    


@app.route('/item/<id>', methods=['GET'])
def item(id):
    return pjax('detail.html',
                item=Item.query.get_or_404(id),
               ) 


@app.route('/item/<id>/destroy', methods=['GET', 'POST'])
@login_required
def item_destroy(id):
    item = Item.query.get_or_404(id)

    # TODO: check dependencies

    db.session.delete(item)
    db.session.commit()

    flash(u'%s gelöscht.'%id, 'success')
    return redirect(url_for('list'))


@app.route('/item_create', methods=['GET'])
@app.route('/item/<id>/edit', methods=['GET'])
@login_required
def item_edit(id=None):
    if id:
        item = Item.query.get_or_404(id)
    else:
        item = Item()
        item.count = 1
        item.name = ''

    # Require form
    if request.method == 'GET':
        return pjax('create_item.html', item=item)


@app.route('/item_update', methods=['POST'])
@app.route('/item/<id>/update', methods=['POST'])
def item_post(id=None):
    if id:
        item = Item.query.get_or_404(id)
    else:
        replace = make_url_safe(request.form.get('name'))
        item = Item(id=replace)
        db.session.add(item)
        
    item.name = request.form.get('name')
    item.description = request.form.get('description')
    item.count = int(request.form.get('count')) if request.form.get('count') else 1

    item.lend_w_int = float(request.form.get('lend_w_int')) if request.form.get('lend_w_int') else None
    item.lend_w_edu = float(request.form.get('lend_w_edu')) if request.form.get('lend_w_edu') else None
    item.lend_w_ext = float(request.form.get('lend_w_ext')) if request.form.get('lend_w_ext') else None

    item.lend_d_int = float(request.form.get('lend_d_int')) if request.form.get('lend_d_int') else None
    item.lend_d_edu = float(request.form.get('lend_d_edu')) if request.form.get('lend_d_edu') else None
    item.lend_d_ext = float(request.form.get('lend_d_ext')) if request.form.get('lend_d_ext') else None

    item.price_buy = float(request.form.get('price_buy')) if request.form.get('price_buy') else None

    item.category = request.form.get('category')

    db.session.commit()

    # Update image if necessary
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
def login():
    from Crypto.Hash import SHA256
    from Crypto.Random import get_random_bytes
    from base64 import b64encode

    if 'logged_in' in session:
        flash('Du bist bereits angemeldet')
        return redirect(url_for('list'))

    if request.method == 'POST':
        challenge = session['challenge']
        hsh_given = request.form['hash']
        h = SHA256.new(challenge+app.config['PASSWORD'])
        hsh_valid = h.hexdigest()

        if hsh_valid == hsh_given:
            session['logged_in'] = True
            flash('Du bist jetzt angemeldet.')
            return redirect(url_for('list'))

        flash(u'Ungültiges Kennwort!', 'error')
    
    challenge = b64encode(get_random_bytes(64))
    session['challenge'] = challenge
    return pjax('login.html', challenge=challenge)


@app.route('/logout')
@login_required
def logout():
    flash('Abgemeldet!')
    session.pop('logged_in', None)
    return redirect(url_for('list'))


@app.route('/admin')
@login_required
def admin():
    1/0
    transactions = Transaction.query.all()
    return pjax('admin.html', transactions=transactions)


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
