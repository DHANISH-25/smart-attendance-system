# ============================================================
#  FILE: app.py
#  PURPOSE: Flask API Bridge between React UI and Python
#  RUN: python app.py
#  API runs at: http://localhost:5000
# ============================================================

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import cv2
import os
import csv
import threading
import face_recognition
import numpy as np
from datetime import date, datetime

app = Flask(__name__)
CORS(app)  # Allow React (port 3000) to talk to Flask (port 5000)

# ── CONFIG ───────────────────────────────────────────────────
KNOWN_FACES_DIR  = "known_faces"
ATTENDANCE_DIR   = "attendance_records"
PREDICTOR_PATH   = "shape_predictor_68_face_landmarks.dat"

os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DIR,  exist_ok=True)

# ── CAMERA STATE (shared across threads) ─────────────────────
camera_state = {
    "active":   False,
    "frame":    None,
    "status":   "idle",
    "message":  "",
    "lock":     threading.Lock()
}

# ════════════════════════════════════════════════════════════
#  ENDPOINT 1 — GET /api/students
#  Returns list of all registered students
# ════════════════════════════════════════════════════════════
@app.route("/api/students", methods=["GET"])
def get_students():
    students = []
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            name = os.path.splitext(filename)[0]
            path = os.path.join(KNOWN_FACES_DIR, filename)
            stat = os.stat(path)
            students.append({
                "name":       name,
                "photo":      filename,
                "registered": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
            })
    return jsonify({ "success": True, "students": students, "total": len(students) })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 2 — POST /api/register
#  Opens webcam, captures face, saves to known_faces/
# ════════════════════════════════════════════════════════════
@app.route("/api/register", methods=["POST"])
def register_student():
    data = request.json
    name = data.get("name", "").strip()

    if not name:
        return jsonify({ "success": False, "message": "Name is required!" }), 400

    save_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")

    # Open webcam
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        return jsonify({ "success": False, "message": "Camera not found!" }), 500

    captured = False
    print(f"\n📷 Registering: {name}")
    print("   Look at camera → Press SPACE to capture → Q to cancel")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Draw guide box
        cv2.rectangle(frame, (cx-120, cy-150), (cx+120, cy+150), (0, 255, 0), 2)
        cv2.putText(frame, f"Registering: {name}", (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "SPACE = Capture  |  Q = Cancel", (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow(f"Register — {name}", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE
            cv2.imwrite(save_path, frame)
            captured = True
            print(f"✅ Saved: {save_path}")
            break
        elif key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

    if captured:
        return jsonify({ "success": True, "message": f"{name} registered successfully!" })
    else:
        return jsonify({ "success": False, "message": "Registration cancelled." })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 3 — GET /api/attendance/today
#  Returns today's attendance from CSV
# ════════════════════════════════════════════════════════════
@app.route("/api/attendance/today", methods=["GET"])
def get_today_attendance():
    today    = date.today().strftime("%Y-%m-%d")
    filename = os.path.join(ATTENDANCE_DIR, f"{today}.csv")
    records  = []

    if os.path.exists(filename):
        with open(filename, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)

    present = [r for r in records if r.get("Status") == "Present"]
    absent  = [r for r in records if r.get("Status") == "Absent"]

    return jsonify({
        "success":      True,
        "date":         today,
        "records":      records,
        "present_count": len(present),
        "absent_count":  len(absent),
        "total":        len(records),
        "percentage":   round(len(present) / len(records) * 100) if records else 0,
    })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 4 — GET /api/attendance/<date>
#  Returns attendance for any specific date
# ════════════════════════════════════════════════════════════
@app.route("/api/attendance/<date_str>", methods=["GET"])
def get_attendance_by_date(date_str):
    filename = os.path.join(ATTENDANCE_DIR, f"{date_str}.csv")
    records  = []

    if not os.path.exists(filename):
        return jsonify({ "success": False, "message": f"No record for {date_str}" }), 404

    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    present = [r for r in records if r.get("Status") == "Present"]

    return jsonify({
        "success":       True,
        "date":          date_str,
        "records":       records,
        "present_count": len(present),
        "absent_count":  len(records) - len(present),
        "total":         len(records),
        "percentage":    round(len(present) / len(records) * 100) if records else 0,
    })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 5 — GET /api/attendance/dates
#  Returns all available attendance dates
# ════════════════════════════════════════════════════════════
@app.route("/api/attendance-dates", methods=["GET"])
def get_attendance_dates():
    dates = []
    if os.path.exists(ATTENDANCE_DIR):
        for f in sorted(os.listdir(ATTENDANCE_DIR), reverse=True):
            if f.endswith(".csv"):
                dates.append(f.replace(".csv", ""))
    return jsonify({ "success": True, "dates": dates })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 6 — POST /api/start-attendance
#  Starts the face recognition + blink detection camera
# ════════════════════════════════════════════════════════════
@app.route("/api/start-attendance", methods=["POST"])
def start_attendance():
    if camera_state["active"]:
        return jsonify({ "success": False, "message": "Camera already running!" })

    # Run in background thread so API stays responsive
    thread = threading.Thread(target=run_attendance_camera)
    thread.daemon = True
    thread.start()

    return jsonify({ "success": True, "message": "Attendance camera started!" })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 7 — POST /api/stop-attendance
#  Stops the attendance camera
# ════════════════════════════════════════════════════════════
@app.route("/api/stop-attendance", methods=["POST"])
def stop_attendance():
    camera_state["active"] = False
    return jsonify({ "success": True, "message": "Camera stopped!" })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 8 — GET /api/camera-status
#  Returns current camera status and last marked student
# ════════════════════════════════════════════════════════════
@app.route("/api/camera-status", methods=["GET"])
def camera_status():
    return jsonify({
        "active":  camera_state["active"],
        "status":  camera_state["status"],
        "message": camera_state["message"],
    })


# ════════════════════════════════════════════════════════════
#  ENDPOINT 9 — GET /api/video-feed
#  Streams live camera feed to React (MJPEG stream)
# ════════════════════════════════════════════════════════════
@app.route("/api/video-feed")
def video_feed():
    def generate():
        while camera_state["active"]:
            with camera_state["lock"]:
                frame = camera_state["frame"]
            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" +
                       buffer.tobytes() + b"\r\n")
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ════════════════════════════════════════════════════════════
#  ENDPOINT 10 — DELETE /api/students/<name>
#  Remove a student from the system
# ════════════════════════════════════════════════════════════
@app.route("/api/students/<name>", methods=["DELETE"])
def delete_student(name):
    for ext in [".jpg", ".jpeg", ".png"]:
        path = os.path.join(KNOWN_FACES_DIR, f"{name}{ext}")
        if os.path.exists(path):
            os.remove(path)
            return jsonify({ "success": True, "message": f"{name} removed!" })
    return jsonify({ "success": False, "message": "Student not found!" }), 404


# ════════════════════════════════════════════════════════════
#  BACKGROUND FUNCTION — Runs attendance camera in thread
# ════════════════════════════════════════════════════════════
def run_attendance_camera():
    import dlib
    from scipy.spatial import distance
    from imutils import face_utils

    EAR_THRESHOLD   = 0.25
    REQUIRED_BLINKS = 1
    LIVENESS_TIMEOUT = 8

    # Load known faces
    known_encodings = []
    known_names     = []
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            name  = os.path.splitext(filename)[0]
            image = face_recognition.load_image_file(
                        os.path.join(KNOWN_FACES_DIR, filename))
            encs  = face_recognition.face_encodings(image)
            if encs:
                known_encodings.append(encs[0])
                known_names.append(name)

    if not known_names:
        camera_state["status"]  = "error"
        camera_state["message"] = "No students registered!"
        return

    # Load dlib
    if not os.path.exists(PREDICTOR_PATH):
        camera_state["status"]  = "error"
        camera_state["message"] = "shape_predictor file missing!"
        return

    detector  = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(PREDICTOR_PATH)
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    def ear(eye):
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        C = distance.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    # CSV setup
    today        = date.today().strftime("%Y-%m-%d")
    csv_file     = os.path.join(ATTENDANCE_DIR, f"{today}.csv")
    already_marked = set()

    if os.path.exists(csv_file):
        with open(csv_file, "r") as f:
            for row in csv.reader(f):
                if row: already_marked.add(row[0])
    else:
        with open(csv_file, "w", newline="") as f:
            csv.writer(f).writerow(["Name", "Date", "Time", "Status"])

    # Camera loop
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    camera_state["active"]  = True
    camera_state["status"]  = "liveness"
    camera_state["message"] = "Please blink to verify"

    state        = "LIVENESS"
    blink_count  = 0
    blink_closed = False
    start_time   = datetime.now()

    while camera_state["active"]:
        ret, frame = cam.read()
        if not ret: break

        frame    = cv2.flip(frame, 1)
        gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w     = frame.shape[:2]
        elapsed  = (datetime.now() - start_time).seconds

        if state == "LIVENESS":
            for face in detector(gray):
                shape     = face_utils.shape_to_np(predictor(gray, face))
                left_eye  = shape[lStart:lEnd]
                right_eye = shape[rStart:rEnd]
                avg_ear   = (ear(left_eye) + ear(right_eye)) / 2.0

                cv2.drawContours(frame, [cv2.convexHull(left_eye)],  -1, (0,255,0), 1)
                cv2.drawContours(frame, [cv2.convexHull(right_eye)], -1, (0,255,0), 1)
                cv2.putText(frame, f"EAR: {avg_ear:.2f}", (10, h-40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

                if avg_ear < EAR_THRESHOLD:
                    blink_closed = True
                if blink_closed and avg_ear >= EAR_THRESHOLD:
                    blink_count += 1
                    blink_closed = False

            if blink_count >= REQUIRED_BLINKS:
                state = "RECOGNIZE"
                camera_state["status"]  = "recognizing"
                camera_state["message"] = "Identifying face..."
                start_time = datetime.now()

            elif elapsed > LIVENESS_TIMEOUT:
                blink_count  = 0
                blink_closed = False
                start_time   = datetime.now()
                camera_state["message"] = "No blink! Spoofing rejected."

            msg_color = (0, 200, 255)
            cv2.putText(frame, f"BLINK TO VERIFY ({blink_count}/{REQUIRED_BLINKS})",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, msg_color, 2)

        elif state == "RECOGNIZE":
            small      = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
            rgb        = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locations  = face_recognition.face_locations(rgb)
            encodings  = face_recognition.face_encodings(rgb, locations)

            for (top,right,bottom,left), enc in zip(locations, encodings):
                top*=4; right*=4; bottom*=4; left*=4
                matches   = face_recognition.compare_faces(known_encodings, enc)
                distances = face_recognition.face_distance(known_encodings, enc)
                name      = "Unknown"

                if len(distances) > 0:
                    idx = np.argmin(distances)
                    if matches[idx] and distances[idx] < 0.5:
                        name = known_names[idx]

                color = (0,255,0) if name != "Unknown" else (0,0,255)
                cv2.rectangle(frame, (left,top), (right,bottom), color, 2)
                cv2.putText(frame, name, (left, bottom+25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

                if name != "Unknown" and name not in already_marked:
                    now = datetime.now().strftime("%I:%M:%S %p")
                    with open(csv_file, "a", newline="") as f:
                        csv.writer(f).writerow([name, today, now, "Present"])
                    already_marked.add(name)
                    camera_state["message"] = f"✅ {name} marked Present!"
                    print(f"✅ Marked: {name} at {now}")

                    # Reset for next student
                    blink_count  = 0
                    blink_closed = False
                    state        = "LIVENESS"
                    start_time   = datetime.now()
                    camera_state["status"]  = "liveness"

        # Status bar
        cv2.rectangle(frame, (0,0), (w,55), (20,20,40), -1)
        cv2.putText(frame, camera_state["message"], (10,38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        # Share frame with video feed endpoint
        with camera_state["lock"]:
            camera_state["frame"] = frame.copy()

    # Cleanup — mark absent
    with open(csv_file, "r") as f:
        present = [r[0] for r in csv.reader(f) if r]
    for name in known_names:
        if name not in present:
            with open(csv_file, "a", newline="") as f:
                csv.writer(f).writerow([name, today, "—", "Absent"])

    cam.release()
    camera_state["active"]  = False
    camera_state["status"]  = "idle"
    camera_state["message"] = "Camera stopped"
    print("📷 Camera stopped.")


# ════════════════════════════════════════════════════════════
#  START SERVER
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 50)
    print("   Smart Attendance — Flask API")
    print("   Running at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, threaded=True, port=5000)
