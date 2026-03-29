"""
============================================================
Community Parking Management System
PROJECT 2 TEAM B
Main Application Python + MySQL
============================================================
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import sys
import warnings

# ─────────────────────────────────────────────
# DB CONFIG
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "surya@123",
    "database": "parking_management3",
}

# ─────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────
def pause():
    input("\n  Press ENTER to continue...")

def show_error(msg):
    print(f"\n  ❌  {msg}")

def show_success(msg):
    print(f"\n  ✅  {msg}")

def fmt_dt(value):
    if value is None:
        return "N/A"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %I:%M %p")
    try:
        return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %I:%M %p")
    except ValueError:
        return str(value)

def format_time(hours):
    total_minutes = int(float(hours) * 60)
    days    = total_minutes // (24 * 60)
    remaining = total_minutes % (24 * 60)
    hr      = remaining // 60
    mins    = remaining % 60
    if days > 0:
        return f"{days} day {hr} hr {mins} minutes"
    elif hr > 0:
        return f"{hr} hr {mins} minutes"
    else:
        return f"{mins} minutes"

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        msg = str(e)
        if "Access denied" in msg:
            show_error("Wrong MySQL username or password.")
        elif "Can't connect" in msg or "Connection refused" in msg:
            show_error("Cannot connect to MySQL. Make sure MySQL server is running.")
        elif "Unknown database" in msg:
            show_error("Database not found. Run database_setup.sql first.")
        else:
            show_error(f"Database connection failed: {msg}")
        sys.exit(1)

def run_query(sql, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.rowcount
    except Error as e:
        show_error(f"Query failed: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def call_procedure(proc_name, args):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    results = []
    try:
        cursor.callproc(proc_name, args)
        conn.commit()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for rs in cursor.stored_results():
                results.extend(rs.fetchall())
        return results
    except Error as e:
        msg = str(e)
        if "1644" in msg or "45000" in msg:
            clean = msg.split(":")[-1].strip() if ":" in msg else msg
            show_error(clean)
        else:
            show_error(f"Operation failed: {msg}")
        return None
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────────
# MODULE 1 — View Parking Slots
# ─────────────────────────────────────────────
def view_slots():
    print("\n  ── Parking Slot Status ──")
    available   = run_query("SELECT * FROM v_available_slots", fetch=True)
    total       = run_query("SELECT COUNT(*) AS total FROM parking_slots", fetch=True)
    avail_count = len(available) if available else 0
    total_count = total[0]['total'] if total else 0
    occupied    = total_count - avail_count

    print(f"  Total Slots  : {total_count}")
    print(f"  Available    : {avail_count}")
    print(f"  Occupied     : {occupied}")
    print()

    rows = run_query(
        "SELECT slot_id, slot_type, floor_number, "
        "IF(is_available,'Free','Occupied') AS status "
        "FROM parking_slots ORDER BY floor_number, slot_id",
        fetch=True,
    )
    if rows:
        print(f"  {'Slot ID':<10} {'Type':<8} {'Floor':<10} {'Status'}")
        print("-" * 42)
        for r in rows:
            print(f"  {r['slot_id']:<10} {r['slot_type']:<8} Floor {r['floor_number']:<6} {r['status']}")
    pause()

# ─────────────────────────────────────────────
# MODULE 2 — Vehicle Entry
# ─────────────────────────────────────────────
def vehicle_entry():
    print("\n  ── Vehicle Entry ──")

    vehicle_number = input("  Enter vehicle number  : ").strip().upper()
    if not vehicle_number or len(vehicle_number) < 4:
        show_error("Invalid vehicle number.")
        pause()
        return

    owner_name = input("  Enter owner name      : ").strip()
    if not owner_name:
        show_error("Owner name cannot be empty.")
        pause()
        return

    print("  Vehicle type: ")
    print("  1. Car")
    print("  2. Bike")
    choice = input("  Choose (1|2)          : ").strip()
    if choice == "1":
        vehicle_type = "Car"
    elif choice == "2":
        vehicle_type = "Bike"
    else:
        show_error("Invalid choice. Please enter 1 or 2.")
        pause()
        return

    result = call_procedure("RegisterVehicleEntry", (vehicle_number, owner_name, vehicle_type))
    if not result:
        pause()
        return

    row = result[0]
    slot_no  = row.get("slot_id")
    floor_no = row.get("floor_number")

    if slot_no is None or floor_no is None:
        fallback = run_query(
            """SELECT slot_id, floor_number
               FROM vehicle_records vr
               JOIN parking_slots ps USING (slot_id)
               WHERE vr.vehicle_number = %s AND vr.exit_time IS NULL
               ORDER BY vr.record_id DESC LIMIT 1""",
            (vehicle_number,), fetch=True
        )
        if fallback:
            slot_no  = fallback[0]["slot_id"]
            floor_no = fallback[0]["floor_number"]
        else:
            slot_no  = "N/A"
            floor_no = "N/A"

    rate_rows = run_query("SELECT rate_per_hour FROM fee_table WHERE vehicle_type = %s", (vehicle_type,), fetch=True)
    late_rows = run_query("SELECT rate_per_hour FROM fee_table WHERE vehicle_type = 'Late'", fetch=True)

    rate      = rate_rows[0]['rate_per_hour'] if rate_rows else "N/A"
    late_rate = late_rows[0]['rate_per_hour'] if late_rows else 50
    entry_time = datetime.now().strftime('%Y-%m-%d %I:%M %p')

    print()
    print("  ====================================")
    print("           Entry Receipt              ")
    print("  ====================================")
    print(f"  Vehicle    : {vehicle_number}")
    print(f"  Owner      : {owner_name}")
    print(f"  Type       : {vehicle_type}")
    print(f"  Slot       : {slot_no}")
    print(f"  Floor      : Floor {floor_no}")
    print(f"  Entry Time : {entry_time}")
    print(f"  Rate       : Rs.{rate} per hour")
    print(f"  Min Charge : 1 hour (Rs.{rate})")
    print(f"  Late Fine  : Rs.{late_rate} per day after 24 hrs")
    print("  ====================================")
    show_success("Vehicle entry recorded successfully!")
    pause()

# ─────────────────────────────────────────────
# MODULE 3 — Vehicle Exit
# ─────────────────────────────────────────────
def vehicle_exit():
    print("\n  ── Vehicle Exit ──")

    vehicle_number = input("  Enter vehicle number  : ").strip().upper()
    if not vehicle_number or len(vehicle_number) < 4:
        show_error("Invalid vehicle number.")
        pause()
        return

    result = call_procedure("RegisterVehicleExit", (vehicle_number,))
    if not result:
        pause()
        return

    row         = result[0]
    record_id   = row["record_id"]
    hours       = float(row["hours_parked"])
    parking_fee = float(row["parking_fee"])
    late_fee    = float(row["late_fee"])
    total_fee   = float(row["total_fee_due"])

    time_row = run_query(
        "SELECT entry_time, exit_time FROM vehicle_records WHERE record_id = %s",
        (record_id,), fetch=True
    )
    entry_time = fmt_dt(time_row[0]["entry_time"]) if time_row else "N/A"
    exit_time  = fmt_dt(time_row[0]["exit_time"])  if time_row else "N/A"

    print()
    print("  ====================================")
    print("              Exit Receipt            ")
    print("  ====================================")
    print(f"  {'Record ID':<14}: {record_id}")
    print(f"  {'Vehicle':<14}: {vehicle_number}")
    print(f"  {'Entry Time':<14}: {entry_time}")
    print(f"  {'Exit Time':<14}: {exit_time}")
    print(f"  {'Duration':<14}: {format_time(hours)}")
    print(f"  {'Parking Fee':<14}: Rs.{parking_fee:.2f}")
    print(f"  {'Late Fee':<14}: Rs.{late_fee:.2f}")
    print("  ------------------------------------")
    print(f"  {'Total Due':<14}: Rs.{total_fee:.2f}")
    print("  ====================================")

    while True:
        pay_now = input("\n  Collect payment now? (y/n): ").strip().lower()
        if pay_now == "y":
            pay_result = call_procedure("RecordPayment", (record_id,))
            if pay_result:
                show_success(pay_result[0].get("message", "Payment recorded."))
            break
        elif pay_now == "n":
            print("  Payment pending. Settle from Payment menu.")
            break
        else:
            show_error("Please enter y or n.")
    pause()

# ─────────────────────────────────────────────
# MODULE 4 — Payment Menu
# ─────────────────────────────────────────────
def payment_menu():
    while True:
        print("\n  ── Payment Menu ──")
        print("  [1] Pay Bill by Vehicle Number")
        print("  [2] View All Unpaid Bills")
        print("  [3] Currently Active Vehicles")
        print("  [4] Daily Income Summary")
        print("  [0] Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            vehicle_number = input("  Enter vehicle number: ").strip().upper()
            if not vehicle_number:
                show_error("Vehicle number cannot be empty.")
                pause()
                continue

            unpaid = run_query(
                """SELECT record_id, vehicle_number, owner_name, vehicle_type,
                          entry_time, exit_time, parking_hours,
                          parking_fee, late_fee,
                          (parking_fee + late_fee) AS total_due
                   FROM vehicle_records
                   WHERE vehicle_number = %s
                     AND payment_status = 'Pending'
                     AND exit_time IS NOT NULL
                   ORDER BY exit_time DESC LIMIT 1""",
                (vehicle_number,), fetch=True
            )

            if not unpaid:
                show_error(f"No unpaid bills found for {vehicle_number}.")
            else:
                r   = unpaid[0]
                rid = r["record_id"]
                print()
                print("  ====================================")
                print("              Pending Bill            ")
                print("  ====================================")
                print(f"  {'Record ID':<14}: {rid}")
                print(f"  {'Vehicle':<14}: {r['vehicle_number']}")
                print(f"  {'Owner':<14}: {r['owner_name']}")
                print(f"  {'Type':<14}: {r['vehicle_type']}")
                print(f"  {'Entry Time':<14}: {fmt_dt(r['entry_time'])}")
                print(f"  {'Exit Time':<14}: {fmt_dt(r['exit_time'])}")
                print(f"  {'Duration':<14}: {format_time(r['parking_hours'])}")
                print(f"  {'Parking Fee':<14}: Rs.{r['parking_fee']:.2f}")
                print(f"  {'Late Fee':<14}: Rs.{r['late_fee']:.2f}")
                print("  ------------------------------------")
                print(f"  {'Total Due':<14}: Rs.{r['total_due']:.2f}")
                print("  ====================================")

                while True:
                    c2 = input("\n  Collect payment now? (y/n): ").strip().lower()
                    if c2 == "y":
                        pay_result = call_procedure("RecordPayment", (rid,))
                        if pay_result:
                            show_success(pay_result[0].get("message", "Payment recorded."))
                        break
                    elif c2 == "n":
                        print("  Payment skipped.")
                        break
                    else:
                        show_error("Please enter y or n.")
            pause()

        elif choice == "2":
            unpaid = run_query("SELECT * FROM v_unpaid_exits ORDER BY exit_time", fetch=True)
            if not unpaid:
                print("\n  No unpaid bills. All payments cleared. ✅")
            else:
                print(f"\n  {'ID':<6} {'Vehicle':<14} {'Owner':<18} {'Parking Fee':<14} {'Late Fee':<12} {'Total Due'}")
                print("-" * 72)
                for r in unpaid:
                    print(f"  {r['record_id']:<6} {r['vehicle_number']:<14} "
                          f"{r['owner_name']:<18} Rs.{r['parking_fee']:<12} "
                          f"Rs.{r['late_fee']:<10} Rs.{r['total_due']}")
            pause()

        elif choice == "3":
            rows = run_query("SELECT * FROM v_active_vehicles", fetch=True)
            if not rows:
                print("\n  No vehicles currently parked.")
            else:
                print(f"\n  {'ID':<5} {'Vehicle':<14} {'Owner':<18} {'Type':<6} {'Slot':<6} {'Floor':<8} {'Entry Time':<22} {'Hrs'}")
                print("-" * 85)
                for r in rows:
                    print(f"  {r['record_id']:<5} {r['vehicle_number']:<14} "
                          f"{r['owner_name']:<18} {r['vehicle_type']:<6} "
                          f"{r['slot_id']:<6} Floor {r['floor_number']:<4} "
                          f"{fmt_dt(r['entry_time']):<22} {r['hours_so_far']}")
            pause()

        elif choice == "4":
            d = input("  Enter date (YYYY-MM-DD, blank = today): ").strip()
            if not d:
                d = str(date.today())
            rows = run_query(
                "SELECT IFNULL(SUM(amount_paid), 0) AS daily_income "
                "FROM payment_records WHERE DATE(payment_time) = %s",
                (d,), fetch=True
            )
            if rows:
                print(f"\n  Daily Income on {d}: Rs.{rows[0]['daily_income']}")
            pause()

        elif choice == "0":
            break
        else:
            show_error("Invalid choice.")
            pause()

# ─────────────────────────────────────────────
# MODULE 5 — Reports
# ─────────────────────────────────────────────
def reports_menu():
    while True:
        print("\n  ── Reports Menu ──")
        print("  [1] Daily Report")
        print("  [2] Monthly Revenue")
        print("  [3] Yearly Revenue")
        print("  [4] Total Vehicles Parked (by date)")
        print("  [5] Average Parking Duration")
        print("  [6] Most Used Parking Slots")
        print("  [0] Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            d = input("  Enter date (YYYY-MM-DD, blank = today): ").strip()
            if not d:
                d = str(date.today())
            rows = call_procedure("GenerateDailyReport", (d,))
            if rows:
                r = rows[0]
                print(f"\n  ── Daily Report: {d} ──")
                print("-" * 42)
                print(f"  Total Vehicles  : {r['total_vehicles_parked']}")
                print(f"  Total Revenue   : Rs.{float(r['total_revenue'] or 0):.2f}")
                print(f"  Average Hours   : {float(r['avg_parking_hours'] or 0):.2f} hrs")
                print(f"  Unpaid Entries  : {r['unpaid_entries']}")
            else:
                print("\n  No data found for this date.")
            pause()

        elif choice == "2":
            month = input("  Enter month (MM): ").strip()
            year  = input("  Enter year (YYYY): ").strip()
            if not month.isdigit() or not 1 <= int(month) <= 12:
                show_error("Invalid month.")
                pause()
                continue
            if not year.isdigit() or not 2000 <= int(year) <= 2099:
                show_error("Invalid year.")
                pause()
                continue
            rows = run_query(
                """SELECT IFNULL(SUM(parking_fee), 0) AS monthly_revenue
                   FROM vehicle_records
                   WHERE MONTH(entry_time) = %s AND YEAR(entry_time) = %s
                   AND exit_time IS NOT NULL""",
                (month, year), fetch=True
            )
            if rows:
                print(f"\n  ── Monthly Report: {month}/{year} ──")
                print("-" * 42)
                print(f"  Total Revenue : Rs.{float(rows[0]['monthly_revenue']):.2f}")
            else:
                print("\n  No data found.")
            pause()

        elif choice == "3":
            year = input("  Enter year (YYYY): ").strip()
            if not year.isdigit() or not 2000 <= int(year) <= 2099:
                show_error("Invalid year.")
                pause()
                continue
            rows = run_query(
                """SELECT IFNULL(SUM(parking_fee), 0) AS yearly_revenue
                   FROM vehicle_records
                   WHERE YEAR(entry_time) = %s AND exit_time IS NOT NULL""",
                (year,), fetch=True
            )
            if rows:
                print(f"\n  ── Yearly Report: {year} ──")
                print("-" * 42)
                print(f"  Total Revenue : Rs.{float(rows[0]['yearly_revenue']):.2f}")
            else:
                print("\n  No data found.")
            pause()

        elif choice == "4":
            d = input("  Enter date (YYYY-MM-DD, blank = today): ").strip()
            if not d:
                d = str(date.today())
            rows = run_query(
                "SELECT COUNT(*) AS total FROM vehicle_records WHERE DATE(entry_time) = %s",
                (d,), fetch=True
            )
            if rows:
                print(f"\n  Vehicles Parked on {d}: {rows[0]['total']}")
            pause()

        elif choice == "5":
            rows = run_query(
                """SELECT IFNULL(AVG(parking_hours), 0) AS avg_hrs
                   FROM vehicle_records WHERE exit_time IS NOT NULL""",
                fetch=True
            )
            if rows:
                print(f"\n  Average Parking Duration: {float(rows[0]['avg_hrs']):.2f} hours")
            pause()

        elif choice == "6":
            rows = run_query(
                "SELECT * FROM v_slot_usage_report ORDER BY total_uses DESC LIMIT 2",
                fetch=True
            )
            if not rows:
                print("\n  No slot usage data available.")
            else:
                print(f"\n  {'Slot':<8} {'Type':<8} {'Floor':<10} {'Total Uses'}")
                print("-" * 38)
                for r in rows:
                    print(f"  {r['slot_id']:<8} {r['slot_type']:<8} Floor {r['floor_number']:<6} {r['total_uses']}")
            pause()

        elif choice == "0":
            break
        else:
            show_error("Invalid choice.")
            pause()

# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────
def main():
    db = get_connection()
    while True:
        print("\n  ══ Community Parking Management System ══")
        print("  [1]  View Parking Slots")
        print("  [2]  Vehicle Entry")
        print("  [3]  Vehicle Exit")
        print("  [4]  Payment")
        print("  [5]  Reports")
        print("  [0]  Exit")
        print("  =========================================")
        choice = input("  Enter choice: ").strip()

        if   choice == "1": view_slots()
        elif choice == "2": vehicle_entry()
        elif choice == "3": vehicle_exit()
        elif choice == "4": payment_menu()
        elif choice == "5": reports_menu()
        elif choice == "0":
            db.close()
            print("\n  Goodbye! 👋\n")
            break
        else:
            show_error("Invalid choice. Please enter 0 to 5.")
            pause()

if __name__ == "__main__":
    main()