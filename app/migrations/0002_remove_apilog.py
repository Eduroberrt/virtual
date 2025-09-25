# Generated manually to remove APILog table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_alter_fivesimorder_status'),  # Latest migration
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS app_apilog;",
            reverse_sql="-- Cannot reverse this migration",
        ),
    ]