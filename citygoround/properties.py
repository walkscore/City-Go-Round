from decimal import Decimal
from google.appengine.ext import db

class DecimalProperty(db.Property):
    data_type = Decimal

    def get_value_for_datastore(self, model_instance):
        return str(super(DecimalProperty, self).get_value_for_datastore(model_instance))

    def make_value_from_datastore(self, value):
        if (value is None) or (value == str(None)):
            # Deal cleanly with out-of-date transit apps.
            return None
        else:
            return Decimal(value)
        
    def validate(self, value):
        value = super(DecimalProperty, self).validate(value)
        if value is None or isinstance(value, Decimal):
            return value
        elif isinstance(value, basestring):
            return Decimal(value)
        raise db.BadValueError("Property %s must be a Decimal or string." % self.name)

