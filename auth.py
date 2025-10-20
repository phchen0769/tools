import streamlit as st
import streamlit_authenticator as stauth
import hydralit as hy

from frist_page import main as frist_main
from second_page import main as second_main
from file_renamer import show_file_rename_page  # 添加这一行
from db_operator import out_sql


# 初始化 站点显示参数
st.set_page_config(
    page_title="学生成绩批阅系统",
    page_icon="🇨🇳",
    layout="wide",
    initial_sidebar_state="auto",
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
    "name": "yuanjuan_cookie",
    "preauthorized": {"emails": "phchen0769@gmail.com"},
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
    # 登录成功
    with st.sidebar:
        st.markdown("***")
        # with cols1.container():
        #     if st.button("注册"):
        #         try:
        #             if authenticator.register_user("注册", preauthorization=False):
        #                 st.success("注册成功！")
        #         except Exception as e:
        #             st.error(e)

        # with cols2.container():
        #     if st.button("重置密码"):
        #         # 重置密码
        #         try:
        #             if authenticator.reset_password(username, "重置密码"):
        #                 st.success("密码重置成功！")
        #         except Exception as e:
        #             st.error(e)

        # with cols3.container():
        #     if st.button("更新个人信息"):
        #         # 更新用户详细信息
        #         try:
        #             if authenticator.update_user_details(username, "更新个人信息"):
        #                 st.success("个人信息更新成功。")
        #         except Exception as e:
        #             st.error(e)

        # # 退出按钮
        # with cols4.container():
        #     # 退出登录
        #     authenticator.logout("退出", "main", key="unique_key")

        cols1, cols2 = st.columns(2)
        cols1.markdown(f"欢迎{st.session_state['name']}")

    # 退出按钮
    with cols2.container():
        # 退出登录
        authenticator.logout("退出", "main", key="unique_key")

    st.sidebar.markdown("***")

    # 隐藏made with streamlit
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 在右侧显示主要内容
    app = hy.HydraApp(title="阅卷系统")

    @app.addapp()
    def 题目详情():
        frist_main()

    @app.addapp()
    def 成绩汇总():
        second_main()

    # 添加文件重命名功能
    @app.addapp()
    def 文件重命名():
        show_file_rename_page()

    app.run()

elif st.session_state["authentication_status"] is False:
    st.error("用户名或密码错误！")
elif st.session_state["authentication_status"] is None:
    st.warning("请输入你的用户名和密码。")

st.markdown(
    """
                        
                        #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5 > div.block-container.st-emotion-cache-1y4p8pa.ea3mdgi4{
                            padding:10px;
                        }
                        #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5 > div.block-container.st-emotion-cache-1y4p8pa.ea3mdgi4 > div > div{
                        padding:0;
                        margin:0;
                        width:80vw;
                        }
                        #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5{
                        padding:0;
                        margin:0;
                        flex-direction: row;
                        flex-wrap: wrap;
                        width:100vw;
                        }

                        #root > div:nth-child(1) > div.withScreencast > div > div > header > div.st-emotion-cache-zq5wmm.ezrtsby0 > div.stDeployButton > button{
                        display:none;
                        }

                        </style>""",
    unsafe_allow_html=True,
)