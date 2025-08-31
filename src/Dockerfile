FROM python:3.10.11

WORKDIR /opt/app/src

RUN apt-get update
RUN apt install libldap2-dev libsasl2-dev -y
COPY src/requirements.txt ./
RUN pip install pip==23.1.2
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt
RUN pip install ptvsd
RUN ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

RUN mkdir -p /etc/app

COPY ../config.json /etc/app/config.json

CMD ["python", "-m", "main"]
