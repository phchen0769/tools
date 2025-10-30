import os
import re
import shutil
import streamlit as st
import zipfile
from datetime import datetime
from utils import chinese_sort_key  # 从utils模块导入排序函数


# 添加中文排序函数
def chinese_sort_key(filename):
    """
    为中文文件名生成排序键，支持数字自然排序和汉字拼音排序
    """
    # 移除文件扩展名，获取完整的文件名（不含扩展名）
    name_without_ext = os.path.splitext(filename)[0]

    # 使用正则表达式将文件名分割为数字和非数字部分
    import re

    parts = re.split(r"(\d+)", name_without_ext)

    # 处理每个部分，将数字转换为数值，非数字部分进行拼音转换
    sort_key = []
    for part in parts:
        if part.isdigit():
            # 数字部分转换为整数，确保数值比较（1 < 2 < 10）
            sort_key.append(int(part))
        else:
            # 非数字部分进行拼音转换
            try:
                from pypinyin import pinyin, Style

                pinyin_list = []
                for item in pinyin(part, style=Style.NORMAL):
                    if item:
                        pinyin_list.append(item[0].lower())
                # 将拼音列表转换为字符串，确保可比较
                sort_key.append("".join(pinyin_list))
            except ImportError:
                # 如果没有安装pypinyin，使用Unicode编码进行简单排序
                sort_key.append(part.lower())

    # 返回一个元组，确保所有元素都是可比较的类型
    return tuple(sort_key)


def extract_name_from_filename(
    filename,
    delimiter="_",
    keep_parts="last:2",
    replacement_pattern="",
    custom_rule="",
    rename_list=None,
):
    """
    从文件名中提取目标名称，支持自定义分隔符和部分选择

    Args:
        filename: 原始文件名
        delimiter: 分隔符，默认为下划线
        keep_parts: 保留的部分，格式如 'first:2'（前2个）, 'last:2'（后2个）, 'range:1-3'（第1到第3个）
        replacement_pattern: 替换模式，用于替换分隔符
        custom_rule: 自定义重命名规则
        rename_list: 重命名名称列表

    Examples:
        extract_name_from_filename("2506106_dengzhizhong_练习1_张三.xlsx", "_", "last:2")
        -> "练习1_张三.xlsx"

        extract_name_from_filename("2506106-dengzhizhong-练习1-张三.xlsx", "-", "range:3-4")
        -> "练习1-张三.xlsx"
    """
    # 如果提供了重命名列表，按顺序重命名
    if rename_list and isinstance(rename_list, list):
        # 获取当前文件在列表中的索引
        file_index = (
            len([f for f in os.listdir(".") if f.startswith("temp_")])
            if "temp_" in filename
            else 0
        )
        # 按顺序分配名称
        if file_index < len(rename_list):
            new_name = rename_list[file_index]
            # 保留原文件扩展名
            return f"{new_name}{os.path.splitext(filename)[1]}"

    # 如果提供了自定义规则，优先使用自定义规则
    if custom_rule:
        # 移除文件扩展名
        name_without_ext = os.path.splitext(filename)[0]
        # 应用自定义规则
        new_name = custom_rule.replace("{filename}", name_without_ext)
        # 添加回扩展名
        return f"{new_name}{os.path.splitext(filename)[1]}"

    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]

    # 按分隔符分割文件名
    parts = name_without_ext.split(delimiter)

    # 解析保留部分的规则
    selected_parts = []
    if keep_parts.startswith("first:"):
        # 保留前n个部分
        n = int(keep_parts.split(":")[1])
        selected_parts = parts[:n]
    elif keep_parts.startswith("last:"):
        # 保留后n个部分
        n = int(keep_parts.split(":")[1])
        selected_parts = parts[-n:] if len(parts) >= n else parts
    elif keep_parts.startswith("range:"):
        # 保留指定范围的部分 (1-indexed)
        range_str = keep_parts.split(":")[1]
        start, end = map(int, range_str.split("-"))
        # 转换为0-indexed并处理边界
        start = max(0, start - 1)
        end = min(len(parts), end)
        selected_parts = parts[start:end]
    elif keep_parts.startswith("custom:"):
        # 自定义索引，如 'custom:0,2,3'
        indices = [int(i) for i in keep_parts.split(":")[1].split(",")]
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


def rename_files_in_directory(
    source_dir,
    target_dir,
    delimiter="_",
    keep_parts="last:2",
    replacement_pattern="",
    custom_rule="",
    rename_list=None,
    preview_only=True,
):
    """
    重命名目录中的文件

    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        delimiter: 文件名分隔符
        keep_parts: 保留的部分设置
        replacement_pattern: 替换模式
        custom_rule: 自定义重命名规则
        rename_list: 重命名名称列表
        preview_only: 是否仅预览而不实际重命名

    Returns:
        list: 包含原始文件名和新文件名的元组列表
    """
    renamed_files = []

    # 支持的文件类型
    supported_extensions = [
        ".xlsx",
        ".xls",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".py",
        ".txt",
        ".csv",
        ".pdf",
    ]

    # 获取文件列表并按中文文件名排序
    files = [
        f
        for f in os.listdir(source_dir)
        if os.path.splitext(f)[1].lower() in supported_extensions and f != ".DS_Store"
    ]

    # 按中文文件名排序（汉字按字母顺序）
    files = sorted(files, key=chinese_sort_key)

    # 遍历源目录中的所有文件
    for i, filename in enumerate(files):
        old_path = os.path.join(source_dir, filename)

        # 根据重命名模式生成新文件名
        if rename_list and isinstance(rename_list, list):
            # 按顺序重命名
            if i < len(rename_list):
                new_name = rename_list[i]
                # 保留原文件扩展名
                new_filename = f"{new_name}{os.path.splitext(filename)[1]}"
            else:
                new_filename = filename
        else:
            # 使用其他规则重命名
            new_filename = extract_name_from_filename(
                filename, delimiter, keep_parts, replacement_pattern, custom_rule
            )

        new_path = os.path.join(target_dir, new_filename)

        # 如果不是预览模式，则执行重命名操作
        if not preview_only:
            # 如果源目录和目标目录相同，直接重命名文件
            if source_dir == target_dir:
                if filename != new_filename:  # 只有当文件名不同时才重命名
                    os.rename(old_path, new_path)
            else:
                # 如果目标目录不同，确保目标目录存在
                os.makedirs(target_dir, exist_ok=True)
                # 复制文件到目标目录
                shutil.copy2(old_path, new_path)

        renamed_files.append((filename, new_filename))

    return renamed_files


def parse_rename_list(text):
    """
    解析重命名列表文本，提取名称
    """
    rename_list = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line:  # 只添加非空行
            rename_list.append(line)

    return rename_list


def show_file_rename_page():
    """显示文件重命名页面"""
    st.title("文件批量重命名工具")
    st.markdown("---")

    # 说明文字
    st.info(
        """
    此工具可以根据自定义规则批量重命名文件。
    例如将 `2506106_dengzhizhong_练习1_张三.xlsx` 重命名为 `练习1_张三.xlsx`。
    支持的文件类型：Excel文件(.xlsx, .xls)、图片文件(.jpg, .jpeg, .png, .gif, .bmp)、Python源码(.py)等。
    """
    )

    # 侧边栏 - 重命名配置
    with st.sidebar:
        st.header("重命名配置")

        # 重命名模式选择
        st.subheader("重命名模式")
        rename_mode = st.radio(
            "选择重命名模式:",
            options=["名称列表顺序重命名", "自定义规则", "分隔符规则"],
            index=0,
        )

        rename_list = None
        custom_rule = ""
        delimiter = "_"
        keep_parts = "last:2"
        replacement_pattern = ""

        if rename_mode == "名称列表顺序重命名":
            st.subheader("名称列表顺序重命名")
            st.info("请输入名称列表，每行一个名称，文件将按顺序重命名为这些名称")

            rename_text = st.text_area(
                "名称列表:",
                height=300,
                help="请输入名称列表，每行一个名称，文件将按顺序重命名为这些名称",
            )

            # 解析重命名列表
            if rename_text:
                rename_list = parse_rename_list(rename_text)

        elif rename_mode == "自定义规则":
            st.subheader("自定义重命名规则")
            custom_rule = st.text_area(
                "自定义重命名规则:",
                placeholder="例如：新文件_{filename}_2024\n使用 {filename} 代表原文件名（不含扩展名）",
                help="输入自定义的重命名规则，可以使用 {filename} 作为原文件名的占位符",
            )

        else:  # 分隔符规则
            st.subheader("分隔符重命名规则")
            # 分隔符设置
            delimiter = st.text_input(
                "文件名分隔符:", value="_", help="用于分割文件名的字符，如 '_'、'-' 等"
            )

            # 保留部分设置
            keep_parts_option = st.radio(
                "选择保留的部分:",
                options=[
                    "保留前N个部分",
                    "保留后N个部分",
                    "保留指定范围的部分",
                    "自定义指定部分",
                ],
                index=1,
            )

            if keep_parts_option == "保留前N个部分":
                n_first = st.number_input(
                    "保留前几个部分:", min_value=1, value=2, step=1
                )
                keep_parts = f"first:{n_first}"
            elif keep_parts_option == "保留后N个部分":
                n_last = st.number_input(
                    "保留后几个部分:", min_value=1, value=2, step=1
                )
                keep_parts = f"last:{n_last}"
            elif keep_parts_option == "保留指定范围的部分":
                col1, col2 = st.columns(2)
                with col1:
                    range_start = st.number_input(
                        "起始位置(从1开始):", min_value=1, value=1, step=1
                    )
                with col2:
                    range_end = st.number_input(
                        "结束位置:",
                        min_value=range_start,
                        value=range_start + 1,
                        step=1,
                    )
                keep_parts = f"range:{range_start}-{range_end}"
            elif keep_parts_option == "自定义指定部分":
                custom_indices = st.text_input(
                    "指定部分索引(从0开始，用逗号分隔):",
                    value="0,2,3",
                    help="例如: 0,2,3 表示保留第1、第3、第4个部分",
                )
                keep_parts = f"custom:{custom_indices}"

            # 分隔符替换设置
            replacement_pattern = st.text_input(
                "新分隔符(留空则保持原分隔符):",
                help="用于替换原分隔符的新字符，如 '-'、'_' 或其他字符",
            )

        # 规则预览
        if rename_mode == "名称列表顺序重命名" and rename_list:
            st.info(f"当前规则预览: 按名称列表顺序重命名，共 {len(rename_list)} 个名称")
        elif rename_mode == "自定义规则" and custom_rule:
            st.info(f"当前规则预览: 自定义规则 - {custom_rule}")
        else:
            st.info(
                f"当前规则预览: 使用 '{delimiter}' 分割文件名，{keep_parts_option if rename_mode == '分隔符规则' else '自定义规则'}，新分隔符: '{replacement_pattern or delimiter}'"
            )

    # 主页面 - 文件选择和重命名操作
    st.markdown("---")

    # 从本地文件夹读取文件
    st.subheader("选择文件目录")

    # 外部存储路径（从环境变量获取或使用默认路径）
    EXTERNAL_STORAGE_PATH = os.getenv("EXTERNAL_STORAGE_PATH", "/external_storage")

    # 获取/external_storage目录下的所有子目录
    available_dirs = []
    if os.path.exists(EXTERNAL_STORAGE_PATH) and os.path.isdir(EXTERNAL_STORAGE_PATH):
        available_dirs = [
            d
            for d in os.listdir(EXTERNAL_STORAGE_PATH)
            if os.path.isdir(os.path.join(EXTERNAL_STORAGE_PATH, d))
        ]
        available_dirs = sorted(available_dirs)

    # 添加根目录选项
    available_dirs.insert(0, "根目录 (/external_storage)")

    # 选择目录
    selected_dir_option = st.selectbox(
        "请选择要处理的目录:",
        options=available_dirs,
        help="选择包含需要重命名文件的目录",
    )

    # 确定实际路径
    if selected_dir_option == "根目录 (/external_storage)":
        local_folder_path = EXTERNAL_STORAGE_PATH
    else:
        local_folder_path = os.path.join(EXTERNAL_STORAGE_PATH, selected_dir_option)

    st.info(f"当前选择的目录: {local_folder_path}")

    if (
        local_folder_path
        and os.path.exists(local_folder_path)
        and os.path.isdir(local_folder_path)
    ):
        # 获取文件夹中的文件
        supported_extensions = [
            ".xlsx",
            ".xls",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".py",
            ".txt",
            ".csv",
            ".pdf",
        ]

        files = [
            f
            for f in os.listdir(local_folder_path)
            if os.path.isfile(os.path.join(local_folder_path, f))
            and os.path.splitext(f)[1].lower() in supported_extensions
        ]

        if files:
            # 按中文文件名排序
            files = sorted(files, key=chinese_sort_key)

            st.success(f"在文件夹中找到 {len(files)} 个支持的文件:")
            st.write(files)

            # 预览重命名结果
            st.subheader("重命名预览")
            renamed_files = rename_files_in_directory(
                local_folder_path,
                local_folder_path,  # 使用同一个目录进行预览
                delimiter=delimiter,
                keep_parts=keep_parts,
                replacement_pattern=replacement_pattern,
                custom_rule=custom_rule,
                rename_list=rename_list,
                preview_only=True,
            )

            if renamed_files:
                # 显示预览表格
                preview_data = []
                for i, (old_name, new_name) in enumerate(renamed_files):
                    status = "✅ 将被重命名" if old_name != new_name else "ℹ️ 无需更改"
                    preview_data.append(
                        {
                            "原始文件名": old_name,
                            "新文件名": new_name,
                            "状态": status,
                        }
                    )
                st.table(preview_data)

                # 选择重命名方式
                st.subheader("重命名操作")
                rename_method = st.radio(
                    "选择重命名方式:",
                    options=["直接重命名目录中的文件", "下载重命名后的文件"],
                    index=0,
                    help="选择直接修改目录中的文件或下载重命名后的文件",
                )

                if rename_method == "直接重命名目录中的文件":
                    # 直接重命名目录中的文件
                    if st.button("执行重命名", type="primary"):
                        try:
                            # 执行实际的重命名操作
                            actual_renamed_files = rename_files_in_directory(
                                local_folder_path,
                                local_folder_path,  # 使用同一个目录进行实际重命名
                                delimiter=delimiter,
                                keep_parts=keep_parts,
                                replacement_pattern=replacement_pattern,
                                custom_rule=custom_rule,
                                rename_list=rename_list,
                                preview_only=False,  # 实际执行重命名
                            )

                            if actual_renamed_files:
                                # 显示重命名结果
                                result_data = []
                                renamed_count = 0
                                for i, (old_name, new_name) in enumerate(
                                    actual_renamed_files
                                ):
                                    if old_name != new_name:
                                        renamed_count += 1
                                        status = "✅ 已重命名"
                                    else:
                                        status = "ℹ️ 无需更改"

                                    result_data.append(
                                        {
                                            "原始文件名": old_name,
                                            "新文件名": new_name,
                                            "状态": status,
                                        }
                                    )

                                st.success(f"成功重命名 {renamed_count} 个文件！")
                                st.table(result_data)

                                # 显示重命名后的文件列表
                                st.subheader("重命名后的文件列表")
                                new_files = [
                                    f
                                    for f in os.listdir(local_folder_path)
                                    if os.path.isfile(
                                        os.path.join(local_folder_path, f)
                                    )
                                    and os.path.splitext(f)[1].lower()
                                    in supported_extensions
                                ]
                                new_files = sorted(new_files, key=chinese_sort_key)
                                st.write(new_files)
                            else:
                                st.warning("没有找到有效的文件进行重命名。")

                        except Exception as e:
                            st.error(f"重命名过程中出现错误: {str(e)}")

                else:
                    # 下载重命名后的文件
                    if st.button("执行重命名并下载文件"):
                        # 创建临时目录用于处理文件
                        temp_processing_dir = "temp_processing"
                        if os.path.exists(temp_processing_dir):
                            shutil.rmtree(temp_processing_dir)
                        os.makedirs(temp_processing_dir, exist_ok=True)

                        # 创建ZIP文件缓冲区
                        import zipfile
                        from io import BytesIO

                        # 执行重命名操作到临时目录
                        actual_renamed_files = rename_files_in_directory(
                            local_folder_path,
                            temp_processing_dir,  # 重命名到临时目录
                            delimiter=delimiter,
                            keep_parts=keep_parts,
                            replacement_pattern=replacement_pattern,
                            custom_rule=custom_rule,
                            rename_list=rename_list,
                            preview_only=False,
                        )

                        if actual_renamed_files:
                            # 创建ZIP文件
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(
                                zip_buffer, "w", zipfile.ZIP_DEFLATED
                            ) as zip_file:
                                for root, dirs, files in os.walk(temp_processing_dir):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        # 在ZIP文件中保持相对路径
                                        arcname = os.path.relpath(
                                            file_path, temp_processing_dir
                                        )
                                        zip_file.write(file_path, arcname)

                            # 提供下载链接
                            st.success("重命名完成！点击下方按钮下载重命名后的文件。")
                            st.download_button(
                                label="📥 下载重命名后的文件",
                                data=zip_buffer.getvalue(),
                                file_name=f"renamed_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                            )

                            # 清理临时目录
                            shutil.rmtree(temp_processing_dir)
                        else:
                            st.warning("没有找到有效的文件进行重命名。")
            else:
                st.warning("没有找到有效的文件进行重命名预览。")
        else:
            st.warning("选择的目录中没有找到支持的文件。")
    else:
        st.error("选择的目录不存在或不是有效目录。")


if __name__ == "__main__":
    show_file_rename_page()
