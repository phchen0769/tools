import os
import re
import streamlit as st
import shutil
from pathlib import Path

def extract_name_from_filename(filename, delimiter='_', keep_parts='last:2', replacement_pattern=''):
    """
    从文件名中提取目标名称，支持自定义分隔符和部分选择
    
    Args:
        filename: 原始文件名
        delimiter: 分隔符，默认为下划线
        keep_parts: 保留的部分，格式如 'first:2'（前2个）, 'last:2'（后2个）, 'range:1-3'（第1到第3个）
        replacement_pattern: 替换模式，用于替换分隔符
    
    Examples:
        extract_name_from_filename("2506106_dengzhizhong_练习1_张三.xlsx", "_", "last:2")
        -> "练习1_张三.xlsx"
        
        extract_name_from_filename("2506106-dengzhizhong-练习1-张三.xlsx", "-", "range:3-4")
        -> "练习1-张三.xlsx"
    """
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 按分隔符分割文件名
    parts = name_without_ext.split(delimiter)
    
    # 解析保留部分的规则
    selected_parts = []
    if keep_parts.startswith('first:'):
        # 保留前n个部分
        n = int(keep_parts.split(':')[1])
        selected_parts = parts[:n]
    elif keep_parts.startswith('last:'):
        # 保留后n个部分
        n = int(keep_parts.split(':')[1])
        selected_parts = parts[-n:] if len(parts) >= n else parts
    elif keep_parts.startswith('range:'):
        # 保留指定范围的部分 (1-indexed)
        range_str = keep_parts.split(':')[1]
        start, end = map(int, range_str.split('-'))
        # 转换为0-indexed并处理边界
        start = max(0, start - 1)
        end = min(len(parts), end)
        selected_parts = parts[start:end]
    elif keep_parts.startswith('custom:'):
        # 自定义索引，如 'custom:0,2,3'
        indices = [int(i) for i in keep_parts.split(':')[1].split(',')]
        selected_parts = [parts[i] for i in indices if 0 <= i < len(parts)]
    else:
        # 默认保留所有部分
        selected_parts = parts
    
    # 如果没有选中任何部分，返回原文件名
    if not selected_parts:
        return filename
    
    # 使用指定的分隔符或替换模式连接部分
    if replacement_pattern:
        # 如果提供了替换模式，则使用它作为分隔符
        new_name = replacement_pattern.join(selected_parts)
    else:
        # 否则使用原始分隔符
        new_name = delimiter.join(selected_parts)
    
    # 添加回扩展名
    return f"{new_name}{os.path.splitext(filename)[1]}"

def rename_files_in_directory(source_dir, target_dir, delimiter='_', keep_parts='last:2', replacement_pattern='', preview_only=False):
    """
    重命名目录中的文件，支持自定义规则
    
    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        delimiter: 分隔符
        keep_parts: 保留的部分规则
        replacement_pattern: 替换分隔符的模式
        preview_only: 是否仅预览而不实际重命名
    
    Returns:
        list: 包含原始文件名和新文件名的元组列表
    """
    renamed_files = []
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 遍历源目录中的所有文件
    for filename in os.listdir(source_dir):
        # 只处理Excel文件
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            old_path = os.path.join(source_dir, filename)
            new_filename = extract_name_from_filename(filename, delimiter, keep_parts, replacement_pattern)
            new_path = os.path.join(target_dir, new_filename)
            
            # 如果不是预览模式，则执行重命名/复制操作
            if not preview_only:
                shutil.copy2(old_path, new_path)
            
            renamed_files.append((filename, new_filename))
    
    return renamed_files

def show_file_rename_page():
    """显示文件重命名页面"""
    st.title("文件批量重命名工具")
    st.markdown("---")
    
    # 说明文字
    st.info("""
    此工具可以根据自定义规则批量重命名文件。
    例如将 `2506106_dengzhizhong_练习1_张三.xlsx` 重命名为 `练习1_张三.xlsx`。
    """)
    
    # 自定义规则设置
    st.subheader("自定义重命名规则")
    
    # 分隔符设置
    delimiter = st.text_input("文件名分隔符:", value="_", help="用于分割文件名的字符，如 '_'、'-' 等")
    
    # 保留部分设置
    keep_parts_option = st.radio(
        "选择保留的部分:",
        options=[
            "保留前N个部分",
            "保留后N个部分", 
            "保留指定范围的部分",
            "自定义指定部分"
        ],
        index=1
    )
    
    keep_parts = "last:2"  # 默认值
    
    if keep_parts_option == "保留前N个部分":
        n_first = st.number_input("保留前几个部分:", min_value=1, value=2, step=1)
        keep_parts = f"first:{n_first}"
    elif keep_parts_option == "保留后N个部分":
        n_last = st.number_input("保留后几个部分:", min_value=1, value=2, step=1)
        keep_parts = f"last:{n_last}"
    elif keep_parts_option == "保留指定范围的部分":
        col1, col2 = st.columns(2)
        with col1:
            range_start = st.number_input("起始位置(从1开始):", min_value=1, value=1, step=1)
        with col2:
            range_end = st.number_input("结束位置:", min_value=range_start, value=range_start+1, step=1)
        keep_parts = f"range:{range_start}-{range_end}"
    elif keep_parts_option == "自定义指定部分":
        custom_indices = st.text_input("指定部分索引(从0开始，用逗号分隔):", value="0,2,3", 
                                     help="例如: 0,2,3 表示保留第1、第3、第4个部分")
        keep_parts = f"custom:{custom_indices}"
    
    # 分隔符替换设置
    replacement_pattern = st.text_input("新分隔符(留空则保持原分隔符):", 
                                      help="用于替换原分隔符的新字符，如 '-'、'_' 或其他字符")
    
    # 规则预览
    st.info(f"当前规则预览: 使用 '{delimiter}' 分割文件名，{keep_parts_option}，新分隔符: '{replacement_pattern or delimiter}'")
    
    st.markdown("---")
    
    # 文件上传区域
    st.subheader("上传需要重命名的文件")
    uploaded_files = st.file_uploader(
        "选择Excel文件 (.xlsx, .xls)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # 创建临时目录存储上传的文件
        temp_upload_dir = "temp_uploads"
        temp_output_dir = "temp_outputs"
        
        # 清理之前的临时目录
        if os.path.exists(temp_upload_dir):
            shutil.rmtree(temp_upload_dir)
        if os.path.exists(temp_output_dir):
            shutil.rmtree(temp_output_dir)
            
        os.makedirs(temp_upload_dir, exist_ok=True)
        os.makedirs(temp_output_dir, exist_ok=True)
        
        # 保存上传的文件
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # 预览重命名结果
        st.subheader("重命名预览")
        renamed_files = rename_files_in_directory(
            temp_upload_dir, 
            temp_output_dir, 
            delimiter=delimiter,
            keep_parts=keep_parts,
            replacement_pattern=replacement_pattern,
            preview_only=True
        )
        
        if renamed_files:
            # 显示预览表格
            preview_data = []
            for old_name, new_name in renamed_files:
                status = "✅ 将被重命名" if old_name != new_name else "ℹ️ 无需更改"
                preview_data.append({
                    "原始文件名": old_name,
                    "新文件名": new_name,
                    "状态": status
                })
            
            st.table(preview_data)
            
            # 显示规则说明
            st.info(f"重命名规则: 使用 '{delimiter}' 分割文件名，{keep_parts_option}，新分隔符: '{replacement_pattern or delimiter}'")
            
            # 执行重命名按钮
            if st.button("执行重命名并下载文件"):
                # 实际执行重命名操作
                actual_renamed_files = rename_files_in_directory(
                    temp_upload_dir, 
                    temp_output_dir, 
                    delimiter=delimiter,
                    keep_parts=keep_parts,
                    replacement_pattern=replacement_pattern,
                    preview_only=False
                )
                
                # 创建下载链接
                st.success(f"成功重命名 {len(actual_renamed_files)} 个文件！")
                
                # 提供打包下载
                import zipfile
                from io import BytesIO
                
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for _, new_name in actual_renamed_files:
                        file_path = os.path.join(temp_output_dir, new_name)
                        if os.path.exists(file_path):
                            zip_file.write(file_path, new_name)
                
                # 下载按钮
                st.download_button(
                    label="下载所有重命名后的文件 (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="重命名后的文件.zip",
                    mime="application/zip"
                )
                
                # 单独下载每个文件
                st.subheader("单独下载文件")
                for _, new_name in actual_renamed_files:
                    file_path = os.path.join(temp_output_dir, new_name)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as file:
                            st.download_button(
                                label=f"下载 {new_name}",
                                data=file,
                                file_name=new_name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
        else:
            st.warning("没有找到有效的Excel文件。")

if __name__ == "__main__":
    show_file_rename_page()