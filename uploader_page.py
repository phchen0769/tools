import streamlit as st
import os
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
from utils import chinese_sort_key  # 添加utils模块导入

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

    management_option = st.sidebar.radio(
        "选择操作", ["上传文件", "查看文件", "删除文件"]
    )

    if management_option == "上传文件":
        show_upload_section()
    elif management_option == "查看文件":
        show_file_list()
    elif management_option == "删除文件":
        show_delete_section()


def show_file_list():
    """
    显示文件列表
    """
    st.header("📋 文件列表")

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
                files.append(
                    {
                        "文件名": file,
                        "大小": format_file_size(file_stat.st_size),
                        "修改时间": datetime.fromtimestamp(file_stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "路径": file_path,
                    }
                )

    # 使用chinese_sort_key对文件列表进行排序
    if files:
        files.sort(key=lambda x: chinese_sort_key(x["文件名"]))

        # 显示文件表格
        df = pd.DataFrame(files)
        st.dataframe(df, use_container_width=True)

        # 文件预览选项
        st.subheader("🔍 文件预览")
        selected_file = st.selectbox("选择文件预览", [f["文件名"] for f in files])

        if selected_file:
            file_path = os.path.join(category_path, selected_file)
            show_file_preview(file_path)
    else:
        st.info(f"'{selected_category}' 分类中暂无文件。")


def show_delete_section():
    """
    显示文件删除部分
    """
    st.header("🗑️ 删除文件")

    # 获取所有分类
    categories = [
        d
        for d in os.listdir(EXTERNAL_STORAGE_PATH)
        if os.path.isdir(os.path.join(EXTERNAL_STORAGE_PATH, d))
    ]

    if not categories:
        st.info("暂无文件可删除。")
        return

    # 选择分类
    selected_category = st.selectbox("选择分类", categories)
    category_path = os.path.join(EXTERNAL_STORAGE_PATH, selected_category)

    # 获取文件列表
    files = []
    if os.path.exists(category_path):
        files = [
            f
            for f in os.listdir(category_path)
            if os.path.isfile(os.path.join(category_path, f))
        ]

    # 使用chinese_sort_key对文件列表进行排序
    if files:
        files.sort(key=chinese_sort_key)

        # 选择要删除的文件
        files_to_delete = st.multiselect("选择要删除的文件", files)

        if files_to_delete:
            st.warning("⚠️ 即将删除以下文件（此操作不可恢复）：")
            for file in files_to_delete:
                st.write(f"- {file}")

            # 确认删除
            if st.button("确认删除", type="secondary"):
                deleted_count = 0
                for file in files_to_delete:
                    file_path = os.path.join(category_path, file)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        st.success(f"✅ 已删除: {file}")
                    except Exception as e:
                        st.error(f"❌ 删除失败 {file}: {e}")

                if deleted_count > 0:
                    st.success(f"🎉 成功删除 {deleted_count} 个文件！")
    else:
        st.info(f"'{selected_category}' 分类中暂无文件。")


def show_upload_section():
    """
    显示文件上传部分
    """

    # 创建分类目录
    categories = ["文档", "图片", "Excel文件", "其他"]
    selected_category = st.selectbox("选择文件分类", categories)

    # 根据分类创建目录
    category_path = os.path.join(EXTERNAL_STORAGE_PATH, selected_category)
    os.makedirs(category_path, exist_ok=True)

    # 文件上传区域
    uploaded_files = st.file_uploader(
        f"选择要上传到 '{selected_category}' 分类的文件",
        type=[
            "pdf",
            "doc",
            "docx",
            "txt",
            "xlsx",
            "xls",
            "csv",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "bmp",
            "zip",
            "rar",
        ],
        accept_multiple_files=True,
        help="支持多文件上传，最大文件大小：200MB",
    )

    if uploaded_files:
        # 显示上传进度
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            # 更新进度
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(
                f"正在上传 {i+1}/{len(uploaded_files)}: {uploaded_file.name}"
            )

            # 保存文件
            file_path = os.path.join(category_path, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 记录上传信息
            log_upload_info(uploaded_file.name, selected_category, file_path)

        # 完成上传
        progress_bar.empty()
        status_text.empty()
        st.success(
            f"✅ 成功上传 {len(uploaded_files)} 个文件到 '{selected_category}' 分类！"
        )

        # 显示上传统计
        show_upload_stats()


def format_file_size(size_bytes):
    """
    格式化文件大小
    """
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"


def log_upload_info(filename, category, file_path):
    """
    记录上传信息（可扩展为数据库记录）
    """
    # 这里可以扩展为将上传记录保存到数据库
    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.sidebar.info(f"📝 上传记录: {filename} → {category} ({upload_time})")


def show_upload_stats():
    """
    显示上传统计信息
    """
    st.subheader("📊 存储统计")

    total_size = 0
    file_count = 0

    # 计算总文件大小和数量
    for category in os.listdir(EXTERNAL_STORAGE_PATH):
        category_path = os.path.join(EXTERNAL_STORAGE_PATH, category)
        if os.path.isdir(category_path):
            for file in os.listdir(category_path):
                file_path = os.path.join(category_path, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文件总数", file_count)
    with col2:
        st.metric("总存储大小", format_file_size(total_size))
    with col3:
        st.metric(
            "分类数量",
            len(
                [
                    d
                    for d in os.listdir(EXTERNAL_STORAGE_PATH)
                    if os.path.isdir(os.path.join(EXTERNAL_STORAGE_PATH, d))
                ]
            ),
        )


def show_file_preview(file_path):
    """
    显示文件预览（根据文件类型）
    """
    file_ext = Path(file_path).suffix.lower()

    if file_ext in [".txt", ".py", ".csv"]:
        # 文本文件预览
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.text_area("文件内容", content, height=200)
        except:
            st.warning("无法预览此文件内容")

    elif file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
        # 图片预览
        st.image(file_path, use_column_width=True)

    elif file_ext in [".xlsx", ".xls"]:
        # Excel文件预览
        try:
            df = pd.read_excel(file_path)
            st.dataframe(df.head(10), use_container_width=True)
        except:
            st.warning("无法预览Excel文件")

    elif file_ext == ".pdf":
        # PDF文件预览（需要扩展）
        st.info("PDF文件预览功能需要额外配置")

    else:
        st.info("暂不支持此文件类型的预览")


if __name__ == "__main__":
    show_file_upload_page()
