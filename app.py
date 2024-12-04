import logging
import csv
import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话加密

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 假设图片存储在static/images目录下
BASE_IMAGE_FOLDER = 'static/images'

# 用户类
class User(UserMixin):
    def __init__(self, id, username, is_admin=False):
        self.id = id
        self.username = username
        self.is_admin = is_admin

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    with open('users.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['id'] == user_id:
                return User(id=row['id'], username=row['username'], is_admin=(row['username'] == 'admin'))
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            # 确保文件存在并可读
            if not os.path.exists('users.csv'):
                with open('users.csv', 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
                    writer.writeheader()

            with open('users.csv', 'a+', newline='') as csvfile:
                csvfile.seek(0)  # 确保从文件开头读取
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['username'] == username:
                        flash('用户名已存在！')
                        return render_template('register.html')
                
                writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
                writer.writerow({'id': username, 'username': username, 'password': hashed_password})
            
            os.makedirs(os.path.join(BASE_IMAGE_FOLDER, username), exist_ok=True)
            flash('注册成功，请登录！')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'注册失败: {str(e)}')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open('users.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username and check_password_hash(row['password'], password):
                    user_obj = User(id=row['id'], username=username, is_admin=(username == 'admin'))
                    login_user(user_obj)
                    flash('登录成功！')
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
        # 管理员查看所有用户的图片
        user_folders = [f for f in os.listdir(BASE_IMAGE_FOLDER) if os.path.isdir(os.path.join(BASE_IMAGE_FOLDER, f))]
        images = {user: os.listdir(os.path.join(BASE_IMAGE_FOLDER, user)) for user in user_folders}
    else:
        # 普通用户查看自己的图片
        user_folder = os.path.join(BASE_IMAGE_FOLDER, current_user.username)
        images = {current_user.username: os.listdir(user_folder)}
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

if __name__ == '__main__':
    app.run(debug=True,port=18888)