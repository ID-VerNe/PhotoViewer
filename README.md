# PhotoViewer - A Simple Image Management System

## Overview
PhotoViewer is a lightweight Flask-based image management system designed for multi-user image storage and management. It provides basic functionalities like image upload, viewing, and downloading, along with an admin panel for user management.

## Key Features
- User System
  - User registration/login
  - Admin account
  - Password reset
- Image Management
  - Image upload (drag & drop supported)
  - Image preview (with thumbnails)
  - Image download
  - Batch operations (select/delete)
- Admin Panel
  - User management (add/delete users)
  - Image management (categorized by users)
  - System log viewing

## Tech Stack
- Backend: Python Flask
- Frontend: HTML/CSS/JavaScript
- Storage: File system + CSV
- Image Processing: Pillow

## Requirements
- Python 3.8+
- Supported image formats: JPG, JPEG, PNG, GIF, WebP
- Recommended OS: Windows/Linux/MacOS

## Installation
1. Clone the repository

```
bash
git clone https://github.com/ID-VerNe/PhotoViewer.git
cd PhotoViewer
```

2. Create virtual environment (optional)

```
bash
python -m venv venv
source venv/bin/activate # Linux/MacOS
venv\Scripts\activate # Windows
```


3. Install dependencies

```
bash
pip install -r requirements.txt
```

4. Run the application

```
bash
python app.py
```


## Configuration
Main configuration options in `setting.py`:
- `DEBUG`: Debug mode switch
- `SECRET_KEY`: Application secret key
- `SERVER_PORT`: Server port (default 18888)
- `ADMIN_USERNAME`: Admin username
- `ADMIN_PASSWORD`: Admin password
- `IMAGE_QUALITY`: Image compression quality (1-100)
- `MAX_IMAGE_SIZE`: Maximum image dimension
- `ALLOWED_EXTENSIONS`: Allowed image formats
- `MAX_UPLOAD_SIZE`: Maximum upload size

## Project Structure

```
PhotoViewer/
├── app.py # Main application file
├── setting.py # Configuration file
├── utils.py # Utility functions
├── requirements.txt # Dependencies
├── static/ # Static files
│ ├── images/ # Image storage
│ ├── styles.css # Style sheet
│ └── theme.css # Theme file
├── templates/ # Template files
│ ├── admin.html # Admin panel
│ ├── index.html # Homepage
│ ├── login.html # Login page
│ ├── register.html # Registration page
└ └── upload.html # Upload page
```

## Usage Guide
1. Default Admin Account
   - Username: idverne
   - Password: 1234567890

2. Regular Users
   - Can register through registration page
   - Default reset password: 123456

3. Image Management
   - Supports drag & drop upload
   - Ctrl/Cmd + click to view original image
   - Supports batch selection and deletion

## Important Notes
- Required directories and admin account will be created automatically on first run
- Regular backup of users.csv and image directory is recommended
- Log file is located at log/app.log

## License
Apache License 2.0

## Contributing
Issues and Pull Requests are welcome

## Contact
GitHub: [ID-VerNe](https://github.com/ID-VerNe)
