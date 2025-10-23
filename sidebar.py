import streamlit as st

from db_operator import to_sql_questions, read_xlsx


# 显示侧边栏
def show_sidebar(question_df, student_df):
    # 初始化会话状态
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    if 'show_success_message' not in st.session_state:
        st.session_state.show_success_message = False
    if 'error_messages' not in st.session_state:
        st.session_state.error_messages = []

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
    
    # 检查是否有新文件上传
    new_files_processed = False
    error_messages = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file and uploaded_file.name not in st.session_state.processed_files:
                try:
                    # 根据文件名，获取班别名
                    try:
                        class_name = uploaded_file.name.split(".")[0].split("_")[-2]
                        # 根据文件名，获取创建者
                        creator = uploaded_file.name.split(".")[0].split("_")[-1]
                    except IndexError:
                        error_messages.append(f"文件 '{uploaded_file.name}' 命名格式不正确，请按照'班别_姓名.xlsx'格式命名")
                        continue
                    
                    # 读取上传的excel表
                    try:
                        df = read_xlsx(uploaded_file)
                    except Exception as e:
                        error_messages.append(f"文件 '{uploaded_file.name}' 读取失败：{str(e)}")
                        continue
                    
                    # 数据导入数据库
                    success, message = to_sql_questions(df, creator, class_name)
                    
                    if success:
                        # 标记文件为已处理
                        st.session_state.processed_files.add(uploaded_file.name)
                        new_files_processed = True
                    else:
                        error_messages.append(f"文件 '{uploaded_file.name}' 导入失败：{message}")
                        
                except Exception as e:
                    error_messages.append(f"文件 '{uploaded_file.name}' 处理时发生未知错误：{str(e)}")
    
    # 如果有新文件处理完成，显示成功消息（只显示一次）
    if new_files_processed and not st.session_state.show_success_message:
        st.session_state.show_success_message = True
        st.success("导入成功！")
    elif not new_files_processed and st.session_state.show_success_message:
        # 如果没有新文件但之前显示了消息，重置状态
        st.session_state.show_success_message = False
    
    # 显示错误消息
    if error_messages:
        for error_msg in error_messages:
            st.error(error_msg)
        # 清空错误消息，避免重复显示
        error_messages.clear()

    st.sidebar.info("作者：陈沛华，时间：2023年11月7日")