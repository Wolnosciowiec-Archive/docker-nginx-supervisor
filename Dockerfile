FROM nginx:mainline-alpine

# Install:
#  - rsyslog for logs aggregation
#  - bash for a normal shell
#  - supervisord for running parallel processes and monitoring them
#  - the rest for PIP to build supervisord

RUN apk add --force --update  \
    bash rsyslog openssl dcron python python-dev py-pip vim \
    gcc musl-dev linux-headers \
    augeas-dev openssl-dev libffi-dev ca-certificates dialog \
    && pip install supervisor \
    && apk del --force gcc libffi-dev musl-dev linux-headers augeas-dev openssl-dev libffi-dev \
    && rm -rf /var/cache/apk/*

# WWW (nginx)
RUN addgroup -g 1000 production \
    && adduser -u 1000 -H -D -s /bin/sh -G production production

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ADD ./maintenance-page /www/maintenance-page
ADD ./ssl-provision /ssl-provision
ADD ./entry-point.sh /entry-point.sh

CMD ["bash /entry-point.sh"]

EXPOSE 80
EXPOSE 443
