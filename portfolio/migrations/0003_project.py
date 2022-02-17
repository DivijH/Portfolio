# Generated by Django 4.0 on 2022-01-24 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0002_rename_blogs_blog_alter_blog_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('summary', models.TextField(max_length=500)),
                ('template', models.CharField(max_length=100)),
            ],
        ),
    ]
