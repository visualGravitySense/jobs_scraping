# Generated by Django 4.2 on 2025-06-06 08:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkedInAuth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField(verbose_name='Access Token')),
                ('refresh_token', models.TextField(verbose_name='Refresh Token')),
                ('expires_at', models.DateTimeField(verbose_name='Expires At')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'LinkedIn Authentication',
                'verbose_name_plural': 'LinkedIn Authentications',
            },
        ),
        migrations.AddField(
            model_name='vacancy',
            name='salary_currency',
            field=models.CharField(default='EUR', max_length=10, verbose_name='Валюта зарплаты'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='salary_max',
            field=models.IntegerField(blank=True, default=None, null=True, verbose_name='Максимальная зарплата'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='salary_min',
            field=models.IntegerField(blank=True, default=None, null=True, verbose_name='Минимальная зарплата'),
        ),
        migrations.AlterField(
            model_name='city',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='error',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='language',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='url',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='JobScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relevance_score', models.FloatField(default=0.0, verbose_name='Релевантность')),
                ('salary_score', models.FloatField(default=0.0, verbose_name='Оценка зарплаты')),
                ('company_score', models.FloatField(default=0.0, verbose_name='Оценка компании')),
                ('total_score', models.FloatField(default=0.0, verbose_name='Общий скор')),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('vacancy', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='score', to='scraping.vacancy')),
            ],
            options={
                'verbose_name': 'Оценка вакансии',
                'verbose_name_plural': 'Оценки вакансий',
            },
        ),
    ]
