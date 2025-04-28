# Face Attend

Welcome to **Face Attend** — a smart and seamless attendance tracking system using face recognition technology!  
Forget manual roll calls — automate and modernize the way you manage attendance with real-time face detection and logging.

---

## 🚀 Features
- 📸 Real-time face detection and recognition
- 🗂️ Automatic enrollment and attendance logging
- 🛡️ Secure, reliable and configurable
- ⚡ Fast and lightweight
- 🎯 Easy to use and extend

---

## 🛠️ Technologies Used
- Python 🐍
- OpenCV (cv2) 🎥
- face_recognition library 🤖
- SQLite3 for user & attendance storage 🗄️
- Custom `sendmail` module for email notifications ✉️

---

## 📂 Project Structure
```
face-attend/
🗂️ Enrolled/               # Stores enrolled face images (named by regno.jpg)
🕚 identifier.sqlite       # SQLite database for users & attendance
🕚 main.py                 # Main script (enroll() & detect() functions)
🕚 sendmail.py             # Email-sending helper module
🕚 requirements.txt        # Python dependencies
🕚 README.md               # This file
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Ayushskull7/Face-Attend.git
cd face-attend
```

### 2. Create & Activate Virtual Environment (Recommended)
```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Email Settings
- Open `sendmail.py`
- Update your SMTP server, sender email, and password/API details.

### 5. Run the Application
```bash
python main.py
```

---

## 🎯 Usage Workflow

### Enrollment
- Script will launch webcam.
- Press **`c`** to capture a frame.
- Enter:
  - Name
  - Role
  - Registration Number (regno)
- The face image will be saved in the `Enrolled/` folder and data stored in `identifier.sqlite`.

### Detection
- Launch detection.
- Webcam will recognize registered faces.
- Automatically mark attendance and send optional email notifications.

---

## 📅 Future Enhancements
- Add GUI interface
- Integrate Cloud database support
- Multi-camera setup for larger spaces
- Mobile app integration for live tracking

---

## 🚀 Let's make attendance smarter with **Face Attend**!

---

### ✨ Made with passion for smart systems ✨

