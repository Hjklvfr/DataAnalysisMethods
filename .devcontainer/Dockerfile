FROM python:3.10-bookworm
LABEL authors="hjklvr"

RUN apt install -y curl

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN apt-get update && apt-get install -y \
    software-properties-common \
    npm
RUN npm install npm@latest -g && \
    npm install n -g && \
    n latest
RUN node --version
RUN npm --version

RUN npm install --global yarn
RUN corepack enable
RUN yarn set version stable

RUN useradd -ms /bin/bash dev
USER dev
WORKDIR /home/dev
