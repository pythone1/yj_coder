import os,glob
import shutil

if __name__ == "__main__":
    # pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\连云港市_灌云县\03图片'
    # pth0 = os.path.dirname(pth)
    # os.chdir(pth)

    # files = glob.glob('*.jpg')
    # for f in files:
    #     zhen,cun,i = f.split('_')[0:3]
    #     shutil.copyfile(f,f"{pth0}\\{zhen}\\{cun}-{i}")

    pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\连云港市_灌云县'
    os.chdir(pth)

    files = glob.glob("*\\*.jpg.jpg")
    for f in files:
        os.rename(f,f.replace('.jpg.jpg','.jpg'))