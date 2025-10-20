FROM mcr.microsoft.com/devcontainers/python:0-3.11

LABEL MAINTAINER = "Fedorov"

# 生成docker-compose时候使用
COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --upgrade pip && pip3 config set global.index-url https:\/\/pypi.tuna.tsinghua.edu.cn\/simple
RUN pip3 install -r /tmp/requirements.txt

EXPOSE 8888

CMD ["streamlit", "run", "main.py","--server.port 8888"]