import pandas as pd

# ===== 参数配置 =====
excel_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\原表\金湖县4月9日、7月2日四鱼明细表.xlsx"
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250703\原表\金湖县照养殖户统计图斑.xlsx"
xls = pd.ExcelFile(excel_path)
sheet_dict = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
    for sheet_name, df in sheet_dict.items():

        df.to_excel(writer, sheet_name=sheet_name, index=False)

        df["图斑编号"] = df["图斑编号"].astype(str)
        group_fields = ["养殖经营人名称", "身份证号", "统一社会信用代码", "地址", "联系方式"]

        if all(col in df.columns for col in group_fields + ["图斑编号"]):
            summary = (
                df.groupby(group_fields)["图斑编号"]
                .apply(lambda x: "、".join(sorted(set(x))))
                .reset_index()
            )
            summary_sheet_name = f"{sheet_name}_图斑汇总"
            summary.to_excel(writer, sheet_name=summary_sheet_name[:31], index=False)  # Excel 限制表名最长31字符
