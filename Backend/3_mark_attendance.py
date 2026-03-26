# ============================================================
#  FILE: 3_mark_attendance.py
#  PURPOSE: Detect faces + check for blink (anti-spoofing)
#           then mark attendance in a CSV file
#
#  REQUIRES: shape_predictor_68_face_landmarks.dat
#            Download: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
# ============================================================

import cv2
import face_recognition
import dlib
import numpy as np
import csv
import os
from scipy.spatial import distance
from imutils import face_utils
from datetime import datetime, date

# ════════════════════════════════════════════════════════════
#  CONFIGURATION — Change these values if needed
# ════════════════════════════════════════════════════════════

KNOWN_FACES_DIR   = "known_faces"          # Folder with student photos
ATTENDANCE_DIR    = "attendance_records"   # Folder for CSV files
PREDICTOR_PATH    = "shape_predictor_68_face_landmarks.dat"

EAR_THRESHOLD     = 0.25   # Below this value = blink detected
                            # Lower = less sensitive, Higher = more sensitive

REQUIRED_BLINKS   = 1      # How many blinks needed to pass liveness check
LIVENESS_TIMEOUT  = 8      # Seconds before "no blink" timeout

# ════════════════════════════════════════════════════════════
#  STEP 1 — LOAD ALL KNOWN STUDENT FACES
# ════════════════════════════════════════════════════════════

print("=" * 55)
print("   SMART ATTENDANCE SYSTEM — With Anti-Spoofing")
print("=" * 55)
print("\n⏳ Loading student faces from database...")

os.makedirs(ATTENDANCE_DIR, exist_ok=True)

known_encodings = []  # List of face encodings (mathematical face data)
known_names     = []  # List of student names matching encodings

# Loop through every photo in known_faces/ folder
for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith((".jpg", ".jpeg", ".png")):

        # Get student name from filename (remove extension)
        name = os.path.splitext(filename)[0]

        # Load the image file
        img_path = os.path.join(KNOWN_FACES_DIR, filename)
        image    = face_recognition.load_image_file(img_path)

        # Generate face encoding (128 measurements of the face)
        encodings = face_recognition.face_encodings(image)

        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(name)
            print(f"   ✅ Loaded: {name}")
        else:
            print(f"   ⚠️  No face found in photo: {filename}")

print(f"\n📚 {len(known_names)} students loaded: {', '.join(known_names)}")

if len(known_names) == 0:
    print("❌ No students registered! Run 2_register_student.py first.")
    exit()

# ════════════════════════════════════════════════════════════
#  STEP 2 — SETUP BLINK DETECTION (Anti-Spoofing)
# ════════════════════════════════════════════════════════════

# Check if landmark file exists
if not os.path.exists(PREDICTOR_PATH):
    print(f"\n❌ Missing file: {PREDICTOR_PATH}")
    print("   Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
    print("   Extract the .dat file and place it in this folder!")
    exit()

# Load dlib's face detector and 68-point landmark predictor
detector  = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

# Eye landmark indices from dlib's 68-point model
# Left eye:  points 36 to 41
# Right eye: points 42 to 47
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# ── Helper Function: Calculate Eye Aspect Ratio ─────────────
#
#    EAR = (||p2-p6|| + ||p3-p5||) / (2 × ||p1-p4||)
#
#    Eye points layout:
#         p2  p3
#    p1           p4
#         p6  p5
#
#    When eye is OPEN  → EAR ≈ 0.3
#    When eye is CLOSED (blink) → EAR ≈ 0.1
#
def eye_aspect_ratio(eye_points):
    # Vertical distances
    A = distance.euclidean(eye_points[1], eye_points[5])  # p2 to p6
    B = distance.euclidean(eye_points[2], eye_points[4])  # p3 to p5
    # Horizontal distance
    C = distance.euclidean(eye_points[0], eye_points[3])  # p1 to p4
    # EAR formula
    ear = (A + B) / (2.0 * C)
    return ear

# ════════════════════════════════════════════════════════════
#  STEP 3 — SETUP ATTENDANCE CSV FILE
# ════════════════════════════════════════════════════════════

# Create a CSV file named with today's date e.g. "2026-03-15.csv"
today         = date.today().strftime("%Y-%m-%d")
csv_filename  = os.path.join(ATTENDANCE_DIR, f"{today}.csv")

# Track who has already been marked today (avoid duplicates)
already_marked = set()

# If CSV already exists, load who was already marked
if os.path.exists(csv_filename):
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header row
        for row in reader:
            if row:
                already_marked.add(row[0])  # row[0] = Name column
    print(f"\n📋 Existing attendance loaded. Already marked: {already_marked}")

# Write CSV header if file is new
if not os.path.exists(csv_filename):
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Date", "Time", "Status"])

# ── Helper Function: Write attendance to CSV ─────────────────
def mark_attendance(name):
    if name not in already_marked:
        now  = datetime.now()
        time = now.strftime("%I:%M:%S %p")   # e.g. 09:32:15 AM

        with open(csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, today, time, "Present"])

        already_marked.add(name)
        print(f"\n✅ MARKED PRESENT: {name} at {time}")
        return True
    else:
        print(f"\n⚠️  {name} already marked today!")
        return False

# ════════════════════════════════════════════════════════════
#  STEP 4 — MAIN WEBCAM LOOP
#
#  State Machine:
#  "LIVENESS"  → Check for blink first (anti-spoofing)
#  "RECOGNIZE" → Then identify the face
# ════════════════════════════════════════════════════════════

print("\n📷 Starting camera...")
print("   ➡  Look at the camera and BLINK to verify you are real")
print("   ➡  Press Q to quit\n")

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("❌ Camera not found!")
    exit()

# State variables
state         = "LIVENESS"   # Current system state
blink_count   = 0            # How many blinks detected
blink_closed  = False        # Was the eye just closed?
start_time    = datetime.now()
status_msg    = "Please BLINK to verify you are real"
status_color  = (0, 200, 255)  # Yellow

# ── MAIN LOOP ────────────────────────────────────────────────
while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame     = cv2.flip(frame, 1)  # Mirror
    gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w      = frame.shape[:2]
    elapsed   = (datetime.now() - start_time).seconds

    # ── STATE 1: LIVENESS CHECK (Blink Detection) ────────────
    if state == "LIVENESS":

        # Detect faces using dlib
        faces = detector(gray)

        for face_rect in faces:
            # Get 68 facial landmarks
            shape      = predictor(gray, face_rect)
            shape_arr  = face_utils.shape_to_np(shape)

            # Extract left and right eye coordinates
            left_eye   = shape_arr[lStart:lEnd]
            right_eye  = shape_arr[rStart:rEnd]

            # Calculate EAR for both eyes
            left_EAR   = eye_aspect_ratio(left_eye)
            right_EAR  = eye_aspect_ratio(right_eye)
            avg_EAR    = (left_EAR + right_EAR) / 2.0

            # Draw eye contours on frame (so student sees feedback)
            left_hull  = cv2.convexHull(left_eye)
            right_hull = cv2.convexHull(right_eye)
            cv2.drawContours(frame, [left_hull],  -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [right_hull], -1, (0, 255, 0), 1)

            # Show EAR value on screen (for debugging)
            cv2.putText(frame, f"EAR: {avg_EAR:.2f}", (10, h - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # ── BLINK DETECTION LOGIC ────────────────────────
            # When EAR drops below threshold = eye is closing
            if avg_EAR < EAR_THRESHOLD:
                blink_closed = True  # Eye is currently closed

            # When EAR goes back up = eye opened again = 1 blink complete
            if blink_closed and avg_EAR >= EAR_THRESHOLD:
                blink_count  += 1
                blink_closed  = False
                print(f"   👁️  Blink detected! ({blink_count}/{REQUIRED_BLINKS})")

        # ── CHECK IF BLINK REQUIREMENT MET ───────────────────
        if blink_count >= REQUIRED_BLINKS:
            state        = "RECOGNIZE"
            status_msg   = "✅ Liveness verified! Identifying..."
            status_color = (0, 255, 0)  # Green
            start_time   = datetime.now()
            print("\n✅ Liveness check PASSED — proceeding to face recognition")

        # ── TIMEOUT: No blink in time limit ──────────────────
        elif elapsed > LIVENESS_TIMEOUT:
            status_msg   = "❌ SPOOFING DETECTED — No blink! Try again."
            status_color = (0, 0, 255)  # Red
            print("\n🚨 SPOOFING ALERT — No blink detected! Resetting...")
            # Reset after 3 seconds
            cv2.putText(frame, status_msg, (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.imshow("Smart Attendance", frame)
            cv2.waitKey(3000)
            # Reset state
            blink_count  = 0
            blink_closed = False
            start_time   = datetime.now()
            status_msg   = "Please BLINK to verify you are real"
            status_color = (0, 200, 255)

        # ── Show blink counter ────────────────────────────────
        cv2.putText(frame, f"Blinks: {blink_count}/{REQUIRED_BLINKS}", (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Time left: {max(0, LIVENESS_TIMEOUT - elapsed)}s",
                    (w - 160, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # ── STATE 2: FACE RECOGNITION ────────────────────────────
    elif state == "RECOGNIZE":

        # Resize frame to speed up face recognition (process smaller image)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame   = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all face locations in the frame
        face_locations = face_recognition.face_locations(rgb_frame)

        # Generate encodings for all detected faces
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            # Scale back up (we resized by 0.25, so multiply by 4)
            top    *= 4
            right  *= 4
            bottom *= 4
            left   *= 4

            # ── COMPARE with known students ──────────────────
            # Returns list of True/False for each known face
            matches    = face_recognition.compare_faces(known_encodings, face_encoding)

            # Calculate distance (lower = more similar)
            distances  = face_recognition.face_distance(known_encodings, face_encoding)

            name       = "Unknown"
            confidence = 0

            if len(distances) > 0:
                # Pick the best match (lowest distance)
                best_idx  = np.argmin(distances)
                best_dist = distances[best_idx]

                # Only accept if distance is low enough (< 0.5 = good match)
                if matches[best_idx] and best_dist < 0.5:
                    name       = known_names[best_idx]
                    confidence = int((1 - best_dist) * 100)  # Convert to %

            # ── Draw box around face ─────────────────────────
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # ── Show name label ──────────────────────────────
            label = f"{name} ({confidence}%)" if name != "Unknown" else "Unknown"
            cv2.rectangle(frame, (left, bottom), (right, bottom + 30),
                          color, cv2.FILLED)
            cv2.putText(frame, label, (left + 5, bottom + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # ── Mark attendance if recognized ────────────────
            if name != "Unknown":
                mark_attendance(name)
                status_msg   = f"✅ {name} marked Present!"
                status_color = (0, 255, 0)

                # Show success for 2 seconds then reset for next student
                cv2.putText(frame, status_msg, (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
                cv2.imshow("Smart Attendance", frame)
                cv2.waitKey(2000)

                # Reset for next student
                blink_count  = 0
                blink_closed = False
                state        = "LIVENESS"
                start_time   = datetime.now()
                status_msg   = "Next student — Please BLINK"
                status_color = (0, 200, 255)

    # ── DISPLAY STATUS BAR AT TOP ────────────────────────────
    cv2.rectangle(frame, (0, 0), (w, 60), (30, 30, 30), cv2.FILLED)
    cv2.putText(frame, status_msg, (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    # ── SHOW CURRENT STATE ───────────────────────────────────
    state_label = "🔍 LIVENESS CHECK" if state == "LIVENESS" else "👤 RECOGNIZING"
    cv2.putText(frame, state_label, (w - 250, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    cv2.imshow("Smart Attendance", frame)

    # Q = quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ════════════════════════════════════════════════════════════
#  STEP 5 — CLEANUP & SUMMARY
# ════════════════════════════════════════════════════════════
cam.release()
cv2.destroyAllWindows()

print("\n" + "=" * 50)
print(f"   📋 ATTENDANCE SUMMARY — {today}")
print("=" * 50)

# Mark absent students
with open(csv_filename, 'r') as f:
    reader     = csv.reader(f)
    next(reader)
    present    = [row[0] for row in reader if row]

absent = [name for name in known_names if name not in present]
for name in absent:
    with open(csv_filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, today, "—", "Absent"])

print(f"\n✅ Present ({len(present)}): {', '.join(present) if present else 'None'}")
print(f"❌ Absent  ({len(absent)}):  {', '.join(absent) if absent else 'None'}")
print(f"\n💾 Saved to: {csv_filename}")
print("\n   ➡  Run 4_view_attendance.py to see full report")
