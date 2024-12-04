### 🐠 Image Feedback

This is a picture display and download app built with Flask, allowing users to register, log in, upload, and download images. The project uses Flask-Login for user authentication and stores user info in a CSV file.

## Prerequisites

- Python 3.10+
- Flask
- Flask-Login
- Werkzeug
- FileSaver.js
- Interact.js

## Running the App

1. Clone or download the project to your local machine.
2. Make sure all dependencies are installed.
3. Fire up the app:

```bash
python app.py
```

4. Open your browser and head to `http://localhost:18888`.

## Build Details

- The project runs on the Flask framework and is launched via the `app.py` file.
- User info is stored in the `users.csv` file.
- Images are saved in the `static/images` directory, with each user having their own folder.

## License

This project is under the Apache License 2.0. Check out the `LICENSE` file for more details.

## Important Notes

- Before deploying to a production environment, make sure to change `your_secret_key` in `app.py` to something more secure.
- This project is for learning and demo purposes only. Don't use it for anything shady.

## Contributing

If you've got improvements or want to contribute code, feel free to submit a Pull Request or open an Issue.

---

Please note that personal identifiable information (PII) and certain hyperlinks have been removed from this document to protect privacy and security.
