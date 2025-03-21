from binascii import unhexlify

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_otp.models import Device, ThrottlingMixin
from django_otp.oath import totp
from django_otp.util import hex_validator, random_hex
from phonenumber_field.modelfields import PhoneNumberField

from two_factor.gateways import make_call, send_sms

from two_factor.fields import EncryptedPhoneNumberField

PHONE_METHODS = (
    ('call', _('Phone Call')),
    ('sms', _('Text Message')),
)


def key_validator(*args, **kwargs):
    """Wraps hex_validator generator, to keep makemigrations happy."""
    return hex_validator()(*args, **kwargs)


class PhoneDevice(ThrottlingMixin, Device):
    """
    Model with phone number and token seed linked to a user.
    """
    class Meta:
        db_table = 'two_factor_phonedevice'

    number = EncryptedPhoneNumberField()
    key = models.CharField(max_length=40,
                           validators=[key_validator],
                           default=random_hex,
                           help_text="Hex-encoded secret key")
    method = models.CharField(max_length=4, choices=PHONE_METHODS,
                              verbose_name=_('method'))

    def __repr__(self):
        return '<PhoneDevice(number={!r}, method={!r}>'.format(
            self.number,
            self.method,
        )

    @property
    def bin_key(self):
        return unhexlify(self.key.encode())

    def validate_token(self, token):
        # local import to avoid circular import
        from two_factor.utils import totp_digits

        try:
            token = int(token)
        except ValueError:
            return False

        for drift in range(-5, 1):
            if totp(self.bin_key, drift=drift, digits=totp_digits()) == token:
                return True
        return False

    def verify_token(self, token):
        # If the PhoneDevice doesn't have an id, we are setting up the device,
        # therefore the throttle is not relevant.
        commit_throttle = False
        if self.id:
            commit_throttle = True
        verify_allowed, _ = self.verify_is_allowed()

        if verify_allowed:
            verified = self.validate_token(token)
            if verified:
                self.throttle_reset(commit=commit_throttle)
            else:
                self.throttle_increment(commit=commit_throttle)
        else:
            verified = False

        return verified

    def generate_challenge(self):
        # local import to avoid circular import
        from two_factor.utils import totp_digits

        """
        Sends the current TOTP token to `self.number` using `self.method`.
        """
        verify_allowed, _ = self.verify_is_allowed()
        if not verify_allowed:
            return None

        no_digits = totp_digits()
        token = str(totp(self.bin_key, digits=no_digits)).zfill(no_digits)
        if self.method == 'call':
            make_call(device=self, token=token)
        else:
            send_sms(device=self, token=token)

    def get_throttle_factor(self):
        return getattr(settings, 'TWO_FACTOR_PHONE_THROTTLE_FACTOR', 1)
