import os, glob,re
import pandas as pd


BZ = '合规性检查'
yzpz = [
"青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "泥鳅", "鲇鱼", "鮰鱼",
"黄颡鱼", "河鲀", "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼", "乌鳢","乌鳗",
"罗非鱼", "鲟鱼", "鳗鲡", "罗氏沼虾", "青虾", "克氏原螯虾", "南美白对虾", "河蟹",
"河蚌", "螺", "蚬", "螺旋藻", "龟", "鳖", "蛙", "珍珠", "其他种类", "观赏鱼",
"鲆鱼", "大黄鱼", "鲽鱼", "斑节对虾", "中国对虾", "日本对虾", "梭子蟹", "青蟹",
"牡蛎", "蚶", "贻贝", "蛤", "蛏", "紫菜", "海参", "海蜇"
]
def extract_species_names(text):
    if pd.isna(text) or str(text).strip() in {'/', ''}:
        return []
    # 匹配“品种名：”这种形式
    matches = re.findall(r'([\u4e00-\u9fa5]+)[：:]', str(text))
    return matches
# 用于检查是否合法
def is_species_list_valid(species_list):
    return set(species_list).issubset(set(yzpz))
def requiredFieldCheck_wsy(df):

    # df = df[df['状态']!='未上报']
    for c in df.columns:
        df.loc[df[c] == '/', c] = ''
    df = df.fillna('')
    df[BZ] = ''

    # 一、用户信息
    # 1、手机号码检查（11位，非空）
    col = '手机号码'
    # 空值检查
    idx_empty = df[df[col].str.strip() == ''].index
    df.loc[idx_empty, BZ] += f"{col}未填写，"
    print(f"{col}未填写：{len(idx_empty)} 条")
    # 非11位数字检查
    idx_invalid = df[(df[col].str.strip() != '') & ~df[col].str.match(r'^\d{11}$')].index
    df.loc[idx_invalid, BZ] += f"{col}非11位手机号码，"
    print(f"{col}非11位手机号码：{len(idx_invalid)} 条")

    # 2、用户类别合法性检查
    valid_users = ['养殖户', '渔技员', '保险业务员', '政府工作人员', '其他','企业工作人员']
    idx = df[~df['用户类别'].isin(valid_users)].index
    df.loc[idx, BZ] += "用户类别填写非法，"
    print(f"用户类别范围外用户类别：{len(idx)} 条")

    # 二、池塘信息
    # 3、塘口编号在检查图斑
    #
    # # 4、池塘空间地理位置与轮廓
    # idx = df[df['池塘位置'] == ''].index
    # df.loc[idx, BZ] += "池塘位置缺失，"
    # print(f"池塘位置缺失：{len(idx)} 条")
    #
    # # 5、所在镇村
    # idx = df[df['地址'].apply(lambda x: len(x.split('-')) != 5)].index
    # df.loc[idx, BZ] += "地址格式错误（按-分割不是5段），"
    # print(f"地址格式错误：{len(idx)} 条")

    # 三、养殖主体信息
    # 12、养殖经营人证件一致性校验
    is_id = lambda x: isinstance(x, str) and re.fullmatch(r'[A-Za-z0-9]{18}', x) is not None
    idx = df[
        (df['统一社会信用代码'].str.strip() == '') &
        (df['身份证号'].str.strip() == '')
        ].index
    df.loc[idx, BZ] += "主体证件号码缺失，"
    print(f"主体证件号码缺失：{len(idx)} 条")
    # #13、养殖经营人证件号码
    # idx = df[(df['养殖主体类型']=='个人')&
    #     ~df['身份证号'].str.strip().apply(is_id)
    #     ].index
    # df.loc[idx, BZ] += "养殖主体身份证号缺失或不是18位，"
    # df_id_checked = df[df['身份证号'].str.strip() != '']
    # # 分组判断同一个身份证是否对应多个养殖经营人名称
    # id_name_group = df_id_checked.groupby('身份证号')['养殖经营人名称'].nunique()
    # inconsistent_ids = id_name_group[id_name_group > 1].index.tolist()
    # idx = df[df['身份证号'].isin(inconsistent_ids)].index
    # df.loc[idx, BZ] += "相同身份证号对应多个养殖经营人名称，"
    # print(f"相同身份证号对应多个养殖经营人名称：{len(idx)} 条")

    # 15、联系人
    idx = df[df['联系人'] == ''].index
    df.loc[idx, BZ] += "联系人缺失，"
    print(f"联系人缺失：{len(idx)} 条")

    # 16、联系方式
    col = '联系方式'
    idx_empty = df[df[col].str.strip() == ''].index
    df.loc[idx_empty, BZ] += f"{col}未填写，"
    print(f"{col}未填写：{len(idx_empty)} 条")
    # 非11位数字检查（跳过空值）
    idx_invalid = df[(df[col].str.strip() != '') & ~df[col].str.match(r'^\d{11}$')].index
    df.loc[idx_invalid, BZ] += f"{col}非11位手机号码，"
    print(f"{col}非11位手机号码：{len(idx_invalid)} 条")

    return df
def requiredFieldCheck_yz(df):

    # df = df[df['状态']!='未上报']
    for c in df.columns:
        df.loc[df[c] == '/', c] = ''
    df = df.fillna('')
    df[BZ] = ''

    # 一、用户信息
    # 1、手机号码检查（11位，非空）
    col = '手机号码'
    # 空值检查
    idx_empty = df[df[col].str.strip() == ''].index
    df.loc[idx_empty, BZ] += f"{col}未填写，"
    print(f"{col}未填写：{len(idx_empty)} 条")
    # 非11位数字检查
    idx_invalid = df[(df[col].str.strip() != '') & ~df[col].str.match(r'^\d{11}$')].index
    df.loc[idx_invalid, BZ] += f"{col}非11位手机号码，"
    print(f"{col}非11位手机号码：{len(idx_invalid)} 条")

    # 2、用户类别合法性检查
    valid_users = ['养殖户', '渔技员', '保险业务员', '政府工作人员', '其他','企业工作人员']
    idx = df[~df['用户类别'].isin(valid_users)].index
    df.loc[idx, BZ] += "用户类别填写非法，"
    print(f"用户类别范围外用户类别：{len(idx)} 条")

    # 二、池塘信息
    # 3、塘口编号在检查图斑

    # 4、池塘空间地理位置与轮廓
    idx = df[df['池塘位置'] == ''].index
    df.loc[idx, BZ] += "池塘位置缺失，"
    print(f"池塘位置缺失：{len(idx)} 条")
    idx = df[df['图斑id'] == ''].index
    df.loc[idx, BZ] += "无对应图斑，"
    print(f"无对应图斑：{len(idx)} 条")

    # 6、池塘土地属性
    valid_land = ['坑塘水面', '耕地', '基本农田','其他','']
    idx = df[~df['池塘土地属性'].isin(valid_land)].index
    df.loc[idx, BZ] += "池塘土地属性填写非法或缺失，"
    print(f"池塘土地属性填写非法或缺失：{len(idx)} 条")

    # 7、养殖面积
    idx = df[(df['合同面积'] == '') & (df['净水面面积'] == '')].index
    df.loc[idx, BZ] += "合同面积与净水面面积不能同时为空，"
    print(f"合同面积与净水面面积同时为空：{len(idx)} 条")

    # 8、池塘所有权
    valid_ownership = ['集体/公司', '个人', '其他']
    idx = df[~df['池塘所有权'].isin(valid_ownership)].index
    df.loc[idx, BZ] += "池塘所有权填写非法或缺失，"
    print(f"池塘所有权填写非法或缺失：{len(idx)} 条")

    # 9、池塘所有权人名称
    idx = df[df['池塘所有权人名称'] == ''].index
    df.loc[idx, BZ] += "池塘所有权人名称缺失，"
    print(f"池塘所有权人名称缺失：{len(idx)} 条")
    # df['池塘所有权人证件号码'] = df['池塘所有权人证件号码'].astype(str).str.replace(r"[ '\u3000]", '', regex=True)
    # # 10、池塘所有权人证件号码
    is_id = lambda x: isinstance(x, str) and re.fullmatch(r'[A-Za-z0-9]{18}', x) is not None
    # # 只检查“池塘所有权”为个人时，且填写了证件号码但不合规的情况
    # idx = df[(df['池塘所有权'] == '个人') &
    #          (df['池塘所有权人证件号码'].str.strip() != '') &
    #          ~df['池塘所有权人证件号码'].apply(is_id)
    #          ].index
    # df.loc[idx, BZ] += "池塘所有权人身份证号不是18位，"
    # print(f"池塘所有权人身份证号不是18位：{len(idx)} 条")
    # # 检查“池塘所有权人证件号码”姓名一致性
    # pid_name_map = df[
    #     df['池塘所有权人证件号码'].str.strip().apply(is_id) & (df['池塘所有权'].str.strip() == '个人')
    #     ][['池塘所有权人证件号码', '池塘所有权人名称']]
    #
    # dup = pid_name_map.groupby('池塘所有权人证件号码')['池塘所有权人名称'].nunique()
    # inconsistent_ids = dup[dup > 1].index.tolist()
    # idx = df[df['池塘所有权人证件号码'].isin(inconsistent_ids) & (df['池塘所有权'].str.strip() == '个人')].index
    # df.loc[idx, BZ] += "相同池塘所有权人证件号码对应多个池塘所有权人名称，"
    # print(f"相同池塘所有权人证件号码对应多个池塘所有权人名称：{len(idx)} 条")


    # 三、养殖主体信息
    # 12、养殖经营人证件一致性校验
    idx = df[
        (df['统一社会信用代码'].str.strip() == '') &
        (df['身份证号'].str.strip() == '')
        ].index
    df.loc[idx, BZ] += "主体证件号码缺失，"
    print(f"主体证件号码缺失：{len(idx)} 条")
    #13、养殖经营人证件号码
    idx = df[(df['养殖主体类型']=='个人') &
             ~df['身份证号'].str.strip().apply(is_id)
        ].index
    df.loc[idx, BZ] += "养殖主体身份证号缺失或不是18位，"
    print(f"养殖主体身份证号缺失或不是18位：{len(idx)} 条")

    df_id_checked = df[df['身份证号'].str.strip() != '']
    df_id_checked = df_id_checked[df_id_checked['养殖主体类型'].str.strip() == '个人']
    # 分组判断同一个身份证是否对应多个养殖经营人名称
    id_name_group = df_id_checked.groupby('身份证号')['养殖经营人名称'].nunique()
    inconsistent_ids = id_name_group[id_name_group > 1].index.tolist()
    idx = df[df['身份证号'].isin(inconsistent_ids) & (df['养殖主体类型'].str.strip() == '个人')].index
    df.loc[idx, BZ] += "相同身份证号对应多个养殖经营人名称，"
    print(f"相同身份证号对应多个养殖经营人名称：{len(idx)} 条")

    # 15、联系人
    idx = df[df['联系人'] == ''].index
    df.loc[idx, BZ] += "联系人缺失，"
    print(f"联系人缺失：{len(idx)} 条")

    # 16、联系方式
    col = '联系方式'
    idx_empty = df[df[col].str.strip() == ''].index
    df.loc[idx_empty, BZ] += f"{col}未填写，"
    print(f"{col}未填写：{len(idx_empty)} 条")
    # 非11位数字检查（跳过空值）
    idx_invalid = df[(df[col].str.strip() != '') & ~df[col].str.match(r'^\d{11}$')].index
    df.loc[idx_invalid, BZ] += f"{col}非11位手机号码，"
    print(f"{col}非11位手机号码：{len(idx_invalid)} 条")

    # 四、 经营信息
    # 17、18、19、用途、养殖方式、水体类型
    yt = ['成品养殖', '苗种培育', '尾水净化', '饵料培育', '休闲垂钓', '其他']
    tzfs = ['池塘养殖', '渔光一体', '跑道鱼', '其他']
    stlx = ['淡水', '咸水', '海水']
    idx = df[~df['用途'].isin(yt)].index
    df.loc[idx, BZ] += "用途填写非法或缺失，"
    print(f"用途填写非法或缺失：{len(idx)} 条")
    idx = df[~df['用途'].isin(['尾水净化', '休闲垂钓']) & ~df['养殖方式'].isin(tzfs)].index
    df.loc[idx, BZ] += "养殖方式填写非法或缺失，"
    print(f"养殖方式填写非法或缺失：{len(idx)} 条")
    idx = df[~df['用途'].isin(['尾水净化', '休闲垂钓']) & ~df['水体类型'].isin(stlx)].index
    df.loc[idx, BZ] += "养殖水体类型填写非法或缺失，"
    print(f"养殖水体类型填写非法或缺失：{len(idx)} 条")

    # 20、养殖品种与预计亩产量
    # 只对用途不是尾水净化/休闲垂钓，且字段不为空的做检查
    idx = df[~df['用途'].isin(['尾水净化', '休闲垂钓']) & (df['养殖品种/预计亩产量'] == '')].index
    df.loc[idx, BZ] += "养殖品种/预计亩产量未填写，"
    print(f"养殖品种/预计亩产量未填写：{len(idx)} 条")

    df1 = df[~df['用途'].isin(['尾水净化', '休闲垂钓']) & (df['养殖品种/预计亩产量'] != '')]
    df1['提取品种列表'] = df1['养殖品种/预计亩产量'].apply(extract_species_names)
    df1['提取品种'] = df1['提取品种列表'].apply(lambda lst: '、'.join(lst))
    idx = df1[~df1['提取品种列表'].apply(is_species_list_valid)].index
    df.loc[idx, BZ] += "养殖品种非法，"
    print(f"养殖品种非法：{len(idx)} 条")

    # 四、标准化改造信息
    # 22、是否完成池塘标准化改造
    df['图斑面积'] = pd.to_numeric(df['图斑面积'], errors='coerce')
    df['图斑面积']=(df['图斑面积'].astype(float))
    idx = df[
        (df['图斑面积'] >= 50) &
        (df['是否完成池塘标准化改造'].isin(['', '---']))
        ].index
    df.loc[idx, BZ] += "50亩以上池塘未填是否完成池塘标准化改造，"
    print(f"50亩以上池塘未填是否完成池塘标准化改造：{len(idx)} 条")

    # 五、尾水排放与清淤情况

    # 23、尾水集中排放期
    valid_months = [str(i) for i in range(1, 14)]
    df1 = df.copy()
    df1['尾水集中排放期_split'] = df1['尾水集中排放期'].astype(str).str.split(r'[；、,，]')
    idx = df1[df1['尾水集中排放期_split'].apply(
        lambda lst: any(x.strip() not in valid_months for x in lst if x.strip())
    )].index
    df.loc[idx, BZ] += "尾水集中排放期含非法月份，"
    print(f"尾水集中排放期含非法月份：{len(idx)} 条")

    # 24、清塘淤泥处置方式
    qtfs = ['边坡堆放', '池塘内部堆填', '外运堆肥','外运填埋', '其它','不处置']
    idx = df[~df['清塘淤泥处理方式'].isin(qtfs)].index
    df.loc[idx, BZ] += "清塘淤泥处理方式填写非法，"
    print(f"清塘淤泥处理方式填写非法：{len(idx)} 条")
    df1 = df[df['清塘淤泥处理方式'] != "不处置"]
    idx = df1[df1['处置频率'] == ''].index
    df.loc[idx, BZ] += f"处置频率未填，"
    print(f"处置频率未填：{len(idx)} 条")

    # 25、排口位置
    idx = df[(df['养殖主体类型'] == '集体/公司') & (df['排口位置'] == '')].index
    df.loc[idx, BZ] += "集体/公司养殖未填写排口位置，"
    print(f"集体/公司养殖未填写排口位置：{len(idx)} 条")

    # 六、尾水处理情况
    # 26、尾水处理
    valid_process = {'三池两坝', '多级净化', '原位修复', '人工湿地', '集中处理', '其他'}
    # 字段转为字符串处理
    df['有无尾水处理'] = df['有无尾水处理'].astype(str).str.strip()
    df['尾水处理工艺'] = df['尾水处理工艺'].astype(str).str.strip()
    df['尾水净化区面积'] = df['尾水净化区面积'].astype(str).str.strip()
    idx = df[df['有无尾水处理'] == ''].index
    df.loc[idx, BZ] += "有无尾水处理未填写，"
    print(f"有无尾水处理未填写：{len(idx)} 条")
    idx = df[(df['有无尾水处理'] == '有') &
             ((df['尾水处理工艺'] == '') | ~df['尾水处理工艺'].isin(valid_process))].index
    df.loc[idx, BZ] += "尾水处理工艺缺失或不合法，"
    print(f"尾水处理工艺缺失或不合法：{len(idx)} 条")

    # 27、尾水净化区面积
    idx = df[(df['有无尾水处理'] == '有') & (~df['尾水处理工艺'].isin({'原位修复'})) & (df['尾水净化区面积'] == '')].index
    df.loc[idx, BZ] += "尾水净化区面积缺失，"
    print(f"尾水净化区面积缺失：{len(idx)} 条")
    return df
# 按照“图斑id”分组并进行处理
def mark_bz(group):
    if len(group) > 1:
        statuses = set(group['养殖状态'])
        if statuses == {'未使用'}:
            group['BZ'] = group.get(BZ, '') + '未使用多点对应同一图斑'
        elif '养殖' in statuses:
            group['BZ'] = group.get(BZ, '') + '养殖多点对应同一图斑'
    return group


if __name__ == "__main__":
    pth = r'E:\全省养殖池溏上图入库普查\合规性检查\20250516'
    os.chdir(pth)
    files = glob.glob(r"*.csv")
    df_list = []
    for f in files:
        df_list.append(pd.read_csv(f,dtype='str',sep=',',usecols=range(54),index_col=False))
    ctxx = pd.concat(df_list, axis=0,ignore_index=True)
    ctxx = ctxx[ctxx['状态']!='未上报']
    print(ctxx['养殖状态'].value_counts())
    total = ctxx['图斑id'].drop_duplicates().shape[0]
    print(f"去重后的图斑总数为：{total}")

    # df_yz = requiredFieldCheck_yz(ctxx[ctxx['养殖状态']=='养殖'])
    # df_yz = ctxx[ctxx['养殖状态'] == '养殖']
    # yz = df_yz['图斑id'].drop_duplicates().shape[0]
    # print(f"去重后的养殖为：{yz}")
    # df_wsy = requiredFieldCheck_wsy(ctxx[ctxx['养殖状态']=='未使用'])
    df_wsy = ctxx[ctxx['养殖状态']=='未使用']
    wsy = df_wsy['图斑id'].drop_duplicates().shape[0]
    print(f"去重后的未使用为：{wsy}")
    #
    # print(len(ctxx[ctxx['养殖状态']=='养殖']),len(ctxx))
    # df_concat = pd.concat([df_yz, df_wsy], axis=0,ignore_index=True)
    # df_dup = df_concat[df_concat['图斑id'] != ''].copy()
    # dup_ids = df_dup['图斑id'][df_dup['图斑id'].duplicated(keep=False)]
    # idx = df_concat[df_concat['图斑id'].isin(dup_ids)].copy()
    # for gid, group in idx.groupby('图斑id'):
    #     statuses = set(group['养殖状态'])
    #     if statuses == {'未使用'}:
    #         df_concat.loc[group.index, BZ] += '未使用多点对应同一图斑，'
    #     elif '养殖' in statuses:
    #         df_concat.loc[group.index, BZ] += '养殖多点对应同一图斑，'
    # print(f"多点对应同一图斑：{len(idx)} 条")
    # df_concat = df_concat[df_concat[BZ] != '']
    # df_concat.to_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250516\20250516合规性检查（错误）重算面积.xlsx')



