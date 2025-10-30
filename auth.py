import streamlit as st
import streamlit_authenticator as stauth
import hydralit as hy

from questions_page import main as frist_main
from records_page import main as second_main
from renamer_page import show_file_rename_page  # 添加这一行
from uploader_page import show_file_upload_page  # 添加文件上传页面导入
from db_operator import out_sql


# 初始化 站点显示参数
st.set_page_config(
    page_title="Tools",
    page_icon="🇨🇳",
    layout="wide",
    initial_sidebar_state="collapsed",  # 改为collapsed以隐藏sidebar
    menu_items=None,
)


# 创建空的字典
credentials = {"usernames": {}}

# 从数据库读取用户信息
user_df = out_sql("users").values

for user in user_df:
    user_dict = dict(
        {
            user[1]: {
                "password": user[2],
                "name": user[3],
                "email": user[4],
            }
        }
    )
    credentials["usernames"].update(user_dict)


# 把密码转换成hash密码
# hashed_passwords = stauth.Hasher(["123"]).generate()

# print(hashed_passwords)


# cookie信息
cookie = {
    "expiry_days": 30,
    "key": "Fedorov is handsome man.",  # 必须是字符串
    "name": "tools_cookie",
    "preauthorized": {"emails": "pwchan0769@icloud.com"},
}

# 实例化authenticator对象
authenticator = stauth.Authenticate(
    credentials,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"],
    # 用于注册检查
    cookie["preauthorized"],
)

# 生成登录框
name, authentication_status, username = authenticator.login("登录", "main")

# 登录页面的注册按钮和重置密码按钮

if st.session_state["authentication_status"]:
    # 隐藏made with streamlit
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .css-1d391kg {display: none;}  /* 隐藏sidebar */
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 在顶部显示用户信息和退出按钮
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"### 👋 欢迎，{st.session_state['name']}！")

    with col3:
        # 退出登录按钮
        if st.button("🚪 退出登录"):
            st.session_state["authentication_status"] = None
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

    @app.addapp()
    def 题目详情():
        frist_main()

    @app.addapp()
    def 成绩汇总():
        second_main()

    app.run()

elif st.session_state["authentication_status"] is False:
    st.error("❌ 用户名或密码错误！")
elif st.session_state["authentication_status"] is None:
    st.warning("🔐 请输入你的用户名和密码。")
