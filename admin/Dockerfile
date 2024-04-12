FROM python:3.11-slim

RUN mkdir app
WORKDIR /app

ADD . /app/
ADD .env.docker .env

RUN pip install -r requirements.txt

CMD python store/manage.py migrate \
    && python store/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')" \
    && python store/manage.py loaddata data.json \ 
    && python store/manage.py runserver 0.0.0.0:8000

