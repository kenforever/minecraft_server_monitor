FROM python:latest

WORKDIR /app

ADD . /app

RUN pip3 install -r requirements.txt


CMD [ "python3", "setup.py" ]
CMD [ "python3", "app.py" ]
