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
import os.path
from operator import itemgetter

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
        images = {}
        for user in user_folders:
            user_path = os.path.join(BASE_IMAGE_FOLDER, user)
            # 获取图片列表并添加修改时间信息
            image_list = []
            for f in os.listdir(user_path):
                if f.lower().endswith(('.jpg', '.png')):
                    file_path = os.path.join(user_path, f)
                    # 获取文件的修改时间
                    mtime = os.path.getmtime(file_path)
                    image_list.append((f, mtime))
            
            # 按修改时间降序排序（新的在前）
            image_list.sort(key=itemgetter(1), reverse=True)
            # 只保留文件名
            images[user] = [img[0] for img in image_list]
    else:
        user_folder = os.path.join(BASE_IMAGE_FOLDER, current_user.username)
        # 获取图片列表并添加修改时间信息
        image_list = []
        if os.path.exists(user_folder):
            for f in os.listdir(user_folder):
                if f.lower().endswith(('.jpg', '.png')):
                    file_path = os.path.join(user_folder, f)
                    # 获取文件的修改时间
                    mtime = os.path.getmtime(file_path)
                    image_list.append((f, mtime))
        
        # 按修改时间降序排序（新的在前）
        image_list.sort(key=itemgetter(1), reverse=True)
        # 只保留文件名
        images = {current_user.username: [img[0] for img in image_list]}

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
    
    # 获取并排序每个用户的图片
    images = {}
    for user in users:
        if user.username != Settings.ADMIN_USERNAME:  # 跳过管理员
            user_path = os.path.join(BASE_IMAGE_FOLDER, user.username)
            if os.path.exists(user_path):
                # 获取图片列表并添加修改时间信息
                image_list = []
                for f in os.listdir(user_path):
                    if f.lower().endswith(('.jpg', '.png')):
                        file_path = os.path.join(user_path, f)
                        # 获取文件的修改时间
                        mtime = os.path.getmtime(file_path)
                        image_list.append((f, mtime))
                
                # 按修改时间降序排序（新的在前）
                image_list.sort(key=itemgetter(1), reverse=True)
                # 只保留文件名
                images[user.username] = [img[0] for img in image_list]
            else:
                images[user.username] = []

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
    flash(f'用户 {username} 的密码已置为 {new_password}。')
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
    # 传递设置到模板
    settings = {
        'max_upload_size': Settings.MAX_UPLOAD_SIZE,
        'allowed_extensions': list(Settings.ALLOWED_EXTENSIONS)
    }
    return render_template('upload.html', 
                         users=users,
                         admin_username=Settings.ADMIN_USERNAME,
                         settings=settings)

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '没有件'}), 400

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

# 修改thumbnail路由，优化性能
@app.route('/thumbnail/<username>/<filename>')
@login_required
def thumbnail(username, filename):
    if current_user.is_admin or current_user.username == username:
        thumbnail_folder = os.path.join(BASE_IMAGE_FOLDER, username, Settings.THUMBNAIL_FOLDER)
        thumbnail_path = os.path.join(thumbnail_folder, filename)
        
        # 如果缩略图不存在，创建缩略图
        if not os.path.exists(thumbnail_path):
            original_path = os.path.join(BASE_IMAGE_FOLDER, username, filename)
            if os.path.exists(original_path):
                if not os.path.exists(thumbnail_folder):
                    os.makedirs(thumbnail_folder)
                try:
                    ImageProcessor.create_thumbnail(original_path, username)
                except Exception as e:
                    logging.error(f"创建缩略图失败 {username}/{filename}: {str(e)}")
                    # 如果缩略图创建失败，返回原图
                    return send_from_directory(os.path.dirname(original_path), filename)
        
        return send_from_directory(thumbnail_folder, filename)
    else:
        flash('无权访问此图片。')
        return redirect(url_for('index'))

# 在现有代码中添加一个新的函数来处理缩略图初始化
def initialize_thumbnails():
    """
    Initialize thumbnails for all images that don't have thumbnails yet
    """
    logging.info("开始检查并创建缩略图...")
    
    # 遍历所有用户文件夹
    for username in os.listdir(BASE_IMAGE_FOLDER):
        user_path = os.path.join(BASE_IMAGE_FOLDER, username)
        if not os.path.isdir(user_path):
            continue
            
        # 确保缩略图文件夹存在
        thumbnail_folder = os.path.join(user_path, Settings.THUMBNAIL_FOLDER)
        if not os.path.exists(thumbnail_folder):
            os.makedirs(thumbnail_folder)
            
        # 遍历用户的所有图片
        for filename in os.listdir(user_path):
            # 检查是否是图片文件
            if any(filename.lower().endswith(ext) for ext in Settings.ALLOWED_EXTENSIONS):
                # 检查是否已存在缩略图
                thumbnail_path = os.path.join(thumbnail_folder, filename)
                if not os.path.exists(thumbnail_path):
                    try:
                        original_path = os.path.join(user_path, filename)
                        ImageProcessor.create_thumbnail(original_path, username)
                        logging.info(f"为 {username}/{filename} 创建缩略图")
                    except Exception as e:
                        logging.error(f"创建缩略图失败 {username}/{filename}: {str(e)}")
    
    logging.info("缩略图初始化完成")

# 在现有的路由之后添加新的重置密码路由
@app.route('/reset_password', methods=['POST'])
def reset_password_user():
    try:
        data = request.get_json()
        username = data.get('username')
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        # 验证所有必需字段是否存在
        if not all([username, old_password, new_password]):
            return jsonify({'error': '请填写所有必需字段'}), 400

        # 读取用户数据
        users = []
        user_found = False
        user_id = None
        
        with open(Settings.USER_CSV_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username:
                    # 验证旧密码
                    if not check_password_hash(row['password'], old_password):
                        return jsonify({'error': '原密码错误'}), 401
                    # 更新密码
                    row['password'] = generate_password_hash(new_password)
                    user_found = True
                    user_id = row['id']
                users.append(row)

        if not user_found:
            return jsonify({'error': '用户不存在'}), 404

        # 将更新后的用户数据写回文件
        with open(Settings.USER_CSV_FILE, 'w', newline='') as csvfile:
            fieldnames = ['id', 'username', 'password']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)

        # 记录密码修改日志
        logging.info(f"用户 {username} 成功修改密码")
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })

    except Exception as e:
        logging.error(f"密码重置失败: {str(e)}")
        return jsonify({'error': '密码重置失败，请稍后重试'}), 500

if __name__ == '__main__':
    # 初始化管理员用户
    Utility.initialize_admin()
    
    # 初始化缩略图
    initialize_thumbnails()
    
    app.run(debug=Settings.DEBUG, port=Settings.SERVER_PORT)