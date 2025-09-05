from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0008_alter_rawarticle_author'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE news_roianalytics "
                "ADD COLUMN IF NOT EXISTS tags_assigned integer NOT NULL DEFAULT 0;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


