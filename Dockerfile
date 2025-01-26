FROM python:3.12-slim
RUN apt-get update && apt-get install -y postgresql-client && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN mkdir /java_code_test
WORKDIR /java_code_test
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN chmod a+x /java_code_test/docker/*.sh
