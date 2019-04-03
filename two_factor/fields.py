import copy

from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings

from pfc import utils

class EncryptedPhoneNumberField(PhoneNumberField):
    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            return utils.decrypt(value, settings.MASTER_KEY)
        except:
            return ''

    def get_db_prep_value(self, value, connection, prepared=False):
        if value == None:
            return value

        db_value = copy.deepcopy(value)

        return utils.encrypt(str(db_value), settings.MASTER_KEY)
