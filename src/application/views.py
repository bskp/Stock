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


def calendar(month_offset=0):
    today = datetime.date.today()
    month = today.month-1 + month_offset
    year = today.year + month/12
    month = month % 12 +1
    day1 = datetime.date(year, month, 1)  # 1. of current month
    day1 = day1 - datetime.timedelta(7)  # Go back a week
    while day1.weekday():  # Monday -> 0
        day1 = day1 + datetime.timedelta(1)
    
    days = []
    for dt in range(7*6):  # Generate days for six weeks
        d = day1 + datetime.timedelta(dt)
        day = {}
        import random
        in_stock = random.randint(0,2)

        day['weekday'] = d.weekday()
        day['nr'] = d.day
        day['month'] = d.strftime(u'%B %Y'.encode('utf-8')).decode('utf-8')
        day['title'] = u'%u Stück' % in_stock
        day['class'] = 'blur' if not d.month == month else ''
        day['class'] += ' today' if d == today else ''
        day['class'] += ' out' if not in_stock else ''

        days += day,
    return days


def session_or_empty(key):
    if key in session:
        return session[key]
    return []


@app.before_request
def create_transaction():
    ta = Transaction()

    lending = session_or_empty('lend')
    buying = session_or_empty('buy')

    ta.group = session_or_empty('group')
    if ta.group == []:
        ta.group = 'int'

    for id in lending:
        item = Item.query.get(id)
        ta.lend[id] = Lend(item, lending[id])

    for id in buying:
        item = Item.query.get(id)
        ta.buy[id] = Buy(item, buying[id])

    ta.date_start = session_or_empty('date_start')
    ta.date_end = session_or_empty('date_end')

    g.ta = ta


@app.after_request
def dump_transaction(response):
    ta = g.ta

    session['lend'] = {id: ta.lend[id].amount for id in ta.lend}
    session['buy'] = {id: ta.buy[id].amount for id in ta.buy}

    session['date_start'] = datetime.datetime.combine(ta.date_start, datetime.time())
    session['date_end'] = datetime.datetime.combine(ta.date_end, datetime.time())

    session['group'] = ta.group

    return response


def pjax(template, **kwargs):
    '''Determine whether the request was made by PJAX.'''

    category=''
    if 'category' in session:
        category = session['category']
        items = Item.query.filter_by(category=category)
    else:
        items = Item.query.order_by('name').all()


    ta = g.ta

    if ta.group and not 'logged_in' in session:
        items = filter(lambda i: i.buyable or i.lendable, items)

    if ta.date_start and ta.date_end:
        #items = filter(Item.in_stock, items)
        pass

    kwargs['logged_in'] = 'logged_in' in session

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
    ''' Decorator for protected views. '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'logged_in' in session:
            flash(u'Du bist nicht angemeldet!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def list():
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
    g.ta.group= group
    return list()


@app.route('/filter/between/<string:start>/and/<string:end>')
def date_filter(start, end):
    ta = g.ta

    # Provide parsing to epoch-ts
    def parse_date(string):
        return datetime.datetime.strptime(string, '%d._%b_%Y')

    ta.date_start = parse_date(start)
    ta.date_end = parse_date(end)

    # Enforce date order
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
        flash('%s nicht eingepackt'%id, 'error')
        return item(id)

    ta.lend[id].amount -= 1

    if ta.lend[id].amount == 0:
        ta.lend.pop(id)
    return item(id)


@app.route('/item/<id>/unbuy')
def item_unbuy(id):
    ta = g.ta

    if not id in ta.buy or ta.buy[id].amount < 1:
        flash('%s nicht eingepackt'%id, 'error')
        return item(id)

    ta.buy[id].amount -= 1

    if ta.buy[id].amount == 0:
        ta.buy.pop(id)
    return item(id)
    

@app.route('/cart/empty')
def cart_empty():
    g.ta.lend.clear()
    g.ta.buy.clear()

    return list()


@app.route('/cart/checkout')
def cart_checkout():

    # TODO read and set a cookie for 
    # name, address, email, phone, group

    ta = g.ta

    if ta.lend and not ta.date_start and not ta.date_end:
        flash(u'Gib einen Zeitraum für deine Bestellung an ("verfügbar vom…")', 'error')
        return list()

    return pjax('checkout.html')


@app.route('/cart/submit', methods=['POST'])
def cart_submit():
    ta = g.ta

    ta.name = request.form.get('name')
    ta.email = request.form.get('email')
    ta.tel = request.form.get('tel')
    ta.payment = request.form.get('payment')
    ta.delivery = request.form.get('delivery')
    ta.remarks = request.form.get('remarks')

    db.session.add(ta)
    db.session.commit()

    flash(u'Danke für deine Bestellung!')
    return cart_empty()
    


@app.route('/item/<id>', methods=['GET'])
def item(id):
    item = Item.query.get_or_404(id)
    return pjax('detail.html',
                item=item,
               ) 


@app.route('/item/<id>/stock', methods=['GET'])
def check_stock(id):
    item = Item.query.get_or_404(id)

    months = []
    for m in range(6):
        months += calendar(m),

    return pjax('stock.html',
                item=item,
                months=months,
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
        # The following attributes are needed to show this dummy-item
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

    request_or_none = lambda key: float(request.form.get(key)) if request.form.get(key) else None

    item.tax_base_int = request_or_none('tax_base_int')
    item.tax_base_edu = request_or_none('tax_base_edu')
    item.tax_base_ext = request_or_none('tax_base_ext')
    item.tax_int = request_or_none('tax_int')
    item.tax_edu = request_or_none('tax_edu')
    item.tax_ext = request_or_none('tax_ext')

    item.tax_period = request.form.get('tax_period')

    item.price_buy = request_or_none('price_buy')

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
    transactions = Transaction.query.all()
    return pjax('admin.html', transactions=transactions)


@app.route('/admin/<id>')
@login_required
def admin_transaction(id):
    transactions = Transaction.query.all()
    return pjax('admin_transaction.html',
                transactions=transactions,
                eta=Transaction.query.get(id)
                )



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
