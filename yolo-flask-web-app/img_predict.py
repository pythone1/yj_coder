from PIL import Image
from ultralytics import YOLO
import glob,os,time


import time

# 在这里放入你想要计时的代码
# 例如，让我们让程序等待5秒钟

# Load a pretrained YOLOv8n model
model = YOLO(r"I:\pyMethod\ultralytics-main\runs\detect\train20\weights\best.pt")

print("Starting timer...")
start_time = time.time()  # 记录开始时间
# Run inference on 'bus.jpg'
filelist = glob.glob(r'I:\pyMethod\ultralytics-main\classify\yolov8_classify\others\*.jpg')
for file in filelist:
    basename = os.path.basename(file)
    filename = os.path.splitext(basename)[0]
    savepath = r'I:\pyMethod\ultralytics-main\classify\yolov8_classify\yolov8_classify\other'
    new_filename = os.path.join(savepath, filename + '_out.jpg')

    results = model(file)  # results list
    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        # im.show()  # show image
        im.save(new_filename)  # save image

end_time = time.time()  # 记录结束时间
elapsed_time = end_time - start_time  # 计算消耗的时间

print(f"Elapsed time: {elapsed_time} seconds")