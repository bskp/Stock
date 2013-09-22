"""
models.py
App Engine datastore models

"""


from google.appengine.ext import ndb

# Categories for items
CATEGORIES = ['outdoor','indoor','vehicle','merchandise', 'machines']

class Item(ndb.Model):
    '''An item that can be bought or borrowed'''
    name = ndb.StringProperty()
    description = ndb.TextProperty()
    count = ndb.IntegerProperty()
    # The corresponding image is saved saved under img/<entity.id>.jpg

    price_int = ndb.FloatProperty()
    price_ext = ndb.FloatProperty()
    price_com = ndb.FloatProperty()
    price_buy = ndb.FloatProperty()

    tax_per_day = ndb.BooleanProperty() # taxing option for e.g. cars
    category = ndb.StringProperty(choices=CATEGORIES)

    def __repr__(self):
        return u"<Item %s>" % (self.key.id())

    def in_stock(self, date):
        ''' Returns the amount in stock on a given date '''
        lends = Lend.query(Lend.date_end < date, Lend.date_start > date).fetch()
        counts = [l.count for l in lends if key.id() in l.items]
        return count - sum(counts)

    def print_prices(self):
        prices = [self.price_int, self.price_ext, self.price_com, self.price_buy]
        prices = map(lambda price: r'<span="price">%s</span>'%price if not price == -1 else '-', prices)
        return '/'.join(prices)
        #return reduce(lambda s, price: s + '<span class="price">%s</span>' if price else '-', self.prices)


class Lend(ndb.Model):
    '''Whenever an item is borrowed or bought, a lend entity is created'''
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    tel = ndb.StringProperty()
    group = ndb.StringProperty(choices=['new', 'confirmed', 'back'])
    payment = ndb.StringProperty(choices=['cash', 'invoice'])
    delivery = ndb.StringProperty() # Address
    remarks = ndb.TextProperty()

    items = ndb.KeyProperty(kind='Item', repeated=True)
    item_amounts = ndb.IntegerProperty(repeated=True)

    date_start = ndb.DateProperty()
    date_end = ndb.DateProperty()
    date = ndb.DateProperty(auto_now_add=True)

