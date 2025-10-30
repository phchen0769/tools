import streamlit as st
import pandas as pd
import os
import glob

from aggrid import aggrid_question
from db_operator import (
    out_sql,
    del_question_data,
    to_sql_questions,
    read_xlsx,
)


# 显示文件导入功能
def show_file_import_section():
    # 初始化会话状态
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
    if "show_success_message" not in st.session_state:
        st.session_state.show_success_message = False
    if "error_messages" not in st.session_state:
        st.session_state.error_messages = []

    # 侧边栏 - 文件导入和模板下载功能
    with st.sidebar:
        st.header("📁 文件管理")

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

        st.markdown("---")

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

            # 显示文件列表供用户选择
            selected_files = st.multiselect(
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
                                st.success(f"✅ 成功导入: {file_name}")
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


# 显示content内容
def show_content(question_df):
    # 显示文件导入功能
    show_file_import_section()

    # 主页面 - 题目详情管理
    st.subheader("📋 题目详情管理")

    # form控件，题目不为空，显示控件
    if not question_df.empty:
        # form控件，表单
        with st.form("question_form"):
            # aggrid控件
            grid_res = aggrid_question(question_df)
            selection = grid_res["selected_rows"]

            # 设置按钮布局
            # col1, col2 = st.columns(2)

            # with col1:
            #     if st.form_submit_button("保存", help="保存修改的题目。"):
            #         if del_data(id=0) and to_sql_questions(grid_res.data):
            #             st.success("题目信息已保存！")
            #         else:
            #             st.error("保存失败！")
            # with col2:
            # form_submit_btn控件，表单提交--删除被选中题目信息

            if st.form_submit_button(
                "🗑️ 删除题目",
                help="删除被选中题目,如果所有题目都没有被选中，则删除所有题目。",
            ):
                if len(selection):
                    for i in selection:
                        del_question_data(i["id"])
                    st.success("✅ 题目已删除！")
                else:
                    if del_question_data(id=0):
                        st.success("✅ 题目已清空！")
                    else:
                        st.error("❌ 删除失败！")

    else:
        st.error("❌ 题目为空！请先导入数据。")

    # 导出当前数据
    @st.cache_data
    def convert_df(question_df):
        return question_df.to_csv().encode("utf_8_sig")

    csv = convert_df(question_df)

    st.download_button(
        label="📊 导出题目详情为CSV",
        data=csv,
        file_name="题目详情.csv",
        mime="text/csv",
    )


def main():
    # 从数据库获取，题目信息
    question_df = out_sql("questions")
    student_df = out_sql("students")

    # 显示content页（已集成文件导入功能）
    show_content(question_df)


if __name__ == "__main__":
    main()
