from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0010_fix_roianalytics_tag_json_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE news_roianalytics "
                "ADD COLUMN IF NOT EXISTS cross_promotion_success_rate double precision NOT NULL DEFAULT 0;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


