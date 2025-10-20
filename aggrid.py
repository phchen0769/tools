import streamlit as st
from st_aggrid import (
    AgGrid,
    JsCode,
    DataReturnMode,
    GridUpdateMode,
    GridOptionsBuilder,
)

# JS方法，用于增加一行到AgGrid表格
js_add_row = JsCode(
    """
function(e) {
    let api = e.api;
    let rowPos = e.rowIndex + 1;
    // 数据转换成JSON
    api.applyTransaction({addIndex: rowPos, add: [{}]})
    };
"""
)

# 为'🌟'列增加一个按钮
cellRenderer_addButton = JsCode(
    """
    class BtnCellRenderer {
        init(params) {
            this.params = params;
            this.eGui = document.createElement('div');
            this.eGui.innerHTML = `
            <span>
                <style>
                .btn_add {
                    background-color: #EAECEE;
                    # border: 1px solid black;
                    color: #AEB6BF;
                    text-align: center;
                    display: inline-block;
                    font-size: 12px;
                    font-weight: bold;
                    height: 2em;
                    width: 5em;
                    border-radius: 12px;
                    padding: 0px;
                }
                </style>
                <button id='click-button' 
                    class="btn_add" 
                    >&#x2193; 添加</button>
            </span>
        `;
        }
        getGui() {
            return this.eGui;
        }
    };
    """
)


# 定义动态表格，并返回操作数据
def aggrid_question(question_df):
    if question_df.empty:
        # 创建一个空容器，用于占位
        container = st.container()
        container.markdown("# 题目为空！")
    else:
        gd = GridOptionsBuilder.from_dataframe(question_df)
        # 打开ag-grid调试信息,选择后输出调试信息
        # gd.configure_grid_options(onRowSelected=js_console)
        # 配置列的默认设置
        # gd.configure_auto_height(autoHeight=True)
        gd.configure_default_column(
            # # 可编辑
            editable=True,
        )
        gd.configure_column(
            field="id",
            header_name="序号",
            width=70,
        )
        gd.configure_column(
            field="question",
            header_name="题目",
            width=400,
        )
        gd.configure_column(
            field="answer",
            header_name="答案",
            width=120,
        )
        gd.configure_column(
            field="score",
            header_name="分数",
            width=50,
        )
        gd.configure_column(
            field="creator",
            header_name="创建者",
            width=70,
        )
        gd.configure_column(
            field="class_name",
            header_name="班级名称",
            width=70,
        )
        gd.configure_column(
            field="add_time",
            header_name="添加时间",
            width=100,
        )
        gd.configure_column(
            field="🌟",
            onCellClicked=js_add_row,
            cellRenderer=cellRenderer_addButton,
            lockPosition="left",
            width=70,
        )
        gd.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            # 预选
            # pre_selected_rows=[{"id": 1}, {"id": 2}],
            # suppressRowClickSelection=False,
        )
        # 表格右侧工具栏
        # gd.configure_side_bar()
        # 分页
        gd.configure_pagination(
            # 取消自动分页
            paginationAutoPageSize=False,
            # 30页一分页
            paginationPageSize=30,
        )

        gridoptions = gd.build()

        # 渲染表格
        grid_res = AgGrid(
            question_df,
            gridOptions=gridoptions,
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.GRID_CHANGED,
            data_return_mode=DataReturnMode.AS_INPUT,
            allow_unsafe_jscode=True,
            theme="streamlit",
            # streamlit,alpine,balham,material
        )
        # 返回数据
        return grid_res


# 定义动态表格，并返回操作数据
def aggrid_student(student_df):
    if student_df.empty:
        # 创建一个空容器，用于占位
        container = st.container()
        container.markdown("# 学生为空！")
    else:
        gd = GridOptionsBuilder.from_dataframe(student_df)
        # 打开ag-grid调试信息,选择后输出调试信息
        # gd.configure_grid_options(onRowSelected=js_console)
        # 配置列的默认设置
        # gd.configure_auto_height(autoHeight=True)
        gd.configure_default_column(
            # # 可编辑
            editable=True,
        )
        gd.configure_column(
            field="id",
            header_name="序号",
            width=70,
        )
        gd.configure_column(
            field="name",
            header_name="姓名",
            width=70,
        )
        gd.configure_column(
            field="score",
            header_name="分数",
            width=50,
        )
        gd.configure_column(
            field="class_name",
            header_name="班级名称",
            width=70,
        )
        gd.configure_column(
            field="🌟",
            onCellClicked=js_add_row,
            cellRenderer=cellRenderer_addButton,
            lockPosition="left",
            width=70,
        )
        gd.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            # 预选
            # pre_selected_rows=[{"id": 1}, {"id": 2}],
            # suppressRowClickSelection=False,
        )
        # 表格右侧工具栏
        # gd.configure_side_bar()
        # 分页
        gd.configure_pagination(
            # 取消自动分页
            paginationAutoPageSize=False,
            # 30页一分页
            paginationPageSize=30,
        )

        gridoptions = gd.build()

        # 渲染表格
        grid_res = AgGrid(
            student_df,
            gridOptions=gridoptions,
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.GRID_CHANGED,
            data_return_mode=DataReturnMode.AS_INPUT,
            allow_unsafe_jscode=True,
            theme="streamlit",
            # streamlit,alpine,balham,material
        )
        # 返回数据
        return grid_res
