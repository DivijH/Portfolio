# Generated by Django 4.0.1 on 2022-08-23 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0006_tag_project_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='slug',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
