from flask import Flask, render_template, Response, jsonify, request, session
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, DecimalRangeField, IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, NumberRange
import os
import cv2

from YOLO_Video import video_detection

# 创建Flask应用对象
app = Flask(__name__)

# 设置secret_key,用于加密session
app.config['SECRET_KEY'] = 'ndww'

# 设置上传文件的保存路径
app.config['UPLOAD_FOLDER'] = 'static/files'


# 使用FlaskForm获取用户上传的视频文件
class UploadFileForm(FlaskForm):
   # FileField用于接收上传的视频文件,保存到file变量中
   # 加了验证器,要求用户上传视频文件,并且格式正确
   file = FileField("File", validators=[InputRequired()])
   submit = SubmitField("Run")


# 生成视频流帧的函数
def generate_frames(path_x=''):
   # 调用视频检测函数处理视频
   yolo_output = video_detection(path_x)
   for detection_ in yolo_output:
       # 使用OpenCV编码每一帧为jpg格式
       ref, buffer = cv2.imencode('.jpg', detection_)

       # 将编码后的图像转换为字节流
       frame = buffer.tobytes()
       # 构造HTTP多部分响应内容,包含image/jpeg头和编码后的帧
       yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# 生成网页视频流的函数
def generate_frames_web(path_x):
   yolo_output = video_detection(path_x)

   for detection_ in yolo_output:
       ref, buffer = cv2.imencode('.jpg', detection_)
       frame = buffer.tobytes()

       # 构造HTTP多部分响应
       yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
@app.route('/', methods=['GET','POST'])
# 主页
@app.route('/home', methods=['GET','POST'])
def home():
   # 清除会话数据
   session.clear()
   # 渲染主页
   return render_template('主页.html')

# 摄像头识别页面
@app.route("/webcam", methods=['GET','POST'])
def webcam():
    # 清除会话数据
   session.clear()
    # 摄像头识别
   return render_template('摄像头识别.html')

# 视频识别页面
@app.route('/FrontPage', methods=['GET','POST'])
def front():
   # 实例化上传表单对象
   form = UploadFileForm()
   if form.validate_on_submit():
       # 获取上传的视频文件
       file = form.file.data
       file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                              secure_filename(file.filename)))
       # 保存视频路径到session
       session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                            secure_filename(file.filename))
   return render_template('视频识别.html', form=form)

# 视频流
@app.route('/video')
def video():
   # 从session中获取上传的视频路径,生成视频流响应返回
   return Response(generate_frames(path_x = session.get('video_path', None)), mimetype='multipart/x-mixed-replace; boundary=frame')

# 网页视频流路由
@app.route('/webapp')
def webapp():
   # 调用generate_frames_web生成网页视频流响应返回
   return Response(generate_frames_web(path_x=0), mimetype='multipart/x-mixed-replace; boundary=frame')


# 启动程序
if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5001,debug=True)