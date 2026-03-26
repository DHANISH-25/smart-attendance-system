# 📸 Smart Classroom Attendance System
### With Anti-Spoofing (Blink Detection)

---

## 📁 Project Structure

```
smart_attendance/
│
├── 1_install_packages.txt     ← Run this FIRST
├── 2_register_student.py      ← Add new student faces
├── 3_mark_attendance.py       ← Run daily to take attendance
├── 4_view_attendance.py       ← View attendance reports
├── known_faces/               ← Student photos stored here
└── attendance_records/        ← CSV files saved here
```

---

## 🚀 How to Run (Step by Step)

### Step 1 — Install Libraries
```bash
pip install opencv-python face_recognition dlib imutils scipy numpy
```
> ⚠️ dlib may take 5–10 minutes to install. Be patient!

### Step 2 — Register Students
```bash
python 2_register_student.py
```
- Enter student name when asked
- Look at camera
- Press **SPACE** to capture
- Repeat for each student

### Step 3 — Take Attendance
```bash
python 3_mark_attendance.py
```
- System checks for **blink** first (anti-spoofing)
- Then recognizes face
- Saves to CSV automatically

### Step 4 — View Report
```bash
python 4_view_attendance.py
```

---

## 🛡️ Anti-Spoofing Explained

```
WITHOUT anti-spoofing:
  Someone holds photo of Dhanish → ❌ Marked Present (WRONG!)

WITH blink detection:
  Someone holds photo of Dhanish → No blink detected → ✅ REJECTED!
  Real Dhanish looks at camera   → Blinks naturally  → ✅ Marked Present!
```

**How blink detection works:**
- dlib finds 68 landmark points on your face
- Points 36–47 are around your eyes
- We calculate Eye Aspect Ratio (EAR)
- EAR drops when you blink
- A photo/screen CANNOT blink → rejected!
