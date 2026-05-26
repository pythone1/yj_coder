import subprocess
import os,gc
import time
import glob


# python.exe文件所在路径，如果有多个版本的python，请注意对应的路径
python_exe_path = r'C:\ProgramData\Anaconda3\envs\snappyenv\python.exe'
# 要执行的python脚本文件
py_file_path = r'D:\pyMethod\snap\preprocess_S1.py'


##### 类型一：研究区1张影像覆盖，不需要影像间合并 #####
# 批处理Sentinel-1 GRDH 数据所在路径（压缩文件即可）
inpath = r''
# 存放处理后数据的路径
outpath= r''
os.makedirs(outpath,exist_ok=True)
# 裁剪范围
subsetregion = None

zip_files = sorted(glob.glob(os.path.join(inpath, '*.zip')))

for zipfile in range(len(zip_files)):
    gc.enable()
    gc.collect()
    file_list = [zipfile]
    basename = os.path.basename(file_list[0])
    # 获取时间和日期
    date = basename.split('_')[4].split('T')[0]
    print("PreProcessing %s's data..." % (date))

    pipeline_out = subprocess.check_output([python_exe_path, py_file_path, file_list, outpath, subsetregion],
                                           stderr=subprocess.STDOUT)
    print("The Preprocession of  %s's data finished!" % (date))
    # # 睡眠30s，以等待释放内存
    print("Sleeping...")
    time.sleep(30)


##### 类型二：研究区跨2张影像，处理时需按日期合并 #####
# 批处理Sentinel-1 GRDH 数据所在路径（压缩文件即可）
inpath = r''
# 存放处理后数据的路径
outpath= r''
os.makedirs(outpath,exist_ok=True)
# 裁剪范围
subsetregion = None

zip_files = sorted(glob.glob(os.path.join(inpath, '*.zip')))
# 同一天两景中的某景构成的part1列表
part1_files = zip_files[::2]
# 同一天两景中的另一景构成的part2列表
part2_files = zip_files[1::2]

for file_ndex in range(len(part1_files)):
    gc.enable()
    gc.collect()
    file_list = [part1_files[file_ndex], part2_files[file_ndex]]
    basename = os.path.basename(file_list[0])
    # 获取时间和日期
    date = basename.split('_')[4].split('T')[0]
    print("PreProcessing %s's data..." % (date))

    pipeline_out = subprocess.check_output([python_exe_path, py_file_path, file_list, outpath, subsetregion],
                                           stderr=subprocess.STDOUT)
    print("The Preprocession of  %s's data finished!" % (date))
    # # 睡眠30s，以等待释放内存
    print("Sleeping...")
    time.sleep(30)






