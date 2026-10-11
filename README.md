# 📱 THE LAHORE ACADAMY JHANG - Mobile App (Flet)

A production-ready, beautiful Android mobile app built from scratch using the **Python Flet Framework** for **THE LAHORE ACADAMY JHANG** Admin/Owner.

---

## 🎯 Architectural Philosophy

1. **Target User: Academy Owner/Admin ONLY (You):**
   * Only **you** install this mobile app on your Android phone.
   * **Students and Parents DO NOT need to install any app.**
2. **100% Free Client WhatsApp Communication:**
   * Automated WhatsApp messages are sent directly from your phone via universal WhatsApp deep-linking and Web integration.
   * **No Meta Cloud API approval or credit card required.**
3. **Frictionless Online Testing:**
   * Students take tests on their phones via a lightweight web link sent to their WhatsApp.
   * **Auto-Grading:** Multiple Choice Questions (MCQs) are graded instantly, and written short answers are evaluated by AI (Google Gemini / semantic model).

---

## 🌟 Core Tabs & Mobile Features

### 👥 Tab 1: Student Directory
* View enrolled students across **9th, 10th, 1st Year (11th)**, and **2nd Year (12th)**.
* Filter by class or search by name / roll number.
* Register new students with Roll No, Name, Class, Enrolled Subjects, Student Mobile, Father Name, Parent WhatsApp, and Monthly Fee.
* **1-Tap WhatsApp Buttons:** Direct chat with Student or Parent.

### 💳 Tab 2: Fee Management & Payment Gateway Settings
* **Payment Gateway Settings:** Enter and save your:
  * 📲 **JazzCash Number & Title**
  * 📱 **EasyPaisa Number & Title**
  * 🏦 **Bank Name, Account Title & IBAN**
* Monthly fee tracking (**Paid** vs **Pending**).
* **1-Click "Send WhatsApp Fee Reminder" Button:** Automatically crafts a polite Roman Urdu message containing the student's pending fee **PLUS your saved JazzCash, EasyPaisa, and Bank details** so parents can pay immediately!
* **1-Click "Mark as Paid" Button:** Updates status to Paid, auto-generates a unique digital receipt (e.g. `REC-2610-0001`), and lets you send the payment receipt to the parent's WhatsApp with 1 tap.

### 📝 Tab 3: Online Test & Auto-Grading Suite
* Create online tests per subject (**Science, Mathematics, English, Computer Science**) and class.
* Add **MCQs** (with 4 options and correct answer) and **Written Short Questions** (with model answers).
* **1-Click "Send Quiz Link to Student WhatsApp":** Generates a link like `http://<your-ip>:8000/quiz/1?sid=1` and pre-fills the invite on WhatsApp.
* Students solve the exam in their phone browser without installing anything!

### 📊 Tab 4: Reports & WhatsApp Dispatcher
* Submissions feed showing completed tests, total marks, percentage, and letter grade (**A+, A, B, C, D, F**).
* Detailed breakdown of MCQs and AI teacher remarks on written short questions.
* **1-Click "Send Scorecard to Father":** Sends formatted report card to the father's WhatsApp.
* **WhatsApp Pairing Engine:** Direct mobile integration active.

---

## 📁 Project File Structure

```text
academy_mobile_app/
│
├── main.py                     # Main Flet Mobile Application & Navigation
├── database.py                 # SQLite ORM models (Students, Fees, Tests, Submissions)
├── seed_data.py                # Pre-populates realistic students, tests & fee invoices
├── requirements.txt            # Python dependencies (flet, sqlalchemy, fastapi, uvicorn, etc.)
├── README.md                   # Beginner setup & APK build instructions
│
├── services/
│   ├── student_service.py      # Student CRUD, validation, and search
│   ├── fee_service.py          # Fee invoices, payment gateway settings & digital receipts
│   ├── test_service.py         # Online test authoring, MCQs, and question pools
│   ├── ai_grading_service.py   # Instant MCQ grading + Gemini AI short question evaluation
│   ├── whatsapp_service.py     # 1-Tap WhatsApp message builder with embedded payment gateways
│   └── quiz_server.py          # Embedded background web server for student exam portal
│
└── views/
    ├── student_view.py         # Tab 1: Student Directory UI
    ├── fee_view.py             # Tab 2: Fee Ledger & Payment Settings UI
    ├── test_view.py            # Tab 3: Online Test & Question Authoring UI
    └── reports_view.py         # Tab 4: Test Scorecards & Parent Dispatch UI
```

---

## 🚀 How to Run the App on Your Computer (Quick Test)

### Step 1: Open Terminal in the App Directory
```powershell
cd C:\Users\Cominn\.gemini\antigravity\scratch\academy_mobile_app
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Run the Mobile App
```powershell
python main.py
```
*A mobile-sized window (portrait layout) will launch immediately on your screen with "THE LAHORE ACADAMY JHANG" at the top header!*

---

## 📦 How to Build the Android `.apk` File (Step-by-Step)

To install this app directly on your Android phone as **"THE LAHORE ACADAMY JHANG"**, follow these steps:

### Option 1: Direct Build with Flet CLI (Local Machine)

1. **Ensure Flutter and Android SDK are installed:**
   * If you have Flutter installed, Flet compiles directly into native Android code!
2. **Run the exact build command in terminal:**
   ```bash
   flet build apk --project the_lahore_academy_jhang --org com.thelahoreacademy.jhang --product "THE LAHORE ACADAMY JHANG"
   ```
3. **Retrieve the generated APK:**
   * Once finished, your installer `.apk` will be located in:
     📁 `build/apk/app-release.apk`
4. **Install on your phone:**
   * Copy `app-release.apk` to your phone via USB cable or send it to yourself on WhatsApp.
   * On your phone, tap `app-release.apk` and select **Install** (allow "Install from Unknown Sources" if prompted).

---

### Option 2: 100% Free Cloud Build (Zero Setup on Your PC)
If you do not have Android Studio or Flutter installed on your PC, you can use **GitHub Actions** to build the `.apk` in 2 minutes for free:

1. Create a free GitHub repository and push this `academy_mobile_app` folder.
2. Add a file `.github/workflows/build_apk.yml`:
   ```yaml
   name: Build Android APK
   on: [push, workflow_dispatch]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: subosito/flutter-action@v2
           with:
             flutter-version: '3.24.x'
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install flet
         - run: flet build apk
         - uses: actions/upload-artifact@v4
           with:
             name: academy-admin-apk
             path: build/apk/*.apk
   ```
3. Push to GitHub. GitHub will compile the `.apk` in the cloud and provide a download link under the **Actions** tab!

---

## 🎓 Online Quiz Testing Walkthrough

1. Go to **Tab 3 (Online Tests)** in the app.
2. Tap **"Send to WA"** next to the test *"10th Mathematics & Physics Midterm"*.
3. Select student **Ali Khan**.
4. WhatsApp will open with the pre-filled test link:
   `http://<your-ip>:8000/quiz/1?sid=1`
5. The student clicks the link on their phone and sees a clean examination interface with MCQs and written questions.
6. When the student clicks **"Submit Exam"**:
   * MCQs are graded instantly.
   * Written short answers are evaluated by AI.
   * Results appear in **Tab 4 (Reports)**.
7. Open **Tab 4**, tap **"Send to Father"**, and Ali's father receives the official scorecard on WhatsApp!
