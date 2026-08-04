# Cloud-based File Manager API using `djangorestframework`
## Requirements
### pip requirements
* django
* djangorestframeworl
* djangorestframework-simplejwt
* celery[redis]
* django-filter
* pyetest (for testing purposes)
* mysqlclient (or another client for your favorite DB)

You can either install the requirements by hand or if
you're using `uv` as your env manager simply run `uv venv`
for creating an environment and `uv sync` to install the packages specified in `pyproject.toml`.

### redis
Redis is used as the broker between django and celery. You can use another broker like RabbitMQ, but be sure to change the required values in `core/settings.py`.
Installation of redis varies depending on the environment, so please do your own search on how to install it.

### celery
An implementation of task queue concept for python. It's installed using python's package manager

### MySQL
The database used in the app. You can opt for postgresql, but I'm not quite sure if there are any incompatibilities between them, or if the app will function the same.

## Steps to take
1. Install the pip requirements
2. Start up your DB, name it whatever you're going to place in `DATABASES.default.name` in `core/settings.py`, or simply `cloud_api` as its the default. User credentials should also match.
3. Run the migrations : `python manage.py migrate`
4. Start up the broker, in the case of redis for windows: `redis-server`
5. Start up celery to check on queues in redis : `celery -A core worker --pool=solo -l debug`
6. Finally start the app: `python manage.py runserver`

#TODO list of apis and their descriptions