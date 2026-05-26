# 导入需要的模块
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os

# 创建 Flask 应用实例
app = Flask(__name__)

# 上传视频的目标文件夹
app.config['UPLOAD_FOLDER'] = r'D:\pymethod\flask\data'

# 允许上传的视频格式
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi'}

# 判断上传的文件是否允许的格式
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# GET请求返回上传页面,POST请求处理上传视频
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # 如果是POST请求,则处理上传视频的逻辑
    if request.method == 'POST':
        # 获取上传的文件
        file = request.files['file']
        # 如果文件存在并且格式允许
        if file and allowed_file(file.filename):
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            # 保存文件到UPLOAD_FOLDER
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


            # 跳转到处理页面
            return render_template('processing.html', filename=filename)

    # GET请求返回上传页面
    return '''
    <!doctype html>
    <title>Upload a video</title>
    <h1>Upload a video</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

# 访问上传的视频文件路由
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 下载上传的视频文件路由
@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# # 启动程序
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001)