FROM ubuntu:24.04

RUN apt update \
    && apt install -y python3 python3-pip git nano vim \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m framed
RUN echo "framed:framed" | chpasswd


USER framed
COPY . /home/framed/
WORKDIR /home/framed

RUN pip install --break-system-packages -r requirements.txt

ENTRYPOINT /bin/bash