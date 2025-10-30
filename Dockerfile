FROM mcr.microsoft.com/devcontainers/python:0-3.11

LABEL MAINTAINER = "Fedorov"

# 设置工作目录
WORKDIR /workspaces/tools

# 复制依赖文件
COPY requirements.txt /tmp/requirements.txt

# 安装依赖
RUN pip3 install --upgrade pip && \
    pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install -r /tmp/requirements.txt

# 创建外部存储目录（可选）
RUN mkdir -p /external_storage && chmod 777 /external_storage

# 暴露端口
EXPOSE 8888

# 设置默认命令
CMD ["streamlit", "run", "auth.py", "--server.port", "8888", "--server.address", "0.0.0.0"]