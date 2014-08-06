"""
models.py
Sqlite datastore models

"""

from application import db
from flask import session

# Categories for items
CATEGORIES = ['all', 'outdoor','indoor','vehicle','merchandise', 'machines']

class Item(db.Model):
    '''An item that can be bought or borrowed'''
    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.Unicode(), unique=True)
    description = db.Column(db.UnicodeText)
    count = db.Column(db.Integer, default=1)
    # The corresponding image is saved saved under uploads/<entity.id>.jpg

    price_int = db.Column(db.Float)
    price_ext = db.Column(db.Float)
    price_com = db.Column(db.Float)
    price_buy = db.Column(db.Float)
    tax_per_day = db.Column(db.Boolean(), default=False) # taxing option for e.g. cars

    category = db.Column(db.Enum(*CATEGORIES))
    #related = relationship('Item', order_by='Item.id')


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
        return self.price_buy != -1


    def lendable(self):
        return self.price_int != -1 or \
                   self.price_ext != -1 or \
                   self.price_com != -1


class Lend(db.Model):
    ''' Whenever an item is borrowed or bought, a lend entity is created '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    email = db.Column(db.Unicode())
    tel = db.Column(db.Unicode())
    group = db.Column(db.Unicode())
    payment = db.Column(db.Unicode())
    delivery = db.Column(db.Unicode()) # Address
    remarks = db.Column(db.UnicodeText())

    #items = ndb.KeyProperty(kind='Item', repeated=True)
    #item_amounts = ndb.IntegerProperty(repeated=True)

    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    date = db.Column(db.DateTime)

