# Generated to align migration state with PhoneDevice.number using
# two_factor.fields.EncryptedPhoneNumberField (see models.py). Without this
# migration, installing this fork on other projects triggers a permanent
# "unapplied" migration warning (models differ from 0001_initial / squashed 0001).

import two_factor.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("phonenumber", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="phonedevice",
            name="number",
            field=two_factor.fields.EncryptedPhoneNumberField(
                max_length=128,
                region=None,
            ),
        ),
    ]
