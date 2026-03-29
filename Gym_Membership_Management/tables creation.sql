CREATE DATABASE gym_management;
USE gym_management;

-- Table for membership plans
CREATE TABLE membership_plans (
    plan_id INT PRIMARY KEY AUTO_INCREMENT,
    plan_name VARCHAR(20) UNIQUE,
    monthly_fee INT NOT NULL
);

ALTER TABLE membership_plans
ADD CONSTRAINT chk_monthly_fee CHECK (monthly_fee > 0);
-- Insert sample plans
INSERT INTO membership_plans (plan_name, monthly_fee)
VALUES 
('Basic', 1500),
('Premium', 3000),
('Personal', 5000);

-- Table for members
CREATE TABLE members (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    age INT,
    gender VARCHAR(10),
    phone VARCHAR(10) UNIQUE,
    plan_id INT,
    join_date DATE,
    trainer_name VARCHAR(50),
    status VARCHAR(10) DEFAULT 'Active'
);