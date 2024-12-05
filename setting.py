import logging

class Settings:
    DEBUG = True
    SECRET_KEY = 'your-secret-key'
    BASE_IMAGE_FOLDER = 'static/images'
    LOG_DIRECTORY = 'log'
    LOG_FILE = 'log/app.log'
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    USER_CSV_FILE = 'users.csv'
    SERVER_PORT = 18888
    LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT = 5  # 保留5个备份文件
    ADMIN_USERNAME = 'idverne'
    ADMIN_PASSWORD = '1234567890'
    DEFAULT_PASSWORD = '123456'
    IMAGE_QUALITY = 80  # JPEG压缩质量(1-100)
    IMAGE_FORMAT = 'JPEG'  # 保存格式
    MAX_IMAGE_SIZE = 8000  # 最大图片尺寸（长边）
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}  # 允许的图片格式
    MAX_UPLOAD_SIZE = 30 * 1024 * 1024  # 最大上传大小
    THUMBNAIL_SIZE = 0.25  # 缩略图尺寸为原图的25%
    THUMBNAIL_FOLDER = 'thumbnails'  # 缩略图子文件夹名
    THUMBNAIL_QUALITY = 60  # 缩略图质量