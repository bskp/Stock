"""
models.py
Sqlite datastore models

"""

from application import db
from sqlalchemy.orm.collections import attribute_mapped_collection

from flask import g

import datetime


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
        ta = g.ta
        if not self.id in ta.buy:
            return 0
        return ta.buy[self.id].amount


    def lending(self):
        ta = g.ta
        if not self.id in ta.buy:
            return 0
        return ta.lend[self.id].amount


    def available(self):
        return self.in_stock() - self.buying() - self.lending()


    def buyable(self):
        return self.price_buy is not None


    def price_lend_w(self):
        ta = g.ta
        return getattr(self, 'lend_w_'+ta.group)


    def price_lend_d(self):
        ta = g.ta
        return getattr(self, 'lend_d_'+ta.group)


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
        ta = g.ta
        return getattr(self, 'lend_d_'+ta.group) is not None


    def lendable(self):
        return self.price_lend_w() is not None


class Buy(db.Model):
    ta_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)

    amount = db.Column(db.Integer)
    item = db.relationship('Item', backref='bought')
    #cost = db.Column(db.Float)

    def cost(self):
        #TODO respect cost-column
        return self.amount*self.item.price_buy

    def __init__(self, item):
        self.item=item
        self.amount=1

    def __repr__(self):
        return '<%u %s>' % (self.amount, self.item.id)
    

class Lend(db.Model):
    ta_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)

    amount = db.Column(db.Integer)
    item = db.relationship('Item', backref='lent')
    #cost = db.Column(db.Float)


    def cost(self, days):
        #TODO respect cost-column
        return self.amount*self.item.price_lend(days)


    def __init__(self, item):
        self.item=item
        self.amount=1

    def __repr__(self):
        return '<%u %s>' % (self.amount, self.item.id)


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

    buy = db.relationship('Buy', backref='transaction', collection_class=attribute_mapped_collection('item_id'),)
    lend = db.relationship('Lend', backref='transaction', collection_class=attribute_mapped_collection('item_id'),)

    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    date = db.Column(db.DateTime)

    
    def days(self):
        return (self.date_end-self.date_start).days
        

    def weeks(self):
        from math import ceil
        return int(ceil(self.days()/7.0))


    def n_in_cart(self):
        return len(self.buy) + len(self.lend)


    def cost(self):
        lends = [il.cost() for il in self.lend.values()]
        buys = [il.cost() for il in self.buy.values()]
        return sum(lends) + sum(buys)


    def __init__(self):
        self.group = 'int'
        self.date = datetime.datetime.utcnow()


    def __repr__(self):
        if self.id is not None:
            return u"<Transaction %u>" % (self.id)
        return u"<Transaction (no ID)>"
