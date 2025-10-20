import streamlit as st
import pandas as pd

from aggrid import aggrid_student
from sidebar import show_sidebar
from db_operator import (
    out_sql,
    del_student_data,
)


# 显示content内容
def show_content(student_df):
    # form控件，题目不为空，显示控件
    if not student_df.empty:
        # form控件，表单
        with st.form("question_form"):
            # aggrid控件
            grid_res = aggrid_student(student_df)
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
            if st.form_submit_button("删除学生", help="删除被选中学生,如果所有学生都没有被选中，则删除所有学生。"):
                if len(selection):
                    for i in selection:
                        del_student_data("Student", i["id"])
                    st.success("学生已删除！")
                else:
                    if del_student_data(id=0):
                        st.success("学生已清空！")
                    else:
                        st.error("删除失败！")

    else:
        st.error("学生为空！请先导入数据。")

    # 导出按钮，导出当前数据
    @st.cache_data
    def convert_df(studnet_df):
        return student_df.to_csv().encode("utf_8_sig")

    csv = convert_df(student_df)

    st.download_button(
        label="导出学生总分为excel",
        data=csv,
        file_name="学生总分.csv",
        mime="text/csv",
    )


def main():
    # 从数据库获取，题目信息
    question_df = out_sql("questions")
    student_df = out_sql("students")

    # 显示siderbar页
    show_sidebar(question_df, student_df)

    # 显示content页
    show_content(student_df)

    # congtainer内容减少padding
    st.markdown(
        """<style>
                        
                        .block-container.st-emotion-cache-z5fcl4.ea3mdgi4{
                            padding:10px;
                        }
                        
                        </style>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
