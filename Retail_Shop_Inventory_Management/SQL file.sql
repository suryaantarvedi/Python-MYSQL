-- Create database
CREATE DATABASE IF NOT EXISTS retail_inventory;
USE retail_inventory;

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT,
    brand VARCHAR(100),
    product_name VARCHAR(100),
    price FLOAT,
    quantity INT,
    supplier VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Stock sufficient'
    -- FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Index for product_name for faster search
CREATE INDEX idx_product_name ON products(product_name);

-- Stored procedure to add product
DELIMITER //
CREATE PROCEDURE add_product_proc(
    IN p_category_id INT,
    IN p_brand VARCHAR(100),
    IN p_name VARCHAR(100),
    IN p_price FLOAT,
    IN p_quantity INT,
    IN p_supplier VARCHAR(100)
)
BEGIN
    INSERT INTO products(category_id, brand, product_name, price, quantity, supplier, status)
    VALUES(p_category_id, p_brand, p_name, p_price, p_quantity, p_supplier, 'Stock sufficient');
END;
//
DELIMITER ;

-- Pre-insert some categories
INSERT INTO categories (category_name) VALUES
('Mobile'),
('Laptop'),
('TV'),
('Accessories'),
('Headphones'),
('Camera');


DELIMITER //
CREATE TRIGGER low_stock_before_update
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
    IF NEW.quantity < 5 THEN
        SET NEW.status = CONCAT('Low stock: Only ', NEW.quantity, ' left');
    ELSE
        SET NEW.status = 'Stock sufficient';
    END IF;
END;
//
DELIMITER ;

select * from products;