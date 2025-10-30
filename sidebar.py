import streamlit as st
import os
import glob

from db_operator import to_sql_questions, read_xlsx


# 显示侧边栏
def show_sidebar(question_df, student_df):
    # 初始化会话状态
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
    if "show_success_message" not in st.session_state:
        st.session_state.show_success_message = False
    if "error_messages" not in st.session_state:
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

    st.sidebar.warning(
        "1、先导入标准答案答题卡，再导入学生答题卡。2、答题卡的名字一定要按照模板文档修改。"
    )

    col1, col2 = st.sidebar.columns(2)

    show_image = False

    with col1:
        if st.sidebar.button("示例"):
            st.sidebar.image("images/1.png", "命名样例")
            st.sidebar.image("images/2.png", "表内容样例-红色内容不能修改")

    with col2:
        if st.sidebar.button("关闭"):
            show_image = not show_image

    # 使用外部存储路径读取Excel文件
    external_storage_dir = "/external_storage/文档"

    # 检查外部存储目录是否存在
    if not os.path.exists(external_storage_dir):
        st.sidebar.error(f"外部存储目录不存在: {external_storage_dir}")
        st.sidebar.info("请确保docker-compose.yml中已正确配置外部存储挂载")
        return

    # 从外部存储目录读取Excel文件
    st.sidebar.subheader("外部存储文件导入")

    # 获取外部存储目录中的Excel文件
    external_files = glob.glob(os.path.join(external_storage_dir, "*.xlsx"))

    if external_files:
        st.sidebar.info(
            f"在 {external_storage_dir} 目录中找到 {len(external_files)} 个Excel文件"
        )

        # 显示文件列表供用户选择
        selected_files = st.sidebar.multiselect(
            "选择要导入的文件",
            [os.path.basename(f) for f in external_files],
            help="选择外部存储目录中的Excel文件进行导入",
        )

        # 检查是否有新文件需要处理
        new_files_processed = False
        error_messages = []

        if selected_files:
            for file_name in selected_files:
                file_path = os.path.join(external_storage_dir, file_name)
                if file_name not in st.session_state.processed_files:
                    try:
                        # 根据文件名，获取班别名
                        try:
                            class_name = file_name.split(".")[0].split("_")[-2]
                            # 根据文件名，获取创建者
                            creator = file_name.split(".")[0].split("_")[-1]
                        except IndexError:
                            error_messages.append(
                                f"文件 '{file_name}' 命名格式不正确，请按照'班别_姓名.xlsx'格式命名"
                            )
                            continue

                        # 读取外部存储Excel文件
                        try:
                            df = read_xlsx(file_path)
                        except Exception as e:
                            error_messages.append(
                                f"文件 '{file_name}' 读取失败：{str(e)}"
                            )
                            continue

                        # 数据导入数据库
                        success, message = to_sql_questions(df, creator, class_name)

                        if success:
                            # 标记文件为已处理
                            st.session_state.processed_files.add(file_name)
                            new_files_processed = True
                            st.sidebar.success(f"✅ 成功导入: {file_name}")
                        else:
                            error_messages.append(
                                f"文件 '{file_name}' 导入失败：{message}"
                            )

                    except Exception as e:
                        error_messages.append(
                            f"文件 '{file_name}' 处理时发生未知错误：{str(e)}"
                        )

        # 显示错误消息
        if error_messages:
            for error_msg in error_messages:
                st.sidebar.error(error_msg)
    else:
        st.sidebar.warning(
            f"在 {external_storage_dir} 目录中未找到Excel文件，请将答题卡文件放入该目录"
        )
        st.sidebar.info("支持的格式：.xlsx 文件")

        # 显示如何使用外部存储目录的说明
        st.sidebar.markdown(
            f"""
        **使用方法：**
        1. 在宿主机上确保路径 `/Volumes/myDriver/Docker/Streamlit/文档` 存在
        2. 将Excel答题卡文件放入该目录
        3. 文件命名格式：`班别_姓名.xlsx`
        4. 刷新页面后即可选择导入
        **注意：** 这是外部存储路径，通过docker-compose.yml挂载到容器
        """
        )

    st.sidebar.info("作者：陈沛华，时间：2023年11月7日")
