# Generated by Django 2.0.7 on 2018-07-31 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commands', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='command',
            name='original_file_name',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]