FROM python:3.7 AS base
ENV PYTHONUNBUFFERED 1

WORKDIR /root/app

COPY ./services/bot/requirements.txt /root/app/requirements.txt
RUN pip install -r requirements.txt

ENV PYTHONPATH="/root/app:$PYTHONPATH"

# Set Up Django App
FROM base

COPY ./services/bot /root/app

# COPY ./scripts /root/app/scripts

# ENTRYPOINT ["./scripts/entry"]
# CMD ["start"]
