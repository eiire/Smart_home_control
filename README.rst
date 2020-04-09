Установка
---------

Установить pipenv https://docs.pipenv.org/

.. code-block:: bash

    $ pip install pipenv


Установить зависимости проекта, включая зависимости для разработки

.. code-block:: bash

    $ pipenv install --dev

Активировать virtualenv проекта

.. code-block:: bash

    $ pipenv shell

Запустить миграции

.. code-block:: bash

    $ python manage.py migrate


Запуск
------

Для запуска периодического опроса состояния дома, используется celery.

Запускается как celery -A coursera_house.celery worker -l info -B

Celery + Redis : https://redis.io/topics/quickstart


Тестирование
------------

.. code-block:: bash

    $ py.test tests
