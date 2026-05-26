from collections import defaultdict

import cv2,os
import numpy as np

from ultralytics import YOLO


model = YOLO(r"I:\downloads\Computervisionprojects-main\YOLOv8-CrashCourse\YOLO-Weights\yolov8x.pt")

video_capture = r'I:\pyMethod\YOLOv8-DeepSORT-Object-Tracking-main\ultralytics\bird_vedio\3.mp4'
cap = cv2.VideoCapture(video_capture)
track_history = defaultdict(lambda: [])

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

basename = os.path.basename(video_capture)
filename = os.path.splitext(basename)[0]

savepath = r'D:\pymethod\flask\runs\yolov8x\mymodel'
new_filename = os.path.join(savepath, filename + '_out.avi')
out = cv2.VideoWriter(new_filename, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frame_width, frame_height))

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
        cv2.putText(annotated_frame, total_birds_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Add text with the current number of birds
        current_num_birds = len(boxes)
        current_birds_text = f"Current numbers of objects: {current_num_birds}"
        cv2.putText(annotated_frame, current_birds_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("YOLOv8 Tracking", annotated_frame)
        # Write the annotated frame to the output video file
        out.write(annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

out.release()
cv2.destroyAllWindows()