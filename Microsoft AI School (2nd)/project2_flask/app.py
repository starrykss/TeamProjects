import os
import subprocess
import shutil
import config 

from datetime import datetime
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, redirect, url_for, request, render_template, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

base_dir = os.path.dirname(__file__)
save_path = os.path.join(base_dir, 'uploads')
main_script_path = os.path.join(base_dir, 'main.py')

app.config.from_object(config)
app.secret_key = "super_secret_key"
app.config['save_path'] = save_path
allowed_extensions = {'jpg', 'png', 'bmp', 'gif'}

db = SQLAlchemy()
migrate = Migrate()
db.init_app(app)
migrate.init_app(app, db)
import models as MF

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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
                if "uploaded_" in file:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

        upload_date = datetime.now()
        image = MF.Image(image_name=filename, image_file=open(os.path.join(save_path, filename), 'rb').read(), upload_date=upload_date)
        db.session.add(image)
        db.session.commit()
        session['uploaded_filename'] = filename 
        upload_date = datetime.now()
        return redirect(url_for('result'))
    else:
        return "Unsupported file type."

@app.route('/result', methods=['GET'])
def result():
    filename = session.get('uploaded_filename', None)
    if not filename:
        return render_template('nofile.html')
    return render_template('result.html', filename=filename)

@app.route('/uploads/<filename>')
def send_uploaded_file(filename):
    return send_from_directory(save_path, filename)

if __name__ == "__main__":
    app.run(port=5001, debug=True)