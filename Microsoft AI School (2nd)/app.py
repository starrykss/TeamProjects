import sys
import webbrowser
import os
import subprocess
import shutil
import config 

from datetime import datetime
from threading import Timer

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from flask import Flask, redirect, url_for, request, render_template, send_from_directory, session
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip

app = Flask(__name__)
base_dir = os.path.dirname(__file__)
save_path = os.path.join(base_dir, 'uploads')
main_script_path = os.path.join(base_dir, 'main.py')
app.config.from_object(config)
app.secret_key = "super_secret_key"
app.config['save_path'] = save_path
allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}

db = SQLAlchemy()
migrate = Migrate()
db.init_app(app)
migrate.init_app(app, db)

import models_flask as MF

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 비디오 확장자 가져오기
def get_video_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'mp4':
        return 'video/mp4'
    elif ext == 'avi':
        return 'video/avi'
    elif ext == 'mov':
        return 'video/quicktime'
    elif ext == 'mkv':
        return 'video/x-matroska'
    else:
        return 'application/octet-stream'

# 비디오 크기 축소
def compress_video(input_path, output_path):
    clip = VideoFileClip(input_path)
    clip_resized = clip.resize(height=360) 
    clip_resized.write_videofile(output_path, codec="libx264")

@app.route('/run_main', methods=['GET'])
def run_main_script():
    try:
        # uploads 폴더의 경로 설정하기
        subprocess.run(["python", main_script_path], check=True)
        shutil.move('./out.mp4', save_path)  # 파일을 uploads 폴더로 이동
        filename = 'out.mp4'
        file_path = os.path.join(save_path, filename)  # 경로를 안전하게 만듭니다.

        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        if os.path.exists(file_path):  # 실제 파일이 있는지 확인합니다.  
            compressed_filename = "compressed_" + filename
            compress_video(file_path, os.path.join(save_path, compressed_filename))
            session['uploaded_filename'] = compressed_filename
            return redirect(url_for('result'))    # 리다이렉트
        else:
            return "File not found", 404
        
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload',methods=['GET'])
def upload():
    return render_template('upload.html')

@app.route('/file_upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request.'
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file.'
    
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        file.save(os.path.join(save_path, filename))

        target_dir = os.path.join(base_dir, "uploads")
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if "compressed_" in file:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

        compressed_filename = "compressed_" + filename
        compress_video(os.path.join(save_path, filename), os.path.join(save_path, compressed_filename))

        upload_date = datetime.now()
        video = MF.Video(video_name=filename, video_file=open(os.path.join(save_path, compressed_filename), 'rb').read(), upload_date=upload_date)
        db.session.add(video)
        db.session.commit()
        session['uploaded_filename'] = compressed_filename 
        upload_date = datetime.now()

        return redirect(url_for('result'))
    else:
        return "Unsupported file type."

@app.route('/result', methods=['GET'])
def result():
    filename = session.get('uploaded_filename', None)
    if not filename:
        return render_template('nofile.html')
    video_type = get_video_type(filename)

    return render_template('result.html', filename=filename, video_type=video_type)

@app.route('/uploads/<filename>')
def send_uploaded_file(filename):
    return send_from_directory(save_path, filename)

@app.route('/oauth/callback')
def kakao():
    return '/oauth/callback'

def open_browser():
    webbrowser.open_new('http://127.0.0.1:'+str(port)+'/')

if __name__ == "__main__":
    port = 5001
    Timer(1, open_browser).start()
    app.run(port=5001, debug=True)