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

    # Prices order as follows: Jubla-internal, other organisations,
    # commercial organisations, price to buy (merch only).
    # If some are omitted, the last given amount is repeated
    prices = ndb.FloatProperty(repeated=True)

    tax_per_day = ndb.BooleanProperty() # taxing option for e.g. cars
    category = ndb.StringProperty(choices=CATEGORIES)

    def __repr__(self):
        return u"<Item %s>" % (self.key.id())


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

