FROM python:3.8.1-slim-buster

WORKDIR /usr/src/app

COPY . .

RUN python setup.py install

ENTRYPOINT ["mirror"]
CMD []
