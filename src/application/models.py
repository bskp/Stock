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
    ''' An item that can be bought or borrowed
        Some methods require the request-context.
        TODO: Proper context validation with exceptions et al.'''

    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.Unicode(), unique=True)
    description = db.Column(db.UnicodeText)
    count = db.Column(db.Integer, default=1)
    # The corresponding image is saved saved under uploads/<entity.id>.jpg

    tax_base_int = db.Column(db.Float, default=0)
    tax_base_edu = db.Column(db.Float, default=0)
    tax_base_ext = db.Column(db.Float, default=0)

    tax_int = db.Column(db.Float)
    tax_edu = db.Column(db.Float)
    tax_ext = db.Column(db.Float)

    tax_period = db.Column(db.Enum('week', 'day'), default='week')
    
    price_buy = db.Column(db.Float)

    category = db.Column(db.Enum(*CATEGORIES))
    related = db.relationship('Item', secondary=related,
                        primaryjoin=id==related.c.item_id,
                        secondaryjoin=id==related.c.related_item_id,)


    def __repr__(self):
        return u"<Item %s>" % (self.id)


    @property
    def in_stock(self):
        ''' Returns the amount of this item in stock during the selected time-
            span. 
        '''
        return self.count - 0#TODO amount lent during session timespan


    @property
    def buying(self):
        ta = g.ta
        if not self.id in ta.buy:
            return 0
        return ta.buy[self.id].amount


    @property
    def lending(self):
        ta = g.ta
        if not self.id in ta.lend:
            return 0
        return ta.lend[self.id].amount


    @property
    def available(self):
        return self.in_stock - self.buying - self.lending


    @property
    def lendable(self):
        return self.tax is not None


    @property
    def buyable(self):
        return self.price_buy is not None


    @property
    def tax_base(self):
        ta = g.ta
        return getattr(self, 'tax_base_'+ta.group)


    @property
    def tax(self):
        ta = g.ta
        return getattr(self, 'tax_'+ta.group)


    def tax_total(self, days):
        from math import ceil
        if self.tax_period == 'week':
            periods = int(ceil(days/7.0))
        else:
            periods = days

        return self.tax_base + periods*self.tax



class Buy(db.Model):
    ta_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)

    amount = db.Column(db.Integer)
    item = db.relationship('Item', backref='bought')
    cost = db.Column(db.Float)  # Possibility to override the cost


    def cost(self):
        #TODO respect cost-column
        return self.amount*self.item.price_buy

    def __init__(self, item, amount=1):
        self.item=item
        self.amount=amount

    def __repr__(self):
        return '<%ux %s>' % (self.amount, self.item.id)
    


class Lend(db.Model):
    ta_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)

    amount = db.Column(db.Integer)
    item = db.relationship('Item', backref='lent')
    cost = db.Column(db.Float)


    def cost(self, days):
        #TODO respect cost-column
        return self.amount*self.item.tax_total(days)


    def __init__(self, item, amount=1):
        self.item=item
        self.amount=amount

    def __repr__(self):
        return '<%ux %s>' % (self.amount, self.item.id)



class Transaction(db.Model):
    ''' Whenever an item is lent or bought, a transaction entity is created '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    email = db.Column(db.Unicode())
    tel = db.Column(db.Unicode())
    group = db.Column(db.Enum('int', 'edu', 'ext'))
    payment = db.Column(db.Unicode())
    delivery = db.Column(db.Unicode()) # Address
    remarks = db.Column(db.UnicodeText())

    progress = db.Column(db.Enum(*PROGRESS), default='new')

    buy = db.relationship('Buy', backref='transaction', collection_class=attribute_mapped_collection('item_id'),)
    lend = db.relationship('Lend', backref='transaction', collection_class=attribute_mapped_collection('item_id'),)

    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    date = db.Column(db.DateTime)

    
    @property
    def days(self):
        if not self.date_end or not self.date_start:
            return 0
        return (self.date_end-self.date_start).days
        

    @property
    def weeks(self):
        from math import ceil
        return int(ceil(self.days/7.0))


    @property
    def n_in_cart(self):

        lend = [item.amount for item in self.lend.values()]
        buy = [item.amount for item in self.buy.values()]

        return sum(lend) + sum(buy)


    @property
    def cost(self):
        lends = [il.cost(self.days) for il in self.lend.values()]
        buys = [il.cost() for il in self.buy.values()]
        return sum(lends) + sum(buys)


    def __init__(self):
        self.group = 'int'
        self.date = datetime.datetime.utcnow()


    def __repr__(self):
        if self.id is not None:
            return u"<Transaction %u>" % (self.id)
        return u"<Transaction (no ID)>"
