# Generated by Django 2.1.7 on 2020-03-15 03:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0002_payment_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paying_payments', to='user.Profile'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiving_payments', to='user.Profile'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='projects.Task'),
        ),
    ]
