import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import streamlit as st

from file_operator import *
from utils import normalize_command

# 建立ORM基础类
Base = declarative_base()

# 全局数据库连接引擎和会话工厂
_engine = None
_session_factory = None

def get_engine():
    """获取全局数据库引擎，使用连接池"""
    global _engine
    if _engine is None:
        # 使用连接池，设置echo=False减少日志输出
        _engine = create_engine(
            "sqlite:///myDB.db", 
            echo=True,  # 关闭详细日志
            pool_size=5,  # 连接池大小
            max_overflow=10,  # 最大溢出连接数
            pool_pre_ping=True,  # 连接前检查
            pool_recycle=3600  # 连接回收时间（秒）
        )
    return _engine

def get_session():
    """获取数据库会话"""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return scoped_session(_session_factory)

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
    # 指定本类映射到students表
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    class_name = Column(String(16))
    score = Column(Integer)

# excel导入数据库表questions
def to_sql_questions(xls_df, creator, class_name):
    # 使用全局会话
    session = get_session()
    try:
        # 检查数据框是否为空
        if xls_df.empty:
            return False, "Excel文件为空或格式不正确"
        
        # 检查数据框列数是否足够
        if len(xls_df.columns) < 3:
            return False, f"Excel文件列数不足，需要至少3列，当前有{len(xls_df.columns)}列"
        
        # 获取标准答案
        try:
            stander_answer = read_data("questions", "answer,score", "admin", class_name)
            stander_answer = dict(stander_answer)
        except Exception as e:
            # 如果没有标准答案，创建一个空的stander_answer
            stander_answer = {"answer": [], "score": []}

        i = 0

        # 只有当创建者不是admin时才创建学生对象
        student_obj = None
        if creator != "admin":
            student_obj = Student(
                name=creator,
                class_name=class_name,
                score=0,
            )

        # 数据写入数据库
        for row_index, row in enumerate(xls_df.values):
            # 答案处理
            try:
                answer = str(row[2])
            except (IndexError, ValueError) as e:
                return False, f"第{row_index + 1}行数据格式错误：{str(e)}"

            # 分数处理
            score = "0"  # 默认值

            if creator == "admin":
                # 如果是admin导入标准答案，直接使用row中的分数
                if len(row) >= 4:
                    try:
                        score = str(row[3])
                    except (IndexError, ValueError):
                        score = "0"
            elif i < len(stander_answer["answer"]):
                # 只有当有标准答案时才进行比较
                if normalize_command(stander_answer["answer"][i]) == normalize_command(answer):
                    score = stander_answer["score"][i]
                    if student_obj:  # 只有存在学生对象时才累加分数
                        # 修复：将score转换为字符串后再检查是否为数字
                        score_str = str(score)
                        student_obj.score += int(score_str) if score_str.isdigit() else 0

            score = str(score)

            # 实例化Question类
            question_obj = Question(
                question=str(row[1]) if len(row) > 1 else "",
                answer=answer,
                score=score,
                add_time=datetime.now(),
                class_name=class_name,
                creator=creator,
            )
            session.add(question_obj)
            i += 1

        # 只有当创建者不是admin时才添加学生信息
        if student_obj:
            student_obj.score = str(student_obj.score)
            session.add(student_obj)

        # 保存
        session.commit()
        # 清除缓存，确保数据立即更新
        clear_cache()
        return True, "导入成功"
    except Exception as e:
        session.rollback()
        return False, f"导入数据时出错: {str(e)}"
    finally:
        session.close()

# 读取数据库中的数据
@st.cache_data(ttl=60)  # 缓存1分钟，减少频繁查询
def out_sql(table_name):
    """读取数据库表数据，使用缓存提高性能"""
    engine = get_engine()
    sql_command = f"select * from {table_name}"
    return pd.read_sql(sql_command, engine)

# 读取特定数据
@st.cache_data(ttl=60)  # 缓存1分钟，减少频繁查询
def read_data(table_name, clum, creator, class_name):
    """读取特定条件的数据，使用缓存提高性能"""
    engine = get_engine()
    # 使用参数化查询防止SQL注入
    sql_command = f"select {clum} from {table_name} where creator = ? and class_name = ?"
    return pd.read_sql(sql_command, engine, params=(creator, class_name))

def clear_cache():
    """清除所有数据库查询缓存"""
    # 清除out_sql缓存
    out_sql.clear()
    # 清除read_data缓存
    read_data.clear()

# 清空question数据表中的数据
def del_question_data(id):
    session = get_session()
    try:
        if id:
            session.query(Question).filter(Question.id == id).delete()
        else:
            session.query(Question).delete()
        session.commit()
        # 清除缓存，确保删除后页面立即更新
        clear_cache()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"删除题目数据时出错: {e}")
        return False
    finally:
        session.close()

# 清空student数据表中的数据
def del_student_data(id):
    session = get_session()
    try:
        if id:
            session.query(Student).filter(Student.id == id).delete()
        else:
            session.query(Student).delete()
        session.commit()
        # 清除缓存，确保删除后页面立即更新
        clear_cache()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"删除学生数据时出错: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    # 获取文件名
    # files_name = get_files_name("answers")

    xls_df = read_xlsx("./answer/HW1-2_02曾俊杰.xlsx")

    to_sql_questions(xls_df, creator="ttcc", class_name="21软件2")

    # 删除id=1的数据
    del_student_data(1)

    # 删除所有数据
    del_student_data(0)