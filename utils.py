import csv
import os
import logging
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from setting import Settings
from PIL import Image, ExifTags
from werkzeug.utils import secure_filename
import pathlib

class Utility:
    @staticmethod
    def load_user_from_csv(user_id):
        with open(Settings.USER_CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['id'] == user_id:
                    return User(id=row['id'], username=row['username'], is_admin=(row['username'] == Settings.ADMIN_USERNAME))
        return None

    @staticmethod
    def register_user(username, password):
        hashed_password = generate_password_hash(password)
        try:
            if not os.path.exists(Settings.USER_CSV_FILE):
                with open(Settings.USER_CSV_FILE, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
                    writer.writeheader()

            with open(Settings.USER_CSV_FILE, 'a+', newline='') as csvfile:
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['username'] == username:
                        return False, '用户名已存在！'
                
                writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
                writer.writerow({'id': username, 'username': username, 'password': hashed_password})
            
            os.makedirs(os.path.join(Settings.BASE_IMAGE_FOLDER, username), exist_ok=True)
            return True, '注册成功，请登录！'
        except Exception as e:
            return False, f'注册失败: {str(e)}'

    @staticmethod
    def initialize_admin():
        admin_username = Settings.ADMIN_USERNAME
        admin_password = Settings.ADMIN_PASSWORD
        hashed_password = generate_password_hash(admin_password)

        # 检查管理员用户是否已经存在
        user_exists = False
        if os.path.exists(Settings.USER_CSV_FILE):
            with open(Settings.USER_CSV_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['username'] == admin_username:
                        user_exists = True
                        break

        # 如果管理员用户不存在，则添加
        if not user_exists:
            with open(Settings.USER_CSV_FILE, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
                if os.stat(Settings.USER_CSV_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerow({'id': admin_username, 'username': admin_username, 'password': hashed_password})
            print(f"管理员用户 {admin_username} 已初始化。")

class User(UserMixin):
    def __init__(self, id, username, is_admin=False):
        self.id = id
        self.username = username
        self.is_admin = is_admin 

class ImageProcessor:
    @staticmethod
    def rotate_image_by_exif(img):
        """根据EXIF信息旋转图片"""
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = dict(img._getexif().items())

            if orientation in exif:
                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            # 图片没有EXIF信息或处理出错，返回原图
            pass
        return img

    @staticmethod
    def is_allowed_file(filename):
        """检查文件扩展名是否允许"""
        return pathlib.Path(filename).suffix.lower() in Settings.ALLOWED_EXTENSIONS

    @staticmethod
    def process_image(image_file, output_path):
        """处理图片：调整大小、压缩质量，保持方向"""
        try:
            # 打开图片
            img = Image.open(image_file)
            
            # 处理图片方向
            img = ImageProcessor.rotate_image_by_exif(img)

            # 如果是PNG格式且有透明通道，转换为RGB
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1])
                img = background

            # 调整图片大小
            if max(img.size) > Settings.MAX_IMAGE_SIZE:
                ratio = Settings.MAX_IMAGE_SIZE / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # 保存处理后的图片
            img.save(output_path, 
                    Settings.IMAGE_FORMAT, 
                    quality=Settings.IMAGE_QUALITY, 
                    optimize=True)
            return True
        except Exception as e:
            logging.error(f"处理图片时出错: {str(e)}")
            return False

    @staticmethod
    def create_thumbnail(image_path, username):
        """为图片创建缩略图，保持原图方向"""
        try:
            # 构建缩略图文件夹路径
            thumbnail_dir = os.path.join(Settings.BASE_IMAGE_FOLDER, username, Settings.THUMBNAIL_FOLDER)
            os.makedirs(thumbnail_dir, exist_ok=True)

            # 获取原始文件名并构建缩略图路径
            filename = os.path.basename(image_path)
            thumbnail_path = os.path.join(thumbnail_dir, filename)

            # 如果缩略图已存在，直接返回路径
            if os.path.exists(thumbnail_path):
                return thumbnail_path

            # 创建缩略图
            with Image.open(image_path) as img:
                # 处理图片方向
                img = ImageProcessor.rotate_image_by_exif(img)
                
                # 计算新尺寸
                width, height = img.size
                new_width = int(width * Settings.THUMBNAIL_SIZE)
                new_height = int(height * Settings.THUMBNAIL_SIZE)

                # 如果是PNG格式且有透明通道，转换为RGB
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1])
                    img = background

                # 调整大小并保存
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 
                        Settings.IMAGE_FORMAT,
                        quality=Settings.THUMBNAIL_QUALITY,
                        optimize=True)

            return thumbnail_path
        except Exception as e:
            logging.error(f"创建缩略图时出错: {str(e)}")
            return None

    @staticmethod
    def save_uploaded_image(file, username):
        """保存上传的图片文件并创建缩略图"""
        if file and ImageProcessor.is_allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_folder = os.path.join(Settings.BASE_IMAGE_FOLDER, username)
            
            # 确保用户文件夹存在
            os.makedirs(user_folder, exist_ok=True)
            
            # 生成输出路径
            output_path = os.path.join(user_folder, filename)
            
            # 处理并保存原图
            if ImageProcessor.process_image(file, output_path):
                # 创建缩略图
                ImageProcessor.create_thumbnail(output_path, username)
                logging.info(f"图片上传成功: {username}/{filename}")
                return True, filename
            else:
                return False, "图片处理失败"
        return False, "不支持的文件格式"

    @staticmethod
    def delete_image(username, filename):
        """删除用户图片及其缩略图"""
        try:
            # 删除原图
            file_path = os.path.join(Settings.BASE_IMAGE_FOLDER, username, filename)
            # 删除缩略图
            thumbnail_path = os.path.join(Settings.BASE_IMAGE_FOLDER, username, 
                                        Settings.THUMBNAIL_FOLDER, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                logging.info(f"图片删除成功: {username}/{filename}")
                return True
            return False
        except Exception as e:
            logging.error(f"删除图片时出错: {str(e)}")
            return False 

class UserManager:
    @staticmethod
    def get_all_users():
        """获取所有用户"""
        users = []
        with open(Settings.USER_CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users.append(User(id=row['id'], username=row['username']))
        return users

    @staticmethod
    def delete_user(username):
        """删除用户"""
        users = []
        with open(Settings.USER_CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] != username:
                    users.append(row)

        with open(Settings.USER_CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
            writer.writeheader()
            writer.writerows(users)
        return True

    @staticmethod
    def reset_user_password(username):
        """重置用户密码"""
        new_password = Settings.DEFAULT_PASSWORD
        hashed_password = generate_password_hash(new_password)
        users = []
        
        with open(Settings.USER_CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username:
                    row['password'] = hashed_password
                users.append(row)

        with open(Settings.USER_CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['id', 'username', 'password'])
            writer.writeheader()
            writer.writerows(users)
        
        return new_password

class ImageManager:
    @staticmethod
    def get_user_images(users):
        """获取所有用户的图片并检查/生成缩略图"""
        images = {}
        for user in users:
            if user.username != Settings.ADMIN_USERNAME:  # 跳过管理员
                user_folder = os.path.join(Settings.BASE_IMAGE_FOLDER, user.username)
                if os.path.exists(user_folder):
                    # 获取用户的所有图片
                    user_images = [f for f in os.listdir(user_folder) 
                                 if os.path.isfile(os.path.join(user_folder, f)) and 
                                 ImageProcessor.is_allowed_file(f)]
                    
                    # 检查并生成缺失的缩略图
                    for image in user_images:
                        image_path = os.path.join(user_folder, image)
                        thumbnail_path = os.path.join(user_folder, 
                                                    Settings.THUMBNAIL_FOLDER, 
                                                    image)
                        
                        # 如果缩略图不存在，则创建
                        if not os.path.exists(thumbnail_path):
                            logging.info(f"为图片创建缩略图: {user.username}/{image}")
                            ImageProcessor.create_thumbnail(image_path, user.username)
                    
                    images[user.username] = user_images
        return images

    @staticmethod
    def batch_delete_images(images_data):
        """批量删除图片"""
        success_count = 0
        for image in images_data:
            username = image.get('username')
            filename = image.get('filename')
            if ImageProcessor.delete_image(username, filename):
                success_count += 1
        return success_count 