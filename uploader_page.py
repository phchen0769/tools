import streamlit as st
import os
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
import time  # 添加time模块导入
from utils import chinese_sort_key  # 添加utils模块导入
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder, JsCode
import zipfile
import io
import base64


# 外部存储路径（从环境变量获取或使用默认路径）
EXTERNAL_STORAGE_PATH = os.getenv("EXTERNAL_STORAGE_PATH", "/external_storage")


def show_file_upload_page():
    """
    显示文件上传页面
    """

    # 创建外部存储目录（如果不存在）
    os.makedirs(EXTERNAL_STORAGE_PATH, exist_ok=True)

    # 侧边栏：文件管理选项
    st.sidebar.header("📤 上传文件")

    management_option = st.sidebar.radio("选择操作", ["上传文件", "查看文件"])

    if management_option == "上传文件":
        show_upload_section()
    elif management_option == "查看文件":
        show_file_list()


def show_file_list():
    """
    显示文件列表，使用aggrid实现文件查看功能
    """
    st.subheader("📋 文件列表")

    # 获取所有分类
    categories = [
        d
        for d in os.listdir(EXTERNAL_STORAGE_PATH)
        if os.path.isdir(os.path.join(EXTERNAL_STORAGE_PATH, d))
    ]

    if not categories:
        st.info("暂无文件分类，请先上传文件。")
        return

    # 选择分类查看
    selected_category = st.selectbox("选择分类查看", categories)
    category_path = os.path.join(EXTERNAL_STORAGE_PATH, selected_category)

    # 获取文件列表
    files = []
    if os.path.exists(category_path):
        for file in os.listdir(category_path):
            file_path = os.path.join(category_path, file)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                file_ext = Path(file_path).suffix.lower()
                files.append(
                    {
                        "文件名": file,
                        "大小": file_stat.st_size,  # 保持原始大小用于排序
                        "格式化大小": format_file_size(file_stat.st_size),
                        "修改时间": datetime.fromtimestamp(file_stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "分类": selected_category,
                        "路径": file_path,
                    }
                )

    # 使用chinese_sort_key对文件列表进行排序
    if files:
        files.sort(key=lambda x: chinese_sort_key(x["文件名"]))

        # 转换为DataFrame用于aggrid显示
        df = pd.DataFrame(files)

        # 配置aggrid
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=False, sortable=True, filterable=True)

        # 配置列
        gb.configure_column("文件名", width=200)
        gb.configure_column("大小", hide=True)  # 隐藏原始大小列
        gb.configure_column("格式化大小", header_name="大小", width=120)
        gb.configure_column("修改时间", width=200)
        gb.configure_column("分类", width=100)
        gb.configure_column("路径", hide=True)  # 隐藏路径列

        # 配置选择
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)

        # 配置分页
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=30)

        # 构建网格选项
        grid_options = gb.build()

        # 显示aggrid表格，添加key参数以支持刷新
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=False,  # 改为False以使用自定义列宽
            theme="streamlit",
            height=400,
            allow_unsafe_jscode=True,
            key=f"file_grid_{selected_category}_{st.session_state.get('file_list_refresh_key', 0)}",
        )

        # 将选中的行信息保存到session state中，以便在sidebar中访问
        selected_rows = grid_response.get("selected_rows", [])
        st.session_state.selected_rows_for_batch_ops = selected_rows

        # 在侧边栏显示批量操作按钮
        if selected_rows:
            with st.sidebar:
                st.write(f"已选择 {len(selected_rows)} 个文件")

                # 批量下载按钮
                # 创建ZIP文件
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for row in selected_rows:
                        file_path = row["路径"]
                        file_name = row["文件名"]
                        # 将文件添加到ZIP中
                        zip_file.write(file_path, file_name)

                # 准备下载
                zip_buffer.seek(0)
                # 直接提供下载按钮
                st.download_button(
                    label="📥 下载选中文件",
                    data=zip_buffer,
                    file_name=f"{selected_category}_选中文件.zip",
                    mime="application/zip",
                    key="batch_download_sidebar",
                )

                # 批量删除按钮
                if st.button("🗑️ 删除选中文件", key="batch_delete_sidebar"):
                    # 执行批量删除
                    deleted_count = 0
                    for row in selected_rows:
                        file_path = row["路径"]
                        file_name = row["文件名"]
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            st.error(f"❌ 删除失败 {file_name}: {e}")

                    if deleted_count > 0:
                        st.success(f"🎉 成功删除 {deleted_count} 个文件！")
                        # 更新刷新键以强制重新加载表格
                        if "file_list_refresh_key" not in st.session_state:
                            st.session_state.file_list_refresh_key = 0
                        st.session_state.file_list_refresh_key += 1
                        # 短暂延迟确保消息显示，然后重新加载页面
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        # 即使没有删除成功，也更新刷新键以清除选择状态
                        if "file_list_refresh_key" not in st.session_state:
                            st.session_state.file_list_refresh_key = 0
                        st.session_state.file_list_refresh_key += 1
    else:
        st.info(f"'{selected_category}' 分类中暂无文件。")


def format_file_size(size_bytes):
    """
    格式化文件大小显示
    """
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"


def get_mime_type(file_extension):
    """
    根据文件扩展名返回MIME类型
    """
    mime_types = {
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    return mime_types.get(file_extension.lower(), "application/octet-stream")


def show_upload_section():
    """
    显示文件上传部分
    """
    st.subheader("📤 上传文件")

    # 获取现有分类
    categories = [
        d
        for d in os.listdir(EXTERNAL_STORAGE_PATH)
        if os.path.isdir(os.path.join(EXTERNAL_STORAGE_PATH, d))
    ]

    # 选择或创建分类
    if categories:
        category_option = st.radio("选择操作", ["选择现有分类", "创建新分类"])
        if category_option == "选择现有分类":
            selected_category = st.selectbox("选择分类", categories)
        else:
            new_category = st.text_input("输入新分类名称")
            selected_category = new_category if new_category else None
    else:
        st.info("暂无现有分类，请创建新分类。")
        new_category = st.text_input("输入新分类名称")
        selected_category = new_category if new_category else None

    if selected_category:
        category_path = os.path.join(EXTERNAL_STORAGE_PATH, selected_category)
        os.makedirs(category_path, exist_ok=True)

        # 文件上传
        uploaded_files = st.file_uploader(
            "选择文件上传", accept_multiple_files=True, key="file_uploader"
        )

        if uploaded_files:
            success_count = 0
            for uploaded_file in uploaded_files:
                try:
                    # 保存文件
                    file_path = os.path.join(category_path, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    success_count += 1
                except Exception as e:
                    st.error(f"❌ 上传失败 {uploaded_file.name}: {e}")

            if success_count > 0:
                st.success(f"🎉 成功上传 {success_count} 个文件！")
                # 更新刷新键以强制重新加载表格
                if "file_list_refresh_key" not in st.session_state:
                    st.session_state.file_list_refresh_key = 0
                st.session_state.file_list_refresh_key += 1
                # 短暂延迟确保消息显示，然后重新加载页面
                time.sleep(1)
                st.experimental_rerun()
