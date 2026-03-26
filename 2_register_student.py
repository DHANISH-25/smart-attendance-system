# ============================================================
#  FILE: 2_register_student.py
#  PURPOSE: Register a new student's face into the system
#  HOW: Opens webcam, captures photo, saves to known_faces/
# ============================================================

import cv2
import os

# ── STEP 1: Setup ────────────────────────────────────────────
# Create the known_faces folder if it doesn't exist
KNOWN_FACES_DIR = "known_faces"
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

print("=" * 50)
print("   SMART ATTENDANCE — Student Registration")
print("=" * 50)

# ── STEP 2: Get student name ─────────────────────────────────
student_name = input("\n Enter student full name: ").strip()

# Check if name is empty
if not student_name:
    print("❌ Name cannot be empty!")
    exit()

# Check if student already registered
save_path = os.path.join(KNOWN_FACES_DIR, f"{student_name}.jpg")
if os.path.exists(save_path):
    print(f"⚠️  '{student_name}' is already registered!")
    overwrite = input("   Overwrite? (y/n): ")
    if overwrite.lower() != 'y':
        print("❌ Registration cancelled.")
        exit()

# ── STEP 3: Open webcam ──────────────────────────────────────
print(f"\n📷 Opening camera for: {student_name}")
print("   ➡  Look straight at the camera")
print("   ➡  Press SPACE to capture")
print("   ➡  Press Q to cancel\n")

cam = cv2.VideoCapture(0)  # 0 = default laptop webcam

# Check if camera opened successfully
if not cam.isOpened():
    print("❌ Camera not found! Check your webcam.")
    exit()

captured = False

# ── STEP 4: Show live webcam feed ────────────────────────────
while True:
    ret, frame = cam.read()  # Read one frame from camera

    if not ret:
        print("❌ Failed to read from camera!")
        break

    # Mirror the frame (feels more natural, like a selfie)
    frame = cv2.flip(frame, 1)

    # Draw a green rectangle guide in the center
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    cv2.rectangle(frame, (cx-120, cy-150), (cx+120, cy+150), (0, 255, 0), 2)

    # Show instructions on screen
    cv2.putText(frame, f"Student: {student_name}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, "SPACE = Capture | Q = Quit", (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(frame, "Align face inside the box", (cx-100, cy-165),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Display the frame in a window
    cv2.imshow("Register Student", frame)

    # ── STEP 5: Wait for key press ───────────────────────────
    key = cv2.waitKey(1) & 0xFF

    # SPACE key = capture photo
    if key == 32:
        cv2.imwrite(save_path, frame)
        captured = True
        print(f"\n✅ Face captured and saved!")
        print(f"   📁 Saved to: {save_path}")
        break

    # Q key = quit without saving
    elif key == ord('q'):
        print("\n❌ Registration cancelled by user.")
        break

# ── STEP 6: Cleanup ──────────────────────────────────────────
cam.release()
cv2.destroyAllWindows()

if captured:
    print(f"\n🎉 '{student_name}' successfully registered!")
    print(f"   Total students registered: "
          f"{len(os.listdir(KNOWN_FACES_DIR))}")
    print("\n   ➡  Run 3_mark_attendance.py to take attendance")
