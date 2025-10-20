import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import streamlit as st

from file_operator import *
from utils import normalize_command

# 建立ORM基础类
Base = declarative_base()


# 定义Question的ORM映射
class Question(Base):
    # 指定本类映射到questions表
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 指定question映射到question字段; question字段为字符串类形
    question = Column(String(300))
    answer = Column(String(100))
    score = Column(Integer)
    creator = Column(String(16))
    class_name = Column(String(16))
    add_time = Column(String(16))


# 定义Student的ORM映射
class Student(Base):
    # 指定本类映射到questions表
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    class_name = Column(String(16))
    score = Column(Integer)

# excel导入数据库表questions
def to_sql_questions(xls_df, creator, class_name):
    # 创建数据库连接引擎
    engine = create_engine("sqlite:///myDB.db", echo=True)
    # 建立session对象
    Session = sessionmaker(bind=engine)
    session = Session()

    # 获取标准答案
    stander_answer = read_data("questions", "answer,score", "admin", class_name)
    stander_answer = dict(stander_answer)

    i = 0

    # 实例化Student类
    student_obj = Student(
        name=creator,
        class_name=class_name,
        score=0,
    )

    # 数据写入数据库
    for row in xls_df.values:
        # 答案处理
        try:
            answer = str(row[2])
        except:
            answer = ""

        # 分数处理
        score = "0"  # 默认值

        # if len(row) >= 4:
        if student_obj.name == "admin":
            # 如果row长度等于4
            score = row[3]
        elif normalize_command(stander_answer["answer"][i]) == normalize_command(answer):
            score = stander_answer["score"][i]
            student_obj.score += score
        # 如果以上条件都不满足，score 保持默认值 0

        score = str(score)

        # 实例化Question类
        question_obj = Question(
            question=row[1],
            answer=answer,
            score=score,
            add_time=datetime.now(),
            class_name=class_name,
            creator=creator,
        )
        session.add(question_obj)

        i += 1

    student_obj.score = str(student_obj.score)

    # 添加学生的信息
    session.add(student_obj)
    # 保存
    session.commit()
    session.close()
    return True


# df导入数据库表students
# def write_student(name, score, class_name="21软件2"):
#     # 创建数据库连接引擎
#     engine = create_engine("sqlite:///myDB.db", echo=True)
#     # 建立session对象
#     Session = sessionmaker(bind=engine)
#     session = Session()

#     # 数据写入数据库
#     student_obj = Student(
#         name=name,
#         class_name=class_name,
#         score=score,
#     )
#     session.add(student_obj)

#     # 保存
#     session.commit()
#     session.close()
#     return True


# 读取数据库中的数据
# @st.cache_data
def out_sql(table_name):
    # 创建数据库连接引擎
    engine = create_engine("sqlite:///myDB.db", echo=True)
    sql_command = f"select * from {table_name}"
    return pd.read_sql(sql_command, engine)


# 读取
def read_data(table_name, clum, creator, class_name):
    engine = create_engine("sqlite:///myDB.db", echo=True)
    sql_command = f"select {clum} from {table_name} where creator = '{creator}' and class_name = '{class_name}'"
    return pd.read_sql(sql_command, engine)


# 清空question数据表中的数据
def del_question_data(id):
    # 创建数据库连接引擎
    engine = create_engine("sqlite:///myDB.db", echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    if id:
        session.query(Question).filter(Question.id == id).delete()
    else:
        session.query(Question).delete()
    session.commit()
    session.close()
    return True


# 清空student数据表中的数据
def del_student_data(id):
    # 创建数据库连接引擎
    engine = create_engine("sqlite:///myDB.db", echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    if id:
        session.query(Student).filter(Student.id == id).delete()
    else:
        session.query(Student).delete()
    session.commit()
    session.close()
    return True


if __name__ == "__main__":
    # 获取文件名
    # files_name = get_files_name("answers")

    xls_df = read_xlsx("./answer/HW1-2_02曾俊杰.xlsx")

    to_sql_questions(xls_df, creator="ttcc", class_name="21软件2")

    # 删除id=1的数据
    del_student_data(1)

    # 删除所有数据
    del_student_data(0)
