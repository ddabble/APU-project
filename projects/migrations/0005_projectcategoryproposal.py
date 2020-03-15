# Generated by Django 2.1.7 on 2020-03-15 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_alter_related_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectCategoryProposal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='projectcategory',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
