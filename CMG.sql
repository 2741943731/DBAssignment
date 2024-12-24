USE CMG;

drop table if exists Orders;
drop table if exists Customer;
drop table if exists Car;
drop table if exists Warehouse;
drop table if exists Factory;
drop table if exists employee;


-- 创建仓库表 (Warehouse)
CREATE TABLE if not exists Warehouse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    total_inventory INT DEFAULT 0,
    manager_id INT NOT NULL
);

-- 创建厂商表 (Factory)
CREATE TABLE if not exists Factory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200),
    contact_info VARCHAR(100)
);

-- 创建汽车表 (Car)
CREATE TABLE if not exists Car (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    warehouse_id INT NOT NULL,
    factory_id INT NOT NULL,
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(id) ON DELETE CASCADE,
    FOREIGN KEY (factory_id) REFERENCES Factory(id) ON DELETE CASCADE
);

-- 创建客户表 (Customer)
CREATE TABLE if not exists Customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    address VARCHAR(200) NOT NULL
);

-- 创建订单表 (Order)
CREATE TABLE if not exists Orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    car_id INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customer(id) ON DELETE CASCADE,
    FOREIGN KEY (car_id) REFERENCES Car(id) ON DELETE CASCADE
);

CREATE TABLE Employee (
    employee_id VARCHAR(20)  PRIMARY KEY COMMENT '员工ID',
    password VARCHAR(255) NOT NULL COMMENT '员工密码，建议加密存储',
    name VARCHAR(100) NOT NULL COMMENT '员工姓名',
    contact VARCHAR(50) COMMENT '员工联系方式',
    employee_type ENUM('管理员', '仓库管理员', '销售管理员') NOT NULL COMMENT '员工类型'
) COMMENT='员工表，存储所有员工信息';

-- 测试数据插入 (可选)
INSERT INTO Factory (name, address, contact_info)
VALUES ('Toyota', '123 Factory Lane', 'factory1@example.com'), 
       ('Honda', '456 Industrial Blvd', 'factory2@example.com');

INSERT INTO Warehouse (name, total_inventory, manager_id)
VALUES ('Main Warehouse', 100, 1), ('Secondary Warehouse', 50, 2);

INSERT INTO Car (model, price, warehouse_id, factory_id)
VALUES ('Toyota Corolla', 20000.00, 1, 1), 
       ('Honda Civic', 22000.00, 1, 2), 
       ('Ford Focus', 18000.00, 2, 1);

INSERT INTO Customer (name, phone, address)
VALUES ('Alice', '1234567890', '123 Main St'), 
       ('Bob', '0987654321', '456 Elm St');

INSERT INTO Orders (customer_id, car_id, quantity)
VALUES (1, 1, 1), (2, 3, 2);

INSERT INTO Employee (employee_id, password, name, contact, employee_type)
VALUES
    ('admin', 'admin123', '张三', '1234567890', '管理员'),
    ('warehouse01', 'warehouse123', '李四', '0987654321', '仓库管理员'),
    ('sales01', 'sales123', '王五', '1122334455', '销售管理员');

select * from Employee;


-- select * from Factory;