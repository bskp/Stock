"""
models.py
Sqlite datastore models

"""

from application import db
from flask import session

# Enums
CATEGORIES = ['all', 'outdoor','indoor','vehicle','merchandise', 'machines']
PROGRESS = ['new', 'confirmed', 'returned']


related = db.Table('related',
    db.Column('item_id', db.String(), db.ForeignKey('item.id')),
    db.Column('related_item_id', db.String(), db.ForeignKey('item.id')),
)

class Item(db.Model):
    '''An item that can be bought or borrowed'''
    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.Unicode(), unique=True)
    description = db.Column(db.UnicodeText)
    count = db.Column(db.Integer, default=1)
    # The corresponding image is saved saved under uploads/<entity.id>.jpg

    lend_w_int = db.Column(db.Float)
    lend_w_edu = db.Column(db.Float)
    lend_w_ext = db.Column(db.Float)

    lend_d_int = db.Column(db.Float)
    lend_d_edu = db.Column(db.Float)
    lend_d_ext = db.Column(db.Float)
    
    price_buy = db.Column(db.Float)

    category = db.Column(db.Enum(*CATEGORIES))
    related = db.relationship('Item', secondary=related,
                        primaryjoin=id==related.c.item_id,
                        secondaryjoin=id==related.c.related_item_id,)


    def __repr__(self):
        return u"<Item %s>" % (self.id)


    def in_stock(self):
        return self.count - 0#TODO amount lent during session timespan


    def buying(self):
        if not 'buy' in session:
            return 0
        if not self.id in session['buy']:
            return 0
        return session['buy'][self.id]


    def lending(self):
        if not 'lend' in session:
            return 0
        if not self.id in session['lend']:
            return 0
        return session['lend'][self.id]


    def available(self):
        return self.in_stock() - self.buying() - self.lending()


    def buyable(self):
        return self.price_buy is not None


    def price_lend_w(self):
        group = 'int'
        if 'group' in session:
            group = session['group']
        return getattr(self, 'lend_w_'+group)


    def price_lend_d(self):
        group = 'int'
        if 'group' in session:
            group = session['group']
        return getattr(self, 'lend_d_'+group)


    def price_lend(self, days):
        from math import ceil

        d = self.price_lend_d()
        w = self.price_lend_w()
        n = 7  # days of second tax-value

        if d is None:
            # Simple taxing
            weeks = int(ceil(days/7.0))
            return weeks*self.price_lend_w()

        # Day-based taxing
        price = (w-d)/(n-1) * (days-1) + d
        return ceil(price)


    def tax_per_day(self):
        group = 'int'
        if 'group' in session:
            group= session['group']
        return getattr(self, 'lend_d_'+group) is not None


    def lendable(self):
        return self.price_lend_w() is not None


'''
lendlist = db.Table('lendlist',
    db.Column('item_id', db.String(), db.ForeignKey('item.id')),
    db.Column('transaction_id', db.Integer, db.ForeignKey('transaction.id')),
)

buylist = db.Table('buylist',
    db.Column('item_id', db.String(), db.ForeignKey('item.id')),
    db.Column('transaction_id', db.Integer, db.ForeignKey('transaction.id')),
)
'''


class Itemlist(db.Model):
    ta_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)

    buy = db.Column(db.Integer, default=0)
    lend = db.Column(db.Integer, default=0)

    item = db.relationship("Item")


class Transaction(db.Model):
    ''' Whenever an item is lent or bought, a transaction entity is created '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    email = db.Column(db.Unicode())
    tel = db.Column(db.Unicode())
    group = db.Column(db.Unicode())
    payment = db.Column(db.Unicode())
    delivery = db.Column(db.Unicode()) # Address
    remarks = db.Column(db.UnicodeText())

    progress = db.Column(db.Enum(*PROGRESS), default='new')

    items = db.relationship("Itemlist")

    '''
    lend = db.relationship('Item', secondary=lendlist,
            backref=db.backref('lent', lazy='dynamic'))
    buy  = db.relationship('Item', secondary=buylist,
            backref=db.backref('bought', lazy='dynamic'))
    '''

    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    date = db.Column(db.DateTime)


    def __repr__(self):
        if self.id is not None:
            return u"<Transaction %u>" % (self.id)
        return u"<Transaction (no ID)>"
