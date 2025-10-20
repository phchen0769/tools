# yuejuan
创建一个web站点用于批改学生成绩。
# 本地运行
streamlit run auth.py
# 指定端口运行
streamlit run auth.py --server.port 8888

# 注意：
# 程序编写完成后，需要把docker-compose-win.yml以及Dockerfile拷贝到程序根目录（与auth.py同级目录）下，cmd cd到程序根目录，后执行 docker-compose -f docker-compose-win.yml up 生成并启动容器。