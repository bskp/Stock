"""
models.py
Sqlite datastore models

"""

from application import db
from flask import session

# Enums
CATEGORIES = ['all', 'outdoor','indoor','vehicle','merchandise', 'machines']
PROGRESS = ['new', 'confirmed', 'returned']


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
        return self.price_buy is not None

    def price_lend(self):
        group = 'int'
        if 'group' in session:
            group = session['group']
        return getattr(self, 'lend_w_'+group)


    def tax_per_day(self):
        group = 'int'
        if 'group' in session:
            group= session['group']
        return getattr(self, 'lend_d_'+group) is not None


    def lendable(self):
        return self.price_lend() is not None


itemlist = db.Table('itemlist',
    db.Column('item_id', db.String(), db.ForeignKey('item.id')),
    db.Column('lend_id', db.Integer, db.ForeignKey('lend.id')),
)


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

    progress = db.Column(db.Enum(*PROGRESS), default='new')

    lend = db.relationship('Item', secondary=itemlist,
            backref=db.backref('lent', lazy='dynamic'))
    buy  = db.relationship('Item', secondary=itemlist,
            backref=db.backref('bought', lazy='dynamic'))

    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    date = db.Column(db.DateTime)

