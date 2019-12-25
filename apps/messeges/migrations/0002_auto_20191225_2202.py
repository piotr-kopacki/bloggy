# Generated by Django 2.2.9 on 2019-12-25 19:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('messeges', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='privatemessage',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pms_sent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='privatemessage',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pms_received', to=settings.AUTH_USER_MODEL),
        ),
    ]
