FROM python:3
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y nginx netcat net-tools

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN mkdir media static logs

RUN pip install -r requirements.txt
ADD . /code

RUN apt-get install -y locales
RUN echo "Europe/Helsinki" > /etc/timezone && \ 
    dpkg-reconfigure -f noninteractive tzdata && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# fi_FI.UTF-8 UTF-8/fi_FI.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="fi_FI.UTF-8"'>/etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=fi_FI.UTF-8
RUN locale -a
RUN export LOCALE_PATHS="/usr/share/i18n"

COPY ./django_local_nginx.conf /etc/nginx/sites-available/
#COPY ./django_production_nginx.conf /etc/nginx/sites-available/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

EXPOSE 8000
COPY ./run.sh /
ENTRYPOINT ["/run.sh"]
