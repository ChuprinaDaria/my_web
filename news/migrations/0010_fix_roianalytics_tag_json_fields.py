from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0009_fix_roianalytics_tags_assigned'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE news_roianalytics "
                "ADD COLUMN IF NOT EXISTS top_performing_tags jsonb NOT NULL DEFAULT '[]'::jsonb;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "ALTER TABLE news_roianalytics "
                "ADD COLUMN IF NOT EXISTS tag_engagement_stats jsonb NOT NULL DEFAULT '{}'::jsonb;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


