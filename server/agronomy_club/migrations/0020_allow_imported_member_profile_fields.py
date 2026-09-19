# Generated manually to preserve existing members while allowing legacy profile completion.

import agronomy_club.models
from django.core import validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agronomy_club', '0019_alter_user_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='discipline',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='user',
            name='grad_yr',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[
                    validators.MinValueValidator(1900),
                    agronomy_club.models.max_value_curr_year,
                ],
            ),
        ),
    ]
