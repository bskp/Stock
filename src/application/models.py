"""
models.py
App Engine datastore models

"""


from google.appengine.ext import ndb


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
    category = ndb.StringProperty(choices=['outdoor','indoor','vehicle','merchandise', 'machines'])

    def __repr__(self):
        return "<Item %s>" % (self.name)


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


class ExampleModel(ndb.Model):
    """Example Model"""
    example_name = ndb.StringProperty(required=True)
    example_description = ndb.TextProperty(required=True)
    added_by = ndb.UserProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
