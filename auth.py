import streamlit as st
import streamlit_authenticator as stauth
import hydralit as hy
from datetime import datetime
import sqlite3
import bcrypt

from questions_page import main as frist_main
from records_page import main as second_main
from renamer_page import show_file_rename_page  # 添加这一行
from uploader_page import show_file_upload_page  # 添加文件上传页面导入
from homevisit_page import show_home_visit_page  # 确保导入正确的函数名
from db_operator import out_sql, create_session, get_session_by_token, delete_session, init_db

# 初始化数据库
init_db()

# 初始化 站点显示参数
st.set_page_config(
    page_title="Tools",
    page_icon="🇨🇳",
    layout="wide",
    initial_sidebar_state="expanded",  # 改为expanded以保持sidebar打开状态
    menu_items=None,
)

# 页面状态初始化
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'session_token' not in st.session_state:
    st.session_state['session_token'] = None

# 自动检查现有session
if st.session_state['authentication_status'] is None and st.session_state.get('session_token'):
    # 尝试使用session token恢复登录状态
    session_data = get_session_by_token(st.session_state['session_token'])
    if session_data:
        # session有效，恢复登录状态
        st.session_state['authentication_status'] = True
        st.session_state['name'] = session_data.name
        st.session_state['username'] = session_data.username
    else:
        # session无效，清除session token
        st.session_state['session_token'] = None
        st.session_state['authentication_status'] = None
        st.session_state['name'] = None
        st.session_state['username'] = None

# 检查当前session是否有效
def validate_session():
    if st.session_state.get('session_token'):
        session_data = get_session_by_token(st.session_state['session_token'])
        if not session_data:
            # Session无效，重置登录状态
            st.session_state['authentication_status'] = None
            st.session_state['name'] = None
            st.session_state['username'] = None
            st.session_state['session_token'] = None
            return False
        return True
    return False

# 尝试使用现有session恢复登录状态
if not st.session_state['authentication_status'] and st.session_state.get('session_token'):
    if validate_session():
        session_data = get_session_by_token(st.session_state['session_token'])
        st.session_state['authentication_status'] = True
        st.session_state['name'] = session_data.name
        st.session_state['username'] = session_data.username

# 如果已经登录，显示主界面
if st.session_state["authentication_status"]:
    # 验证session是否仍然有效
    if not validate_session():
        st.rerun()

    # 隐藏made with streamlit
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            /* 顶行工具栏*/
            header, .stApp > header, .st-emotion-cache-18ni7ap ea3mdgi2 {
                visibility: hidden;
            }

            /* 主页头部 */
            .st-emotion-cache-z5fcl4{
                padding: 1rem !important;
                /* background-color: #ADD8E6 !important; */
            }
            </style>
            """

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 在顶部显示用户信息和退出按钮
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"### 👋 欢迎，{st.session_state['name']}！")

    with col3:
        # 退出登录按钮
        if st.button("退出登录", key="logout_button"):
            # 只有在按钮被点击时才执行登出操作
            if st.session_state.get('session_token'):
                delete_session(st.session_state['session_token'])
            st.session_state["authentication_status"] = None
            st.session_state["name"] = None
            st.session_state["username"] = None
            st.session_state["session_token"] = None
            st.rerun()

    st.markdown("---")

    # 在右侧显示主要内容
    app = hy.HydraApp(title="教学工具")

    # 添加文件上传功能
    @app.addapp()
    def 文件上传():
        show_file_upload_page()

    # 添加文件重命名功能
    @app.addapp()
    def 文件重命名():
        show_file_rename_page()

    # 添加家访表功能
    @app.addapp()
    def 家访表():
        show_home_visit_page()

    @app.addapp()
    def 题目详情():
        frist_main()

    @app.addapp()
    def 成绩汇总():
        second_main()

    # 添加管理用户功能
    @app.addapp()
    def 管理用户():
        st.subheader("用户管理")
        
        # 检查是否为管理员
        if st.session_state.get('username') != 'admin':
            st.error("只有管理员才能访问此页面")
            return
        
        # 添加新用户到侧边栏
        with st.sidebar:
            st.header("添加新用户")
            with st.form("add_user_form"):
                new_username = st.text_input("新用户名")
                new_name = st.text_input("姓名")
                new_email = st.text_input("邮箱")
                new_password = st.text_input("密码", type="password")
                confirm_password = st.text_input("确认密码", type="password")
                
                submit_new_user = st.form_submit_button("添加用户")
                
                if submit_new_user:
                    if not new_username or not new_name or not new_email or not new_password:
                        st.error("请填写所有字段")
                    elif new_password != confirm_password:
                        st.error("两次输入的密码不一致")
                    else:
                        try:
                            # 连接到数据库
                            conn = sqlite3.connect('myDB.db')
                            cursor = conn.cursor()
                            
                            # 检查用户名是否已存在
                            cursor.execute("SELECT id FROM users WHERE username=?", (new_username,))
                            existing_user = cursor.fetchone()
                            
                            if existing_user:
                                st.error("用户名已存在")
                            else:
                                # 加密密码
                                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                                hashed_str = hashed.decode('utf-8')
                                
                                # 插入新用户
                                cursor.execute(
                                    "INSERT INTO users (username, password, name, email) VALUES (?, ?, ?, ?)",
                                    (new_username, hashed_str, new_name, new_email)
                                )
                                conn.commit()
                                st.success("用户添加成功")
                        except Exception as e:
                            st.error(f"添加用户时出错: {e}")
                        finally:
                            conn.close()
        
        # 显示所有用户
        conn = sqlite3.connect('myDB.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, username, name, email FROM users")
            users = cursor.fetchall()
            
            st.write("### 所有用户")
            if users:
                # 创建表格标题
                col_id, col_username, col_name, col_email, col_actions = st.columns([1, 2, 2, 3, 2])
                
                with col_id:
                    st.write("**ID**")
                with col_username:
                    st.write("**用户名**")
                with col_name:
                    st.write("**姓名**")
                with col_email:
                    st.write("**邮箱**")
                with col_actions:
                    st.write("**操作**")
                
                # 用分隔线分隔标题和数据
                st.markdown("<hr style='margin: 0 0 10px 0;'>", unsafe_allow_html=True)
                
                # 显示每一行用户数据
                for user in users:
                    col_id, col_username, col_name, col_email, col_actions = st.columns([1, 2, 2, 3, 2])
                    
                    with col_id:
                        st.write(str(user[0]))
                    with col_username:
                        st.write(user[1])
                    with col_name:
                        st.write(user[2])
                    with col_email:
                        st.write(user[3])
                    with col_actions:
                        # 水平排列修改和删除按钮
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button(f"修改", key=f"modify_{user[0]}", help=f"修改用户 {user[1]}"):
                                # 将当前用户信息存入session state
                                st.session_state['editing_user'] = user
                                st.session_state['show_modify_form'] = True
                        with btn_col2:
                            if st.button(f"删除", key=f"delete_{user[0]}", help=f"删除用户 {user[1]}"):
                                if user[1] != 'admin':  # 不允许删除admin用户
                                    try:
                                        cursor.execute("DELETE FROM users WHERE id=?", (user[0],))
                                        conn.commit()
                                        st.success(f"用户 {user[1]} 已删除")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"删除用户时出错: {e}")
                                else:
                                    st.error("不能删除管理员账户")
                
                # 用分隔线分隔用户列表和操作区
                st.markdown("---")
            else:
                st.write("没有找到用户")
            
            # 修改用户表单
            if st.session_state.get('show_modify_form'):
                editing_user = st.session_state.get('editing_user')
                if editing_user:
                    st.write(f"### 修改用户: {editing_user[1]}")
                    with st.form("modify_user_form"):
                        new_username = st.text_input("用户名", value=editing_user[1])
                        new_name = st.text_input("姓名", value=editing_user[2])
                        new_email = st.text_input("邮箱", value=editing_user[3])
                        new_password = st.text_input("新密码（留空则不修改）", type="password")
                        
                        submit_modify = st.form_submit_button("更新用户")
                        
                        if submit_modify:
                            try:
                                updates = []
                                params = []
                                
                                # 检查用户名是否与其他用户冲突（排除当前用户）
                                cursor.execute(
                                    "SELECT id FROM users WHERE username=? AND id!=?",
                                    (new_username, editing_user[0])
                                )
                                existing_user = cursor.fetchone()
                                
                                if existing_user:
                                    st.error("用户名已存在")
                                else:
                                    updates.append("username=?")
                                    params.append(new_username)
                                    
                                    updates.append("name=?")
                                    params.append(new_name)
                                    
                                    updates.append("email=?")
                                    params.append(new_email)
                                    
                                    if new_password:  # 如果提供了新密码
                                        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                                        hashed_str = hashed.decode('utf-8')
                                        updates.append("password=?")
                                        params.append(hashed_str)
                                    
                                    # 构建更新SQL
                                    sql = f"UPDATE users SET {','.join(updates)} WHERE id=?"
                                    params.append(editing_user[0])
                                    
                                    cursor.execute(sql, params)
                                    conn.commit()
                                    
                                    st.success("用户信息已更新")
                                    # 重置编辑状态
                                    st.session_state['editing_user'] = None
                                    st.session_state['show_modify_form'] = False
                                    st.rerun()
                            except Exception as e:
                                st.error(f"更新用户时出错: {e}")
                        
                        # 取消按钮
                        if st.form_submit_button("取消"):
                            st.session_state['editing_user'] = None
                            st.session_state['show_modify_form'] = False
                            st.rerun()
        finally:
            conn.close()

    app.run()

else:
    # 显示登录表单
    st.markdown("<h3 style='text-align: center;'>登录</h3>", unsafe_allow_html=True)
    
    # 输入框居中
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        
        login_button = st.button("登录")
        
        if login_button:
            if not username or not password:
                st.error("请输入用户名和密码！")
            else:
                try:
                    # 直接连接数据库查询用户信息
                    conn = sqlite3.connect('myDB.db')
                    cursor = conn.cursor()
                    
                    # 查询所有用户以显示可用用户名
                    cursor.execute("SELECT username, name FROM users")
                    all_users = cursor.fetchall()
                    
                    # 然后查找指定的用户
                    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        # 提取用户信息，根据结构 (id, username, password, name, email, ?)
                        user_id = user[0]
                        db_username = user[1]
                        stored_password = user[2]
                        db_name = user[3]
                        db_email = user[4]
                        
                        # 验证密码
                        input_password = password.encode('utf-8')
                        
                        # 检查存储的密码是否是bcrypt hash格式
                        if stored_password and (stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith('$2y$')):
                            # 使用bcrypt验证
                            password_valid = bcrypt.checkpw(input_password, stored_password.encode('utf-8'))
                        else:
                            # 直接比较密码
                            password_valid = stored_password == password
                        
                        if password_valid:
                            # 创建新的session
                            session_token = create_session(
                                db_username,  # username
                                db_name,      # name
                                db_email      # email
                            )
                            
                            # 设置session状态
                            st.session_state['authentication_status'] = True
                            st.session_state['name'] = db_name
                            st.session_state['username'] = db_username
                            st.session_state['session_token'] = session_token
                            
                            st.rerun()
                        else:
                            st.error("❌ 密码错误！")
                    else:
                        st.error("❌ 用户不存在！数据库中没有找到该用户名。")
                        if all_users:
                            st.info("数据库中存在的用户: " + ", ".join([f"{u[0]}({u[1]})" if len(u) > 1 else u[0] for u in all_users]))
                        else:
                            st.warning("警告: 数据库中没有任何用户")
                except sqlite3.Error as e:
                    st.error(f"数据库错误: {str(e)}")
                except Exception as e:
                    st.error(f"登录过程中发生错误: {str(e)}")
                finally:
                    if 'conn' in locals():
                        conn.close()