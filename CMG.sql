USE CMG;

drop table if exists Inventory_Info;
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
    total_inventory INT DEFAULT 500,
    used_inventory INT DEFAULT 0,
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
    factory_id INT NOT NULL,
    FOREIGN KEY (factory_id) REFERENCES Factory(id) ON DELETE CASCADE
);

-- 创建库存信息表 (InventoryInfo)
CREATE TABLE if not exists Inventory_Info (
    warehouse_id INT,
    car_id INT,
    car_quantity INT,
    primary key (warehouse_id, car_id),
    foreign key (warehouse_id) references Warehouse(id),
    foreign key (car_id) references Car(id)
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


-- 触发器
-- 在创建订单前检查库存是否充足。如果库存不足，则阻止插入
DELIMITER //
CREATE TRIGGER before_order_insert
BEFORE INSERT ON Orders
FOR EACH ROW
BEGIN
    DECLARE available_quantity INT;

    -- 获取库存数量
    SELECT car_quantity INTO available_quantity
    FROM Inventory_Info
    WHERE car_id = NEW.car_id;

    -- 如果库存不足，抛出错误
    IF available_quantity < NEW.quantity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient inventory for the requested car.';
    END IF;
END;
//
DELIMITER ;

-- 触发器
--更新仓库库存
--当一个订单插入到 Orders 表时，触发器会减少 Warehouse 中对应汽车的库存，并更新 used_inventory 的值
DELIMITER $$

CREATE TRIGGER after_order_insert
AFTER INSERT ON Orders
FOR EACH ROW
BEGIN
    DECLARE v_car_quantity INT;
    DECLARE v_warehouse_id INT;

    -- 查找第一个拥有足够库存的仓库
    SELECT warehouse_id, car_quantity INTO v_warehouse_id, v_car_quantity
    FROM Inventory_Info
    WHERE car_id = NEW.car_id AND car_quantity >= NEW.quantity
    ORDER BY car_quantity DESC
    LIMIT 1
    FOR UPDATE;

    IF v_warehouse_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '没有仓库有足够的库存来完成订单。';
    ELSE
        -- 更新 Inventory_Info 表，减少车辆数量
        UPDATE Inventory_Info
        SET car_quantity = car_quantity - NEW.quantity
        WHERE warehouse_id = v_warehouse_id AND car_id = NEW.car_id;

        -- 更新 Warehouse 表，添加 used_inventory 
        UPDATE Warehouse
        SET used_inventory = used_inventory - NEW.quantity
        WHERE id = v_warehouse_id;
    END IF;
END$$

DELIMITER ;

-- 触发器
-- 检查 used_inventory 是否超出 total_inventory。
DELIMITER //
CREATE TRIGGER check_used_inventory
BEFORE UPDATE ON Warehouse
FOR EACH ROW
BEGIN
    -- 检查更新后的 used_inventory 是否超过 total_inventory
    IF NEW.used_inventory > NEW.total_inventory THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Used inventory cannot exceed total inventory.';
    END IF;
END;
//
DELIMITER ;

-- 添加约束条件

-- 订单数量非负
ALTER TABLE Orders ADD CONSTRAINT chk_quantity_nonnegative CHECK (quantity > 0);
-- 库存数量非负
ALTER TABLE Inventory_Info ADD CONSTRAINT chk_car_quantity_nonnegative CHECK (car_quantity >= 0);


-- 存储过程
-- 增加库存
DELIMITER //
CREATE PROCEDURE IncreaseInventory(
    IN p_car_id INT,
    IN p_warehouse_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE existing_quantity INT;

    -- 查询当前仓库中该汽车的库存数量
    SELECT car_quantity INTO existing_quantity
    FROM Inventory_Info
    WHERE car_id = p_car_id AND warehouse_id = p_warehouse_id
    LIMIT 1;

    -- 如果库存记录存在，则更新库存
    IF existing_quantity IS NOT NULL THEN
        UPDATE Inventory_Info
        SET car_quantity = car_quantity + p_quantity
        WHERE car_id = p_car_id AND warehouse_id = p_warehouse_id;
    ELSE
        -- 如果没有库存记录，插入新的记录
        INSERT INTO Inventory_Info (car_id, warehouse_id, car_quantity)
        VALUES (p_car_id, p_warehouse_id, p_quantity);
    END IF;

    -- 更新仓库的已使用库存
    UPDATE Warehouse
    SET used_inventory = used_inventory + p_quantity
    WHERE id = p_warehouse_id;

END;
//
DELIMITER ;

-- 测试数据插入 (可选)
INSERT INTO Factory (name, address, contact_info)
VALUES ('Toyota', '123 Factory Lane', 'factory1@example.com'), 
       ('Honda', '456 Industrial Blvd', 'factory2@example.com');

INSERT INTO Warehouse (name, total_inventory, used_inventory, manager_id)
VALUES ('Main Warehouse', 200, 100, 1), ('Secondary Warehouse', 100, 0, 2);

INSERT INTO Car (model, price, factory_id)
VALUES ('Toyota Corolla', 20000.00, 1),
       ('Honda Civic', 22000.00, 2),
       ('Ford Focus', 18000.00, 1);

INSERT INTO Customer (name, phone, address)
VALUES ('Alice', '1234567890', '123 Main St'), 
       ('Bob', '0987654321', '456 Elm St');

INSERT INTO Orders (customer_id, car_id, quantity)
VALUES (1, 1, 1);

INSERT INTO Employee (employee_id, password, name, contact, employee_type)
VALUES
    ('admin', 'admin123', '张三', '1234567890', '管理员'),
    ('warehouse01', 'warehouse123', '李四', '0987654321', '仓库管理员'),
    ('sales01', 'sales123', '王五', '1122334455', '销售管理员');

INSERT INTO Inventory_Info (warehouse_id, car_id, car_quantity)
VALUES
    (1, 1, 100);

select * from Employee;
select * from Inventory_Info;

-- select * from Factory;