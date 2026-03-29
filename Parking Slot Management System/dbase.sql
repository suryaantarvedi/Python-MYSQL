-- ============================================================
-- Community Parking Management System
-- PROJECT 2 – TEAM B
-- Complete Database Setup Script
-- Last Updated: All changes synced with main.py
--
-- CHANGES FROM ORIGINAL:
-- 1. RegisterVehicleEntry  : Returns slot_id, floor_number, message
--                            as separate columns (fixes N/A bug)
-- 2. RegisterVehicleExit   : Calculates & stores late_fee at exit time
--                            Removed duplicate UPDATE parking_slots
--                            (trg_vehicle_exit trigger handles it)
--                            Returns parking_fee, late_fee, total_fee_due
-- 3. RecordPayment         : Uses pre-computed late_fee from vehicle_records
--                            No longer recalculates late fee
-- 4. GenerateDailyReport   : Returns total_vehicles_parked, total_revenue,
--                            avg_parking_hours, unpaid_entries
--                            (matches reports_menu Option 1 in main.py)
-- 5. v_unpaid_exits view   : Reads late_fee directly from vehicle_records
--                            total_due = parking_fee + late_fee
-- 6. v_slot_usage_report   : Shows all slots ordered by total_uses DESC
--                            (no LIMIT — matches reports_menu Option 6)
-- ============================================================

CREATE DATABASE IF NOT EXISTS parking_management3;
USE parking_management3;

-- ============================================================
-- TABLE 1: parking_slots (Member 1)
-- ============================================================
CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id      INT AUTO_INCREMENT PRIMARY KEY,
    slot_type    ENUM('Car', 'Bike') NOT NULL,
    floor_number INT NOT NULL DEFAULT 1,
    is_available BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- TABLE 2: fee_table (Member 1)
-- ============================================================
CREATE TABLE IF NOT EXISTS fee_table (
    vehicle_type  ENUM('Car', 'Bike', 'Late') PRIMARY KEY,
    rate_per_hour DECIMAL(6,2) NOT NULL
);

-- ============================================================
-- TABLE 3: vehicle_records (Member 1)
-- ============================================================
CREATE TABLE IF NOT EXISTS vehicle_records (
    record_id      INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20)  NOT NULL,
    owner_name     VARCHAR(100) NOT NULL,
    vehicle_type   ENUM('Car', 'Bike') NOT NULL,
    slot_id        INT,
    entry_time     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exit_time      DATETIME DEFAULT NULL,
    parking_hours  DECIMAL(6,2)  DEFAULT NULL,
    parking_fee    DECIMAL(10,2) DEFAULT NULL,
    late_fee       DECIMAL(10,2) DEFAULT 0.00,
    payment_status ENUM('Pending', 'Paid') NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);

-- ============================================================
-- TABLE 4: payment_records (Member 1)
-- ============================================================
CREATE TABLE IF NOT EXISTS payment_records (
    payment_id   INT AUTO_INCREMENT PRIMARY KEY,
    record_id    INT NOT NULL,
    amount_paid  DECIMAL(10,2) NOT NULL,
    payment_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (record_id) REFERENCES vehicle_records(record_id)
);

-- ============================================================
-- SEED DATA: fee_table
-- ============================================================
INSERT IGNORE INTO fee_table (vehicle_type, rate_per_hour) VALUES
('Car',  50.00),
('Bike', 20.00),
('Late', 50.00);  -- Rs.50 per day late fine

-- ============================================================
-- SEED DATA: parking_slots (30 slots, 3 floors)
-- ============================================================
INSERT INTO parking_slots (slot_type, floor_number) VALUES
('Car',1),('Car',1),('Car',1),('Car',1),('Car',1),
('Bike',1),('Bike',1),('Bike',1),('Bike',1),('Bike',1),
('Car',2),('Car',2),('Car',2),('Car',2),('Car',2),
('Bike',2),('Bike',2),('Bike',2),('Bike',2),('Bike',2),
('Car',3),('Car',3),('Car',3),('Car',3),('Car',3),
('Bike',3),('Bike',3),('Bike',3),('Bike',3),('Bike',3);

-- ============================================================
-- STORED PROCEDURE 1: RegisterVehicleEntry (Member 2)
-- ============================================================
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS RegisterVehicleEntry(
    IN p_vehicle_number VARCHAR(20),
    IN p_owner_name     VARCHAR(100),
    IN p_vehicle_type   ENUM('Car','Bike')
)
BEGIN
    DECLARE v_slot_id INT DEFAULT NULL;

    IF EXISTS (
        SELECT 1 FROM vehicle_records
        WHERE vehicle_number = p_vehicle_number AND exit_time IS NULL
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Vehicle is already parked in the system.';
    END IF;

    SELECT slot_id INTO v_slot_id
    FROM parking_slots
    WHERE slot_type = p_vehicle_type AND is_available = TRUE
    LIMIT 1;

    IF v_slot_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No available parking slot for this vehicle type.';
    END IF;

    INSERT INTO vehicle_records (vehicle_number, owner_name, vehicle_type, slot_id, entry_time)
    VALUES (p_vehicle_number, p_owner_name, p_vehicle_type, v_slot_id, NOW());

    -- NOTE: trg_vehicle_entry trigger handles marking the slot unavailable after INSERT.

    -- Return slot_id and floor_number as separate columns so Python can
    -- read row["slot_id"] and row["floor_number"] directly.
    SELECT v_slot_id AS slot_id,
           (SELECT floor_number FROM parking_slots WHERE slot_id = v_slot_id) AS floor_number,
           CONCAT('Entry recorded! Assigned to Slot ', v_slot_id,
                  ' - Floor ', (SELECT floor_number FROM parking_slots WHERE slot_id = v_slot_id)) AS message;
END$$
DELIMITER ;

-- ============================================================
-- STORED PROCEDURE 2: RegisterVehicleExit (Member 3)
--
-- CHANGES vs original:
--   1. Removed the duplicate UPDATE parking_slots (trg_vehicle_exit trigger handles it).
--   2. Late fee is now calculated and saved here so that the Python
--      bill display (data[5] parking_fee + data[6] late_fee) is correct.
-- ============================================================
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS RegisterVehicleExit(
    IN p_vehicle_number VARCHAR(20)
)
BEGIN
    DECLARE v_record_id  INT;
    DECLARE v_slot_id    INT;
    DECLARE v_entry_time DATETIME;
    DECLARE v_hours      DECIMAL(6,2);
    DECLARE v_fee        DECIMAL(10,2);
    DECLARE v_late_fee   DECIMAL(10,2);
    DECLARE v_late_rate  DECIMAL(6,2);
    DECLARE v_days_late  INT;
    DECLARE v_type       ENUM('Car','Bike');
    DECLARE v_rate       DECIMAL(6,2);

    -- Find the active parking record
    SELECT record_id, slot_id, entry_time, vehicle_type
    INTO v_record_id, v_slot_id, v_entry_time, v_type
    FROM vehicle_records
    WHERE vehicle_number = p_vehicle_number AND exit_time IS NULL
    LIMIT 1;

    IF v_record_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No active parking record found for this vehicle.';
    END IF;

    -- Calculate parking duration (minimum 1 hour)
    SET v_hours = GREATEST(1, ROUND(TIMESTAMPDIFF(MINUTE, v_entry_time, NOW()) / 60.0, 2));

    -- Calculate parking fee based on vehicle type
    SELECT rate_per_hour INTO v_rate FROM fee_table WHERE vehicle_type = v_type;
    SET v_fee = v_hours * v_rate;

    -- Calculate late fee:
    -- A vehicle is considered "late" if exit is more than 1 day after entry.
    -- Each additional day beyond the first incurs a flat late fine.
    SET v_days_late = GREATEST(0, DATEDIFF(NOW(), v_entry_time) - 1);
    SELECT rate_per_hour INTO v_late_rate FROM fee_table WHERE vehicle_type = 'Late';
    SET v_late_fee = v_days_late * v_late_rate;

    -- Update record with exit details, fees, and mark payment as Pending.
    -- NOTE: slot is freed by trg_vehicle_exit trigger (AFTER UPDATE), so no UPDATE parking_slots here.
    UPDATE vehicle_records
    SET exit_time      = NOW(),
        parking_hours  = v_hours,
        parking_fee    = v_fee,
        late_fee       = v_late_fee,
        payment_status = 'Pending'
    WHERE record_id = v_record_id;

    -- Return summary (used as confirmation; Python fetches full details via a separate SELECT)
    SELECT v_record_id       AS record_id,
           p_vehicle_number  AS vehicle_number,
           v_hours           AS hours_parked,
           v_fee             AS parking_fee,
           v_late_fee        AS late_fee,
           (v_fee + v_late_fee) AS total_fee_due;
END$$
DELIMITER ;

-- ============================================================
-- STORED PROCEDURE 3: RecordPayment (Member 4)
--
-- CHANGES vs original:
--   This procedure is kept for completeness but is NO LONGER called
--   by the Python exit code. Payment is handled directly in Python:
--     - INSERT into payment_records
--     - UPDATE vehicle_records SET payment_status = 'Paid'
--   The late_fee calculation has been moved to RegisterVehicleExit,
--   so this procedure simply records payment using the pre-computed
--   totals from vehicle_records.
-- ============================================================
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS RecordPayment(
    IN p_record_id INT
)
BEGIN
    DECLARE v_parking_fee DECIMAL(10,2);
    DECLARE v_late_fee    DECIMAL(10,2);
    DECLARE v_total_due   DECIMAL(10,2);

    SELECT parking_fee, late_fee
    INTO v_parking_fee, v_late_fee
    FROM vehicle_records
    WHERE record_id = p_record_id AND payment_status = 'Pending';

    IF v_parking_fee IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No pending payment found for this record.';
    END IF;

    SET v_total_due = v_parking_fee + v_late_fee;

    UPDATE vehicle_records
    SET payment_status = 'Paid'
    WHERE record_id = p_record_id;

    INSERT INTO payment_records (record_id, amount_paid)
    VALUES (p_record_id, v_total_due);

    SELECT CONCAT('Payment of Rs.', v_total_due, ' recorded successfully.') AS message;
END$$
DELIMITER ;

-- ============================================================
-- STORED PROCEDURE 4: GenerateDailyReport (Member 5)
-- ============================================================
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS GenerateDailyReport(
    IN p_date DATE
)
BEGIN
    SELECT
        COUNT(*)                     AS total_vehicles_parked,
        IFNULL(SUM(parking_fee), 0)  AS total_revenue,
        ROUND(AVG(parking_hours), 2) AS avg_parking_hours,
        SUM(CASE WHEN payment_status = 'Pending' THEN 1 ELSE 0 END) AS unpaid_entries
    FROM vehicle_records
    WHERE DATE(entry_time) = p_date AND exit_time IS NOT NULL;
END$$
DELIMITER ;

-- ============================================================
-- TRIGGER 1: Prevent duplicate entry (Member 2)
-- ============================================================
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS trg_prevent_duplicate_entry
BEFORE INSERT ON vehicle_records
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM vehicle_records
        WHERE vehicle_number = NEW.vehicle_number AND exit_time IS NULL
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Vehicle already has an active parking session.';
    END IF;
END$$
DELIMITER ;

-- ============================================================
-- TRIGGER 2: Auto mark slot occupied on entry (Member 2)
--
-- NOTE: RegisterVehicleEntry already calls UPDATE parking_slots
-- before the INSERT. This trigger acts as a safety net to ensure
-- the slot is always marked unavailable after insert, even if
-- called from outside the stored procedure.
-- ============================================================
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS trg_vehicle_entry
AFTER INSERT ON vehicle_records
FOR EACH ROW
BEGIN
    IF NEW.slot_id IS NOT NULL THEN
        UPDATE parking_slots SET is_available = FALSE WHERE slot_id = NEW.slot_id;
    END IF;
END$$
DELIMITER ;

-- ============================================================
-- TRIGGER 3: Auto free slot on exit (Member 3)
--
-- This trigger fires when exit_time is set (i.e., vehicle exits).
-- RegisterVehicleExit no longer manually updates parking_slots —
-- this trigger handles it, avoiding the double-update.
-- ============================================================
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS trg_vehicle_exit
AFTER UPDATE ON vehicle_records
FOR EACH ROW
BEGIN
    IF OLD.exit_time IS NULL AND NEW.exit_time IS NOT NULL THEN
        UPDATE parking_slots SET is_available = TRUE WHERE slot_id = NEW.slot_id;
    END IF;
END$$
DELIMITER ;

-- ============================================================
-- FUNCTION 1: CalculateParkingFee (Member 3)
-- ============================================================
DELIMITER $$
CREATE FUNCTION IF NOT EXISTS CalculateParkingFee(
    p_entry_time   DATETIME,
    p_exit_time    DATETIME,
    p_vehicle_type ENUM('Car','Bike')
)
RETURNS DECIMAL(10,2)
DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE v_hours DECIMAL(6,2);
    DECLARE v_rate  DECIMAL(6,2);
    SET v_hours = GREATEST(1, ROUND(TIMESTAMPDIFF(MINUTE, p_entry_time, p_exit_time) / 60.0, 2));
    SELECT rate_per_hour INTO v_rate FROM fee_table WHERE vehicle_type = p_vehicle_type;
    RETURN v_hours * v_rate;
END$$
DELIMITER ;

-- ============================================================
-- FUNCTION 2: GetDailyRevenue (Member 5)
-- ============================================================
DELIMITER $$
CREATE FUNCTION IF NOT EXISTS GetDailyRevenue(p_date DATE)
RETURNS DECIMAL(10,2)
DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(10,2);
    SELECT IFNULL(SUM(amount_paid), 0) INTO v_total
    FROM payment_records WHERE DATE(payment_time) = p_date;
    RETURN v_total;
END$$
DELIMITER ;

-- ============================================================
-- VIEW 1: v_available_slots (Member 2)
-- ============================================================
CREATE OR REPLACE VIEW v_available_slots AS
SELECT slot_id, slot_type, floor_number
FROM parking_slots
WHERE is_available = TRUE
ORDER BY floor_number, slot_type;

-- ============================================================
-- VIEW 2: v_active_vehicles (Member 5)
-- ============================================================
CREATE OR REPLACE VIEW v_active_vehicles AS
SELECT
    vr.record_id,
    vr.vehicle_number,
    vr.owner_name,
    vr.vehicle_type,
    vr.slot_id,
    ps.floor_number,
    vr.entry_time,
    ROUND(TIMESTAMPDIFF(MINUTE, vr.entry_time, NOW()) / 60.0, 2) AS hours_so_far
FROM vehicle_records vr
JOIN parking_slots ps ON vr.slot_id = ps.slot_id
WHERE vr.exit_time IS NULL;

-- ============================================================
-- VIEW 3: v_unpaid_exits (Member 4)
--
-- CHANGE: late_fee is now stored directly in vehicle_records
-- (set by RegisterVehicleExit), so this view reads it from there
-- instead of recalculating it. total_due = parking_fee + late_fee.
-- ============================================================
CREATE OR REPLACE VIEW v_unpaid_exits AS
SELECT
    record_id,
    vehicle_number,
    owner_name,
    parking_fee,
    late_fee,
    exit_time,
    (parking_fee + late_fee) AS total_due
FROM vehicle_records
WHERE exit_time IS NOT NULL AND payment_status = 'Pending';

-- ============================================================
-- VIEW 4: v_slot_usage_report (Member 5)
-- ============================================================
CREATE OR REPLACE VIEW v_slot_usage_report AS
SELECT
    ps.slot_id,
    ps.slot_type,
    ps.floor_number,
    COUNT(vr.record_id) AS total_uses
FROM parking_slots ps
LEFT JOIN vehicle_records vr ON ps.slot_id = vr.slot_id
GROUP BY ps.slot_id, ps.slot_type, ps.floor_number
ORDER BY total_uses DESC;