# Generated by Django 2.2.7 on 2019-11-28 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0007_auto_20191128_1816'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('WA', 'Wrong Answer'), ('TLE', 'Time Limit Exceeded'), ('AC', 'Accepted'), ('MLE', 'Memory Limit Exceeded'), ('RTE', 'Runtime Error'), ('PEN', 'Pending'), ('UNE', 'Unknown Error'), ('ACE', 'Abort Called Error'), ('CTE', 'Compilation Error')], default='PEN', max_length=3),
        ),
        migrations.DeleteModel(
            name='SampleCase',
        ),
    ]