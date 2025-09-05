from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0011_fix_roianalytics_cross_promo'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE news_newswidget "
                "ADD COLUMN IF NOT EXISTS show_tags boolean NOT NULL DEFAULT false;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "ALTER TABLE news_newswidget "
                "ADD COLUMN IF NOT EXISTS show_cross_promotion boolean NOT NULL DEFAULT false;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


