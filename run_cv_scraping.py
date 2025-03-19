import os, sys

from django.contrib.auth import get_user_model

from apps.scraping.parsers import *
from apps.scraping.models import Vacancy, City, Language, Error, Url

import django
django.setup()

proj = os.path.dirname(os.path.abspath('manage.py'))
sys.path.append(proj)
os.environ["DJANGO_SETTINGS_MODULE"] = "configs.settings"

User = get_user_model()

parsers = (
            (work, 'https://www.work.ua/ru/jobs-kyiv-python/'),
            (dou, 'https://jobs.dou.ua/vacancies/?city=%D0%9A%D0%B8%D0%B5%D0%B2&category=Python'),
            (djinni, 'https://djinni.co/jobs/keyword-python/kyiv/'),
            (rabota, 'https://rabota.ua/zapros/python/%D0%BA%D0%B8%D0%B5%D0%B2')
)


def get_settings():
    qs = User.objects.filter(send_email=True).values()
    settings_list = set((q['city_id'], q['language_id']) for q in qs)
    return settings_list


def get_urls(_settings):
    qs = Url.objects.all().values()
    url_dct = {(q['city_id'], q['language_id']): q['url_data'] for q in qs}
    urls = []
    for pair in _settings:
        tmp = {}
        tmp['city'] = pair[0]
        tmp['language'] = pair[1]
        tmp['url_data'] = url_dct[pair]
        urls.append(tmp)
    return urls

q = get_settings()
u = get_urls(q)

city = City.objects.filter(slug='kiev').first()
language = Language.objects.filter(slug='python').first()

jobs, errors = [], []
for func, url in parsers:
    j, e = func(url)
    jobs += j
    errors += e

for job in jobs:
    v = Vacancy(**job, city=city, language=language)
    try:
        v.save()
        print(v)
    except Exception as e:
        print(v, e)

if errors:
    er = Error(data=errors).save()
