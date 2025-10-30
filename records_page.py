import streamlit as st
import pandas as pd

from aggrid import aggrid_student
from db_operator import (
    out_sql,
    del_student_data,
)


# 显示content内容
def show_content(student_df):
    # 侧边栏 - 页面标题和功能按钮
    with st.sidebar:
        st.subheader("📊 学生成绩汇总")

        # 只有在学生数据不为空时才显示删除和导出功能
        if not student_df.empty:
            # 由于st.form不能在sidebar中使用，我们改用st.button
            if st.button("删除所有学生"):
                if del_student_data(id=0):
                    st.success("✅ 学生已清空！")
                    # 重新加载页面以反映更改
                    st.experimental_rerun()
                else:
                    st.error("❌ 删除失败！")

            @st.cache_data
            def convert_df(student_df):
                return student_df.to_csv().encode("utf_8_sig")

            csv = convert_df(student_df)

            st.download_button(
                label="📥 导出学生总分为CSV",
                data=csv,
                file_name="学生总分.csv",
                mime="text/csv",
            )
        else:
            st.info("暂无学生数据可操作")

    # 主内容区域 - 显示学生数据表格
    if not student_df.empty:
        # aggrid控件显示学生数据
        grid_res = aggrid_student(student_df)

        # 如果需要单独删除某些选中的学生，可以在这里添加额外的逻辑
        # 但由于我们已经将删除所有学生的功能移到了侧边栏，这里主要只用于显示

    else:
        st.error("❌ 学生为空！请先导入数据。")


def main():
    # 从数据库获取，学生信息
    student_df = out_sql("students")

    # 显示content页
    show_content(student_df)


if __name__ == "__main__":
    main()
