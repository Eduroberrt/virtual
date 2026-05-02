# Generated migration for adding refunded field to FiveSimOrder model
# This migration merges two branches: 0014_alter_fivesimorder_status and 0004_service_mtelsms_service_id

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_alter_fivesimorder_status'),
        ('app', '0004_service_mtelsms_service_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='fivesimorder',
            name='refunded',
            field=models.BooleanField(default=False, help_text='Prevent double refunds'),
        ),
    ]
