import csv
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from utils import Utility, User, ImageProcessor, UserManager, ImageManager
from setting import Settings
from logging.config import dictConfig
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.secret_key = Settings.SECRET_KEY

# 创建日志目录
if not os.path.exists(Settings.LOG_DIRECTORY):
    os.makedirs(Settings.LOG_DIRECTORY)

# 配置日志记录
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': Settings.LOG_FORMAT,
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': Settings.LOG_FILE,
            'maxBytes': Settings.LOG_MAX_BYTES,
            'backupCount': Settings.LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        'werkzeug': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        '': {
            'level': Settings.LOG_LEVEL,
            'handlers': ['file']
        }
    }
})

logging.info('应用程序启动')


# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

BASE_IMAGE_FOLDER = Settings.BASE_IMAGE_FOLDER

@login_manager.user_loader
def load_user(user_id):
    return Utility.load_user_from_csv(user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, message = Utility.register_user(username, password)
        flash(message)
        if success:
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open(Settings.USER_CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username and check_password_hash(row['password'], password):
                    user_obj = User(id=row['id'], username=username, is_admin=(username == 'idverne'))
                    login_user(user_obj)
                    flash('登录成功！')
                    if user_obj.is_admin:
                        return redirect(url_for('admin'))
                    else:
                        return redirect(url_for('index'))
            flash('用户名或密码错误！')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功注销。')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        user_folders = [f for f in os.listdir(BASE_IMAGE_FOLDER) if os.path.isdir(os.path.join(BASE_IMAGE_FOLDER, f))]
        images = {user: [f for f in os.listdir(os.path.join(BASE_IMAGE_FOLDER, user)) if f.lower().endswith(('.jpg', '.png'))] for user in user_folders}
    else:
        user_folder = os.path.join(BASE_IMAGE_FOLDER, current_user.username)
        images = {current_user.username: [f for f in os.listdir(user_folder) if f.lower().endswith(('.jpg', '.png'))]}
    logging.info("访问主页，用户: %s", current_user.username)
    return render_template('index.html', images=images, is_admin=current_user.is_admin)

@app.route('/image/<username>/<filename>')
@login_required
def image(username, filename):
    if current_user.is_admin or current_user.username == username:
        user_folder = os.path.join(BASE_IMAGE_FOLDER, username)
        logging.info("请求查看图片: %s/%s", username, filename)
        return send_from_directory(user_folder, filename)
    else:
        flash('无权访问此图片。')
        return redirect(url_for('index'))

@app.route('/download/<username>/<filename>')
@login_required
def download(username, filename):
    if current_user.is_admin or current_user.username == username:
        user_folder = os.path.join(BASE_IMAGE_FOLDER, username)
        logging.info("请求下载图片: %s/%s", username, filename)
        return send_from_directory(user_folder, filename, as_attachment=True)
    else:
        flash('无权下载此图片。')
        return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('无权访问此页面。')
        return redirect(url_for('index'))

    users = UserManager.get_all_users()
    images = ImageManager.get_user_images(users)

    return render_template('admin.html', 
                         users=users, 
                         images=images,
                         admin_username=Settings.ADMIN_USERNAME,
                         Settings=Settings)

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('无权执行此操作。')
        return redirect(url_for('admin'))

    username = request.form['username']
    password = request.form['password']
    success, message = Utility.register_user(username, password)
    flash(message)
    return redirect(url_for('admin'))

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if not current_user.is_admin:
        flash('无权执行此操作。')
        return redirect(url_for('admin'))

    if UserManager.delete_user(username):
        flash(f'用户 {username} 已删除。')
    return redirect(url_for('admin'))

@app.route('/reset_password/<username>', methods=['POST'])
@login_required
def reset_password(username):
    if not current_user.is_admin:
        flash('无权执行此操作。')
        return redirect(url_for('admin'))

    new_password = UserManager.reset_user_password(username)
    flash(f'用户 {username} 的密码已重置为 {new_password}。')
    return redirect(url_for('admin'))

@app.route('/get_log_content')
def get_log_content():
    try:
        with open('log/app.log', 'r') as log_file:
            log_content = log_file.read()
    except FileNotFoundError:
        log_content = ""  # 如果日志文件不存在，返回空白内容
    except Exception as e:
        app.logger.error(f"读取日志时出错: {e}")
        log_content = ""  # 发生其他错误时，也返回空白内容
    return log_content

@app.route('/upload')
@login_required
def upload():
    if not current_user.is_admin:
        flash('无权访问此页面。')
        return redirect(url_for('index'))
    
    users = UserManager.get_all_users()
    return render_template('upload.html', 
                         users=users,
                         admin_username=Settings.ADMIN_USERNAME)

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    username = request.form.get('username')

    if not username:
        return jsonify({'error': '未选择用户'}), 400

    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if file.content_length and file.content_length > Settings.MAX_UPLOAD_SIZE:
        return jsonify({'error': '文件太大'}), 400

    success, result = ImageProcessor.save_uploaded_image(file, username)
    if success:
        return jsonify({'success': True, 'filename': result})
    else:
        return jsonify({'error': result}), 400

@app.route('/delete_image/<username>/<filename>', methods=['POST'])
@login_required
def delete_image(username, filename):
    if not current_user.is_admin:
        flash('无权执行此操作。')
        return redirect(url_for('admin'))

    if ImageProcessor.delete_image(username, filename):
        flash(f'图片 {filename} 已删除。')
    else:
        flash('删除图片失败。')
    
    return redirect(url_for('admin'))

@app.route('/batch_delete_images', methods=['POST'])
@login_required
def batch_delete_images():
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403

    data = request.get_json()
    images = data.get('images', [])
    success_count = ImageManager.batch_delete_images(images)
    
    if success_count == len(images):
        return jsonify({'success': True, 'message': f'成功删除 {success_count} 张图片'})
    else:
        return jsonify({'success': False, 'message': f'删除完成，成功 {success_count} 张，失败 {len(images) - success_count} 张'})

# 添加新的缩略图路由
@app.route('/thumbnail/<username>/<filename>')
@login_required
def thumbnail(username, filename):
    if current_user.is_admin or current_user.username == username:
        thumbnail_folder = os.path.join(BASE_IMAGE_FOLDER, username, Settings.THUMBNAIL_FOLDER)
        # 如果缩略图不存在，尝试创建
        if not os.path.exists(os.path.join(thumbnail_folder, filename)):
            original_path = os.path.join(BASE_IMAGE_FOLDER, username, filename)
            if os.path.exists(original_path):
                ImageProcessor.create_thumbnail(original_path, username)
        
        logging.info(f"请求查看缩略图: {username}/{filename}")
        return send_from_directory(thumbnail_folder, filename)
    else:
        flash('无权访问此图片。')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # 初始化管理员用户
    Utility.initialize_admin()
    app.run(debug=Settings.DEBUG, port=Settings.SERVER_PORT)