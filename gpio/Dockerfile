FROM ubuntu:20.04

RUN apt update && \
    apt install -y --no-install-recommends mosquitto-clients gpiod

COPY gpio_poller.sh /opt/gpio_poller.sh
RUN chmod +x /opt/gpio_poller.sh

CMD /opt/gpio_poller.sh
