# 📊 SQL & Python Portfolio Projects  

This repository contains real-world projects showcasing database design, automation, and business-focused analytics. Each project demonstrates how SQL and Python can be combined to solve practical problems.

### 1️⃣ Retail Inventory Program  
A project focused on managing retail store products with categories, automated stock monitoring, and Python integration.  

It includes:  
- 🗄️ **Database Design**: Two main tables — `Categories` and `Products` with foreign key relationships  
- ⚡ **Stored Procedure**: `add_product_proc` ensures consistent product insertion with default stock status  
- 🔍 **Indexing**: Product name index for fast search queries (`LIKE '%phone%'`)  
- 🔄 **Trigger Automation**: Updates stock status automatically (`Low stock: Only X left`) when quantity < 5  
- 📊 **Application Features**:  
  - Add Product (via stored procedure)  
  - View Products (JOIN categories + products)  
  - Search Products (optimized with index)  
  - Update Products (trigger ensures correct stock status)  
  - Delete Products (by product ID)
  
### 2️⃣ Gym Membership Management System  
A project designed to manage gym members, plans, trainers, and revenue summaries.  

It includes:  
- 🗄️ **Database Schema**: Two tables — `membership_plans` and `members` with foreign key enforcement  
- 🧑‍🤝‍🧑 **Member Management**: CRUD operations for adding, viewing, searching, updating, and deleting members  
- 📊 **Reporting Features**:  
  - View All Members (JOIN with membership plans)  
  - Revenue Summary (aggregate queries with `COUNT` and `SUM`)  
  - Search by Member ID or Name  
- ⚡ **Automation**: Bulk deletion of inactive members to keep database clean  
- 🔄 **Program Flow**: Python app with continuous menu loop for CRUD operations

### 3️⃣ Parking Slot Management System  
A project to automate parking slot allocation, entry/exit tracking, and billing.  

It includes:  
- 🗄️ **Database Design**: Multiple tables — `Vehicle Records`, `Parking Slots`, `Fee Table`, `Payment Records`  
- 🚗 **Modules**:  
  - Vehicle Entry (records vehicle details)  
  - Slot Allocation (assigns available slots)  
  - Exit (records exit time + duration)  
  - Billing (calculates fee based on duration)  
  - Reports (vehicles parked, revenue, slot usage)  
- ⚡ **Stored Procedures**:  
  - `RegisterVehicleEntry`, `RegisterVehicleExit`, `RecordPayment`, `GenerateDailyReport`  
- 📊 **Functions**:  
  - `CalculateParkingFee`, `GetDailyRevenue`  
- 🔍 **Views**:  
  - Active Vehicles, Available Slots, Slot Usage Report, Unpaid Exits  
- 📈 **Outputs**: Daily/Monthly/Yearly revenue, most used slots, average parking duration  
- 🚀 **Future Enhancements**: Mobile app integration, QR-based entry/exit, Power BI dashboards 
