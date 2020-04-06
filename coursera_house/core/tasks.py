from __future__ import absolute_import, unicode_literals
from celery import task

from .models import Setting
from .. import settings


@task()
def smart_home_manager():
    # Код для проверки условий
    pass
