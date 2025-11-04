import streamlit as st
import pandas as pd
import os
import glob
import tempfile

from aggrid import aggrid_question
from db_operator import (
    out_sql,
    del_question_data,
    to_sql_questions,
    read_xlsx,
)


# 显示文件导入功能（移除了模板下载和查看命名示例）
def show_file_import_section():
    # 初始化会话状态
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
    if "show_success_message" not in st.session_state:
        st.session_state.show_success_message = False
    if "error_messages" not in st.session_state:
        st.session_state.error_messages = []
    # 添加本地文件处理状态跟踪
    if "processed_local_files" not in st.session_state:
        st.session_state.processed_local_files = set()
    # 添加file_uploader的key状态跟踪
    if "local_file_uploader_key" not in st.session_state:
        st.session_state.local_file_uploader_key = 0

    # 侧边栏 - 文件导入功能（移除了模板下载和查看命名示例）
    with st.sidebar:
        st.header("📋题目管理")

        # 使用外部存储路径读取Excel文件
        external_storage_dir = "/external_storage/文档"

        # 检查外部存储目录是否存在
        if not os.path.exists(external_storage_dir):
            st.error(f"❌ 外部存储目录不存在: {external_storage_dir}")
            st.info("请确保docker-compose.yml中已正确配置外部存储挂载")
            return

        # 从外部存储目录读取Excel文件
        st.subheader("📤 外部存储文件导入")

        # 获取外部存储目录中的Excel文件
        external_files = glob.glob(os.path.join(external_storage_dir, "*.xlsx"))

        if external_files:
            st.info(
                f"✅ 在 {external_storage_dir} 目录中找到 {len(external_files)} 个Excel文件"
            )

            # 初始化全选状态
            if "select_all" not in st.session_state:
                st.session_state.select_all = False

            # 创建全选按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 全选所有文件"):
                    st.session_state.select_all = not st.session_state.select_all
                    # 更新选择的文件列表
                    if st.session_state.select_all:
                        st.session_state.selected_files = [
                            os.path.basename(f) for f in external_files
                        ]
                    else:
                        st.session_state.selected_files = []

            with col2:
                if st.button("🔄 刷新文件列表"):
                    # 清理processed_files状态以避免死循环
                    st.session_state.processed_files = set()
                    st.experimental_rerun()

            # 显示文件列表供用户选择
            # 使用会话状态来保持选择的状态
            if "selected_files" not in st.session_state:
                st.session_state.selected_files = []

            selected_files = st.multiselect(
                "选择要导入的文件",
                [os.path.basename(f) for f in external_files],
                default=st.session_state.selected_files,
                help="选择外部存储目录中的Excel文件进行导入",
                key="file_selector",
            )

            # 更新会话状态
            st.session_state.selected_files = selected_files

            # 检查是否有新文件需要处理
            new_files_processed = False
            error_messages = []

            if selected_files:
                # 如果是全选状态，优先处理admin文件
                if st.session_state.select_all:
                    # 将admin文件排在前面
                    admin_files = [f for f in selected_files if "admin" in f.lower()]
                    other_files = [
                        f for f in selected_files if "admin" not in f.lower()
                    ]
                    # 重新排序：admin文件在前，其他文件在后
                    ordered_files = admin_files + other_files
                else:
                    # 非全选状态保持原有顺序
                    ordered_files = selected_files

                # 按照排序后的顺序处理文件
                for file_name in ordered_files:
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
                                st.success(f"✅ 成功导入: {file_name}")

                                # 如果是admin文件，给出特殊提示
                                if "admin" in file_name.lower():
                                    st.info(
                                        "🚨 注意：已优先导入标准答案文件，请等待其他文件继续导入..."
                                    )
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
                    st.error(error_msg)

            # 显示导入状态
            if new_files_processed:
                st.success("🎉 所选文件已成功导入！")
                # 重置全选状态
                st.session_state.select_all = False
                # 重新加载页面以反映更改
                st.experimental_rerun()
        else:
            st.warning(
                f"⚠️ 在 {external_storage_dir} 目录中未找到Excel文件，请将答题卡文件放入该目录"
            )
            st.info("📋 支持的格式：.xlsx 文件")

            # 显示如何使用外部存储目录的说明
            st.markdown(
                f"""
            **📝 使用方法：**
            1. 在宿主机上确保路径 `/Volumes/myDriver/Docker/Streamlit/文档` 存在
            2. 将Excel答题卡文件放入该目录
            3. 文件命名格式：`班别_姓名.xlsx`
            4. 刷新页面后即可选择导入
            **💡 注意：** 这是外部存储路径，通过docker-compose.yml挂载到容器
            """
            )

        # 添加本地文件上传功能
        st.subheader("💻 本地文件上传")
        st.info("您可以直接上传Excel文件进行导入")

        # 使用st.file_uploader允许用户上传多个Excel文件
        uploaded_files = st.file_uploader(
            "选择Excel文件上传",
            type=["xlsx"],
            accept_multiple_files=True,
            key=f"local_file_uploader_{st.session_state.local_file_uploader_key}",
        )

        # 处理上传的文件
        if uploaded_files:
            local_files_processed = False
            local_error_messages = []

            for uploaded_file in uploaded_files:
                try:
                    # 获取上传的文件名
                    file_name = uploaded_file.name

                    # 检查文件是否已经处理过
                    if file_name in st.session_state.processed_local_files:
                        continue

                    # 根据文件名，获取班别名和创建者
                    try:
                        class_name = file_name.split(".")[0].split("_")[-2]
                        creator = file_name.split(".")[0].split("_")[-1]
                    except IndexError:
                        local_error_messages.append(
                            f"文件 '{file_name}' 命名格式不正确，请按照'班别_姓名.xlsx'格式命名"
                        )
                        continue

                    # 创建临时文件来保存上传的文件内容
                    with tempfile.NamedTemporaryFile(
                        suffix=".xlsx", delete=False
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name

                    # 读取上传的Excel文件
                    try:
                        df = read_xlsx(tmp_file_path)
                    except Exception as e:
                        local_error_messages.append(
                            f"文件 '{file_name}' 读取失败：{str(e)}"
                        )
                        # 清理临时文件
                        os.unlink(tmp_file_path)
                        continue

                    # 数据导入数据库
                    success, message = to_sql_questions(df, creator, class_name)

                    # 清理临时文件
                    os.unlink(tmp_file_path)

                    if success:
                        # 标记文件为已处理
                        st.session_state.processed_local_files.add(file_name)
                        local_files_processed = True
                        st.success(f"✅ 成功导入: {file_name}")

                        # 如果是admin文件，给出特殊提示
                        if "admin" in file_name.lower():
                            st.info("🚨 注意：已导入标准答案文件")
                    else:
                        local_error_messages.append(
                            f"文件 '{file_name}' 导入失败：{message}"
                        )

                except Exception as e:
                    local_error_messages.append(
                        f"文件 '{uploaded_file.name}' 处理时发生未知错误：{str(e)}"
                    )

            # 显示本地文件上传的错误消息
            if local_error_messages:
                for error_msg in local_error_messages:
                    st.error(error_msg)

            # 显示本地文件上传状态
            if local_files_processed:
                st.success("🎉 上传的文件已成功导入！")
                # 重置file_uploader状态
                st.session_state.local_file_uploader_key += 1
                # 清理已处理文件记录
                st.session_state.processed_local_files = set()
                # 重新加载页面以反映更改
                st.experimental_rerun()


# 显示content内容
def show_content(question_df):
    # 显示文件导入功能
    show_file_import_section()

    # 侧边栏 - 操作功能
    with st.sidebar:
        # 只有在题目不为空时才显示删除和导出功能
        if not question_df.empty:
            # 由于st.form不能在sidebar中使用，我们改用st.button
            if st.button("删除所有题目"):
                if del_question_data(id=0):
                    st.success("✅ 题目已清空！")
                    # 重新加载页面以反映更改
                    st.experimental_rerun()
                else:
                    st.error("❌ 删除失败！")

            @st.cache_data
            def convert_df(question_df):
                return question_df.to_csv().encode("utf_8_sig")

            csv = convert_df(question_df)

            st.download_button(
                label="📥 导出题目详情为CSV",
                data=csv,
                file_name="题目详情.csv",
                mime="text/csv",
            )
        else:
            st.info("暂无题目数据可操作")

        # 在侧边栏最下方添加模板下载和查看命名示例功能
        st.markdown("---")

        # 下载模板按钮
        st.subheader("📥 模板下载")
        col1, col2 = st.columns(2)

        with col1:
            # download_btn控件，下载导入模板
            with open("./template/班别_admin.xlsx", "rb") as file:
                st.download_button(
                    label="标准答案模板",
                    data=file,
                    file_name="班别_admin.xlsx",
                    mime="ms-excel",
                )

        with col2:
            # download_btn控件，下载导入模板
            with open("./template/班别_姓名.xlsx", "rb") as file:
                st.download_button(
                    label="答题卡模板",
                    data=file,
                    file_name="班别_姓名.xlsx",
                    mime="ms-excel",
                )

        st.markdown("---")

        st.warning(
            "💡 **重要提示：**\n"
            "1. 先导入标准答案答题卡，再导入学生答题卡\n"
            "2. 答题卡的名字一定要按照模板文档修改"
        )

        # 示例图片显示
        if st.button("📷 查看命名示例"):
            st.image("images/1.png", "命名样例")
            st.image("images/2.png", "表内容样例-红色内容不能修改")

    # 主内容区域 - 显示题目数据表格
    if not question_df.empty:
        # aggrid控件显示题目数据
        grid_res = aggrid_question(question_df)

        # 如果需要单独删除某些选中的题目，可以在这里添加额外的逻辑
        # 但由于我们已经将删除所有题目的功能移到了侧边栏，这里主要只用于显示

    else:
        st.error("❌ 题目为空！请先导入数据。")


def main():
    # 从数据库获取，题目信息
    question_df = out_sql("questions")
    student_df = out_sql("students")

    # 显示content页（已集成文件导入功能）
    show_content(question_df)


if __name__ == "__main__":
    main()
