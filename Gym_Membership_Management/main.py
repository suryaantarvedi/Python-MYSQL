import mysql.connector

# Connect to MySQL
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="surya@123",   # change if needed
        database="gym_management"
    )
    cursor = db.cursor()
    print("Database connection successful!")

except mysql.connector.Error as err:
    print("Database connection failed:", err)
    exit()

# -------------------------------
# Functions
# -------------------------------

def add_member():
    # Show available plans
    cursor.execute("SELECT plan_id, plan_name, monthly_fee FROM membership_plans")
    plans = cursor.fetchall()
    print("Available Plans:")
    for plan in plans:
        print(f"{plan[0]} - {plan[1]} (Fee: {plan[2]})")

    # Collect member details
    name = input("Enter Member Name: ")
    age = int(input("Enter Age: "))
    gender = input("Enter Gender: ")

    # Validate phone number (must be exactly 10 digits)
    while True:
        phone = input("Enter Phone Number: ")
        if len(phone) == 10:
            break
        else:
            print("Invalid phone number! Please enter exactly 10 digits.")

    plan_id = int(input("Enter Plan ID (choose number from above): "))
    join_date = input("Enter Join Date (YYYY-MM-DD): ")
    trainer = input("Enter Trainer Name: ")

    sql = """INSERT INTO members 
             (name, age, gender, phone, plan_id, join_date, trainer_name, status)
             VALUES (%s,%s,%s,%s,%s,%s,%s,'Active')"""
    values = (name, age, gender, phone, plan_id, join_date, trainer)

    cursor.execute(sql, values)
    db.commit()
    print("Member added successfully!")

def view_members():
    print("\n--- View Members ---")
    print("1 Show all members")
    print("2 Show gym membership summary")
    choice = input("Enter choice: ")

    if choice == "1":
        cursor.execute("""
            SELECT m.member_id, m.name, p.plan_name, p.monthly_fee, m.status
            FROM members m
            JOIN membership_plans p ON m.plan_id = p.plan_id
        """)
        rows = cursor.fetchall()
        print(f"{'ID':<5}{'Name':<15}{'Plan':<15}{'Fee':<10}{'Status':<10}")
        print("-" * 55)
        for row in rows:
            print(f"{row[0]:<5}{row[1]:<15}{row[2]:<15}{row[3]:<10}{row[4]:<10}")



    elif choice == "2":
        cursor.execute("""
            SELECT p.plan_name,
                   COUNT(m.member_id) AS total_members,
                   SUM(p.monthly_fee) AS total_revenue
            FROM members m
            JOIN membership_plans p ON m.plan_id = p.plan_id
            WHERE m.status = 'Active'
            GROUP BY p.plan_name
        """)
        rows = cursor.fetchall()
        print("Plan   Members   Revenue")
        for row in rows:
            print(row[0], row[1], row[2])

def search_member():
    choice = input("Search by (1) ID or (2) Name: ")
    if choice == "1":
        member_id = input("Enter Member ID: ")
        cursor.execute("""
            SELECT m.member_id, m.name, m.phone, m.status,
                   p.plan_name, p.monthly_fee
            FROM members m
            JOIN membership_plans p ON m.plan_id = p.plan_id
            WHERE m.member_id = %s
        """, (member_id,))
    else:
        name = input("Enter Member Name: ")
        cursor.execute("""
            SELECT m.member_id, m.name, m.phone, m.status,
                   p.plan_name, p.monthly_fee
            FROM members m
            JOIN membership_plans p ON m.plan_id = p.plan_id
            WHERE m.name = %s
        """, (name,))

    result = cursor.fetchone()
    if result:
        print(f"{'ID':<5}{'Name':<15}{'Phone':<15}{'Status':<10}{'Plan':<15}{'Fee':<10}")
        print("-" * 70)
        print(f"{result[0]:<5}{result[1]:<15}{result[2]:<15}{result[3]:<10}{result[4]:<15}{result[5]:<10}")
    else:
        print("No member found.")

def update_member():
    member_id = input("Enter Member ID to update: ")

    new_phone = input("Enter new phone: ")
    # Show available plans
    cursor.execute("SELECT plan_id, plan_name, monthly_fee FROM membership_plans")
    plans = cursor.fetchall()
    print("Available Plans:")
    for plan in plans:
        print(f"{plan[0]} - {plan[1]} (Fee: {plan[2]})")
    new_plan_id = int(input("Enter new Plan ID: "))
    new_trainer = input("Enter new trainer: ")
    new_status = input("Enter new status: ")

    sql = """UPDATE members 
             SET phone=%s, plan_id=%s, trainer_name=%s, status=%s 
             WHERE member_id=%s"""
    values = (new_phone, new_plan_id, new_trainer, new_status, member_id)

    cursor.execute(sql, values)
    db.commit()
    print("Member updated successfully!")

def delete_member():
    print("Choose deletion type:")
    print("1 Delete Member")
    print("2 Delete All Inactive Members")
    choice = input("Enter choice: ")

    if choice == "1":
        member_id = input("Enter Member ID: ")
        cursor.execute("SELECT status FROM members WHERE member_id=%s", (member_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute("DELETE FROM members WHERE member_id=%s", (member_id,))
            db.commit()
            print("Member deleted successfully.")
        else:
            print("Member not found.")

    elif choice == "2":
        cursor.execute("DELETE FROM members WHERE status='Inactive'")
        db.commit()
        print("All inactive members deleted successfully.")

    else:
        print("Invalid choice.")

# -------------------------------
# Menu-driven flow (5 options)
# -------------------------------
while True:
    print("\n--- Gym Membership Menu ---")
    print("1 Add Member")
    print("2 View Members")
    print("3 Search Member")
    print("4 Update Member")
    print("5 Delete Member")
    print("6 Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        add_member()
    elif choice == "2":
        view_members()
    elif choice == "3":
        search_member()
    elif choice == "4":
        update_member()
    elif choice == "5":
        delete_member()
    elif choice == "6":
        print("Exiting program...")
        break
    else:
        print("Invalid choice. Try again.")

try:
    if db.is_connected():
        cursor.close()
        db.close()
except:
    pass