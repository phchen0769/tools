import streamlit as st

from db_operator import to_sql_questions, read_xlsx


# 显示侧边栏
def show_sidebar(question_df, student_df):
    # 标题
    con_col1, con_col2 = st.sidebar.columns(2)

    with con_col1:
        # download_btn控件，下载导入模板
        with open("./template/班别_admin.xlsx", "rb") as file:
            st.download_button(
                label="下载标准答案模板",
                data=file,
                file_name="班别_admin.xlsx",
                mime="ms-excel",
            )

    with con_col2:
        # download_btn控件，下载导入模板
        with open("./template/班别_姓名.xlsx", "rb") as file:
            st.download_button(
                label="下载答题卡模板",
                data=file,
                file_name="班别_姓名.xlsx",
                mime="ms-excel",
            )

    st.sidebar.markdown("***")

    st.sidebar.warning("1、先导入标准答案答题卡，再导入学生答题卡。2、答题卡的名字一定要按照模板文档修改。")

    col1, col2 = st.sidebar.columns(2)

    show_image = False

    with col1:
        if st.sidebar.button("示例"):
            st.sidebar.image("images/1.png", "命名样例")
            st.sidebar.image("images/2.png", "表内容样例-红色内容不能修改")

    with col2:
        if st.sidebar.button("关闭"):
            show_image = not show_image

    # file_uploader控件，上传excle表
    uploaded_files = st.sidebar.file_uploader(
        label="导入数据", type=["xlsx"], accept_multiple_files=True
    )
    for uploaded_file in uploaded_files:
        if uploaded_file:
            # 根据文件名，获取班别名
            class_name = uploaded_file.name.split(".")[0].split("_")[-2]
            # 根据文件名，获取创建者
            # creator = uploaded_file.name.split(".")[0].split("-")[1]
            creator = uploaded_file.name.split(".")[0].split("_")[-1]
            # creator = uploaded_file.name.split(".")[0][-3:]
            # 读取上传的excel表
            df = read_xlsx(uploaded_file)
            # 数据导入数据库
            to_sql_questions(df, creator, class_name)
            st.success("导入成功！")

    st.sidebar.info("作者：陈沛华，时间：2023年11月7日")
