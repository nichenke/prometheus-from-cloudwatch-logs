FROM python:3.7-slim

RUN pip3 install pipenv

COPY . /app

WORKDIR /app

RUN pipenv install --system
RUN python3 setup.py install

CMD ['python3', "/app/process.py"]