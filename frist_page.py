import streamlit as st
import pandas as pd

from aggrid import aggrid_question
from sidebar import show_sidebar
from db_operator import (
    out_sql,
    del_question_data,
)


# 显示content内容
def show_content(question_df):
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

            if st.form_submit_button("删除题目", help="删除被选中题目,如果所有题目都没有被选中，则删除所有题目。"):
                if len(selection):
                    for i in selection:
                        del_question_data(i["id"])
                    st.success("题目已删除！")
                else:
                    if del_question_data(id=0):
                        st.success("题目已清空！")
                    else:
                        st.error("删除失败！")

    else:
        st.error("题目为空！请先导入数据。")

        # 导出当前数据

    @st.cache_data
    def convert_df(question_df):
        return question_df.to_csv().encode("utf_8_sig")

    csv = convert_df(question_df)

    st.download_button(
        label="导出题目详情为excel",
        data=csv,
        file_name="题目详情.csv",
        mime="text/csv",
    )


def main():
    # 从数据库获取，题目信息
    question_df = out_sql("questions")
    student_df = out_sql("students")

    # 显示siderbar页
    show_sidebar(question_df, student_df)

    # 显示content页
    show_content(question_df)

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
