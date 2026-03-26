# ============================================================
#  FILE: 4_view_attendance.py
#  PURPOSE: View attendance records from CSV files
#           Shows today's report or any past date
# ============================================================

import csv
import os
from datetime import date

ATTENDANCE_DIR = "attendance_records"

print("=" * 55)
print("   SMART ATTENDANCE — View Reports")
print("=" * 55)

# ── List all available attendance files ─────────────────────
files = sorted(os.listdir(ATTENDANCE_DIR)) if os.path.exists(ATTENDANCE_DIR) else []
csv_files = [f for f in files if f.endswith(".csv")]

if not csv_files:
    print("\n❌ No attendance records found!")
    print("   Run 3_mark_attendance.py first.")
    exit()

# ── Show available dates ─────────────────────────────────────
print("\n📅 Available attendance records:")
for i, f in enumerate(csv_files):
    print(f"   [{i+1}] {f.replace('.csv', '')}")

print(f"   [0] Today ({date.today()})")

# ── Select which date to view ────────────────────────────────
choice = input("\nEnter number (or press ENTER for today): ").strip()

if choice == "" or choice == "0":
    filename = os.path.join(ATTENDANCE_DIR, f"{date.today()}.csv")
else:
    try:
        idx      = int(choice) - 1
        filename = os.path.join(ATTENDANCE_DIR, csv_files[idx])
    except (ValueError, IndexError):
        print("❌ Invalid choice!")
        exit()

if not os.path.exists(filename):
    print(f"❌ File not found: {filename}")
    exit()

# ── Read and display the CSV ─────────────────────────────────
print(f"\n{'=' * 55}")
print(f"   📋 ATTENDANCE REPORT")
print(f"   📁 File: {os.path.basename(filename)}")
print(f"{'=' * 55}")

present_list = []
absent_list  = []

with open(filename, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)  # Skip header

    # Print table header
    print(f"\n{'Name':<20} {'Date':<12} {'Time':<12} {'Status'}")
    print("-" * 55)

    for row in reader:
        if row:
            name, date_col, time_col, status = row
            # Color coding in terminal
            status_symbol = "✅" if status == "Present" else "❌"
            print(f"{name:<20} {date_col:<12} {time_col:<12} {status_symbol} {status}")

            if status == "Present":
                present_list.append(name)
            else:
                absent_list.append(name)

# ── Summary ──────────────────────────────────────────────────
total = len(present_list) + len(absent_list)
pct   = int((len(present_list) / total) * 100) if total > 0 else 0

print(f"\n{'=' * 55}")
print(f"   SUMMARY")
print(f"{'=' * 55}")
print(f"   Total Students : {total}")
print(f"   Present        : {len(present_list)} ({pct}%)")
print(f"   Absent         : {len(absent_list)} ({100-pct}%)")
print(f"\n   ✅ Present: {', '.join(present_list) if present_list else 'None'}")
print(f"   ❌ Absent : {', '.join(absent_list)  if absent_list  else 'None'}")
print(f"\n💾 Full data saved at: {filename}")
print("   (Open this .csv file in Excel for full report!)")
