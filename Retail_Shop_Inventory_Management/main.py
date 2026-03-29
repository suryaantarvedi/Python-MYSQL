import mysql.connector

# ---------------- DATABASE CONNECTION ----------------

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="surya@123",
        database="retail_inventory"
    )

    cursor = db.cursor()
    print("Database Connected Successfully")

except mysql.connector.Error as err:
    print("Database connection failed:", err)
    exit()

# ---------------- CREATE TABLES ----------------

try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        category_name VARCHAR(100)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        category_id INT,
        brand VARCHAR(100),
        product_name VARCHAR(100),
        price FLOAT,
        quantity INT,
        supplier VARCHAR(100),
        status VARCHAR(100)
    )
    """)

    db.commit()

except mysql.connector.Error as err:
    print("Table creation error:", err)

# ---------------- FUNCTIONS ----------------

# ADD PRODUCT
def add_product():
    try:
       name = input("Enter product name: ")

        # check duplicate
       cursor.execute("SELECT product_id, quantity FROM products WHERE product_name=%s",(name,))
       result = cursor.fetchone()

       if result:
            pid, qty = result
            print(f"Product already exists with quantity {qty}")
            add_qty = int(input("Enter quantity to add: "))

            new_qty = qty + add_qty

            cursor.execute(
                "UPDATE products SET quantity=%s WHERE product_id=%s",
                (new_qty,pid)
            )

            db.commit()
            print("Quantity updated successfully")

       else:

            # show categories
            cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
            categories = cursor.fetchall()

            print("\nExisting Categories")
            for c in categories:
                print(f"{c[0]} - {c[1]}")

            category_id = int(input("Enter category ID: "))

            brand = input("Enter brand: ")
            price = float(input("Enter price: "))
            quantity = int(input("Enter quantity: "))
            supplier = input("Enter supplier: ")

            cursor.execute("""
            INSERT INTO products(category_id,brand,product_name,price,quantity,supplier,status)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            """,(category_id,brand,name,price,quantity,supplier,"Stock Sufficient"))

            db.commit()

            print("Product added successfully")

    except ValueError:
        print("Invalid input. Please enter correct values.")

    except mysql.connector.Error as err:
        print("Database error:",err)

# VIEW PRODUCTS
def view_products():
    try:
        # Show all products
        cursor.execute("""
        SELECT p.product_id, p.product_name, 
               p.price, p.quantity
        FROM products p
        """)

        rows = cursor.fetchall()

        print("\nProduct List")
        print("-" * 80)

        print(f"{'ID':<5}{'Product Name':<30}{'Price':<12}{'Quantity':<10}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:<5}{row[1]:<30}{row[2]:<15}{row[4]:<10}")


    except Exception as e:
        print("Error while fetching products:", e)

# SEARCH PRODUCT
def search_product():

    try:                     #   ???????
        name = input("Enter product name to search: ")

        cursor.execute("""
        SELECT p.product_id, p.product_name, c.category_name,
               p.price, p.quantity, p.supplier
        FROM products p
        JOIN categories c
        ON p.category_id = c.category_id
        WHERE p.product_name LIKE %s
        """, ('%' + name + '%',))

        result = cursor.fetchall()

        if result:

            print("\nProduct List")
            print("-" * 80)

            print(f"{'ID':<5}{'Product Name':<30}{'Category':<15}{'Price':<12}{'Quantity':<10}{'Supplier':<20}")
            print("-" * 80)

            for row in result:
                print(f"{row[0]:<5}{row[1]:<30}{row[2]:<15}{row[3]:<12}{row[4]:<10}{row[5]:<20}")

        else:
            print("Product not found")

    except mysql.connector.Error as err:
        print("Database error:", err)
        
# UPDATE PRODUCT
def update_product():

    try:
        name = input("Enter product name to update: ")

        price = float(input("Enter new price: "))
        quantity = int(input("Enter new quantity: "))

        cursor.execute("""
        UPDATE products
        SET price=%s, quantity=%s
        WHERE product_name=%s
        """,(price,quantity,name))

        db.commit()

        print("Product updated successfully")

        if quantity < 5:
            print("⚠ Low Stock Alert! Only few items left.")

    except ValueError:
        print("Invalid input")

    except mysql.connector.Error as err:
        print("Database error:",err)

# DELETE PRODUCT
def delete_product():

    try:
        name = input("Enter product name to delete: ")

        cursor.execute(
            "DELETE FROM products WHERE product_name=%s",(name,)
        )

        db.commit()

        print("Product deleted successfully")

    except mysql.connector.Error as err:
        print("Database error:",err)

# ---------------- MENU ----------------

while True:

    print("\nRetail Inventory System")
    print("1 Add Product")
    print("2 View Products")
    print("3 Search Product")
    print("4 Update Product")
    print("5 Delete Product")
    print("6 Exit")

    try:
        choice = input("Enter your choice: ")

        if choice == "1":
            add_product()

        elif choice == "2":
            view_products()

        elif choice == "3":
            search_product()

        elif choice == "4":
            update_product()

        elif choice == "5":
            delete_product()

        elif choice == "6":
            print("Exiting program")
            break

        else:
            print("Invalid choice")

    except Exception as e:
        print("Error:",e)
try:
    if db.is_connected():
        cursor.close()
        db.close()
except:
    pass


# cursor.execute("""UPDATE products SET price=%s, quantity=%s WHERE product_name=%s  """,(price,quantity,name))
