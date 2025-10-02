# Generated manually for adding implementation_steps fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0020_add_processedarticle_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='processedarticle',
            name='implementation_steps_en',
            field=models.JSONField(default=list, verbose_name='Кроки впровадження (EN)'),
        ),
        migrations.AddField(
            model_name='processedarticle',
            name='implementation_steps_pl',
            field=models.JSONField(default=list, verbose_name='Кроки впровадження (PL)'),
        ),
        migrations.AddField(
            model_name='processedarticle',
            name='implementation_steps_uk',
            field=models.JSONField(default=list, verbose_name='Кроки впровадження (UK)'),
        ),
    ]
