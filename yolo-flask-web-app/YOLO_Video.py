from ultralytics import YOLO
import cv2,os
import numpy as np
from collections import defaultdict

def video_detection(path_x):
    # Load the YOLOv8 model
    model = YOLO(r"E:\PY\YOLO\yolov12\yolov12x.pt")

    video_capture = path_x
    # video_capture =  "rtmp://rtmp05open.ys7.com:1935/v3/openlive/AC2058520_1_1?expire=1785460773&id=872770799247822848&t=9354901cc09e448141dfd4f966a96fe4641658487166f9bf983e10cea7cfb7f6&ev=100"
    # video_capture = 'rtsp://admin:wy123456@192.168.1.108:port/cam/realmonitor?channel=1&subtype=0'
    cap = cv2.VideoCapture(video_capture)

    # print(cap.get(cv2.CAP_PROP_FPS))

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # basename = os.path.basename(video_capture)
    # filename = os.path.splitext(basename)[0]
    filename = 'test'
    savepath = r'D:\pymethod\flask\runs\yolov8x\mymodel'

    new_filename = os.path.join(savepath, filename + '_out.avi')

    out = cv2.VideoWriter(new_filename, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frame_width, frame_height))

    # out = cv2.VideoWriter('out.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frame_width, frame_height))


    track_history = defaultdict(lambda: [])
    while cap.isOpened():
        success, img = cap.read()
        if success:
            # Run YOLOv8 tracking on the frame, persisting tracks between frames
            results = model.track(img, persist=True)
            boxes = results[0].boxes.xywh.cpu()
            # 获取追踪ID
            if results[0].boxes.id is not None:
                track_ids = results[0].boxes.id.int().cpu().tolist()
            else:
                print("No tracking IDs were found.")
                track_ids = []

            # Visualize the results on the frame
            annotated_frame = results[0].plot()

            # Plot the tracks
            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                track = track_history[track_id]
                track.append((float(x), float(y)))  # x, y center point
                if len(track) > 30:  # retain 90 tracks for 90 frames
                    track.pop(0)
                    # Draw the tracking lines
                points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated_frame, [points], isClosed=False, color=(0, 0, 255), thickness=2)

            # Add text with the total number of birds
            total_num_birds = len(track_history)
            total_birds_text = f"Total numbers of objects: {total_num_birds}"
            cv2.putText(annotated_frame, total_birds_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2,
                        cv2.LINE_AA)

            # Add text with the current number of birds
            current_num_birds = len(boxes)
            current_birds_text = f"Current numbers of objects: {current_num_birds}"
            cv2.putText(annotated_frame, current_birds_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2,
                        cv2.LINE_AA)

            # Yield the annotated frame
            yield annotated_frame

            # Write the annotated frame to the output video file
            out.write(annotated_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    out.release()
    cv2.destroyAllWindows()
# def video_detection(path_x):
#     video_capture = path_x
#     #Create a Webcam Object
#     cap=cv2.VideoCapture(video_capture)
#     frame_width=int(cap.get(3))
#     frame_height=int(cap.get(4))
#     basename = os.path.basename(video_capture)
#     # 提取文件名(不包含扩展名)
#     filename = os.path.splitext(basename)[0]
#     # 拼接新路径和文件名
#     savepath = r'D:\pymethod\flask\runs\yolov8x\mymodel'
#     new_filename = os.path.join(savepath, filename + '_out.avi')
#     print(new_filename)
#     basename = os.path.basename(video_capture)
#     out=cv2.VideoWriter(new_filename, cv2.VideoWriter_fourcc('M', 'J', 'P','G'), 10, (frame_width, frame_height))
#
#     classNames =['bird']
#     model = YOLO(r'I:\pyMethod\ultralytics-main\runs\detect\train19\weights\best.pt')
#     # model=YOLO(r"I:\downloads\Computervisionprojects-main\YOLOv8-CrashCourse\YOLO-Weights\yolov8x.pt")
#     # classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
#     #               "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
#     #               "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
#     #               "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
#     #               "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
#     #               "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
#     #               "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
#     #               "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
#     #               "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
#     #               "teddy bear", "hair drier", "toothbrush"
#     #               ]
#     while True:
#         success, img = cap.read()
#         results=model(img,stream=True)
#         for r in results:
#             boxes=r.boxes
#             for box in boxes:
#                 x1,y1,x2,y2=box.xyxy[0]
#                 x1,y1,x2,y2=int(x1), int(y1), int(x2), int(y2)
#                 # print(x1,y1,x2,y2)
#                 cv2.rectangle(img, (x1,y1), (x2,y2), (255,0,255),3)
#                 conf=math.ceil((box.conf[0]*100))/100
#                 cls=int(box.cls[0])
#                 class_name=classNames[cls]
#                 label=f'{class_name}{conf}'
#                 t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
#                 # print(t_size)
#                 c2 = x1 + t_size[0], y1 - t_size[1] - 3
#                 cv2.rectangle(img, (x1,y1), c2, [255,0,255], -1, cv2.LINE_AA)  # filled
#                 cv2.putText(img, label, (x1,y1-2),0, 1,[255,255,255], thickness=1,lineType=cv2.LINE_AA)
#                 # print(img)
#         yield img
#         out.write(img)
#         #cv2.imshow("image", img)
#         #if cv2.waitKey(1) & 0xFF==ord('1'):
#             #break
#     out.release()
# cv2.destroyAllWindows()
