# Backend для Armada

## Стэк
* Django
* Django Rest Framework
* PostgeSQL
* Docker
* Redis
* RabbitMQ


## Code Style

* Необходимо придерживаться стандартов PEP8

## Информация по структуре
 Приложения джанго (сервисы) необходимо создавать в папке src/apps для этого нужно создать папку с названием сервиса 
 и ввести команду `./src/manage.py startapp <app_name> src/apps/<app_name>/`

При создании нового приложения необходимо зайти в apps.py и добавить `label = 'transfer_<app_name>'` в классе приложения.

## Команды
Для того, чтобы сгенерировать миграции необходимо ввести команду `docker compose exec web src/manage.py makemigrations`
Для того, чтобы применить миграции необходимо ввести команду `docker compose exec web src/manage.py migrate`
Для запуска тестов в докере: `docker compose exec web src/manage.py test`

## Информация по работе с GIT

В main ветке будет храниться текущая прод версия, в develop - текущая версия в разработке, то что потом отправится в прод.
У каждого будет своя папка с ветками вида: `name/feature_name`, где name - ваше имя, feature_name - название фичи, которую вы добавляете.
Затем, после того как вы закончили работу над фичей вы делаете pull request в develop ветку. Тимлид проверяет всё ли ок, после чего ваши изменения мерджатся в develop ветку.
