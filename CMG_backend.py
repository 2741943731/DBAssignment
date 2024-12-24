from flask import Flask, session, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pymysql

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/CMG'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)


class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_inventory = db.Column(db.Integer, default=0)
    used_inventory = db.Column(db.Integer, default=0)
    manager_id = db.Column(db.Integer, nullable=False)


class InventoryInfo(db.Model):
    warehouse_id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, primary_key=True)
    car_quantity = db.Column(db.Integer, nullable=False)


class Factory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    contact_info = db.Column(db.String(100), nullable=True)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    factory_id = db.Column(db.Integer, db.ForeignKey('factory.id'), nullable=False)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class Employee(db.Model):
    employee_id = db.Column(db.String(20), primary_key=True, nullable=False, comment='员工登录账号')
    password = db.Column(db.String(50), nullable=False, comment='员工密码，简单明文存储')
    name = db.Column(db.String(100), nullable=False, comment='员工姓名')
    contact = db.Column(db.String(50), nullable=True, comment='员工联系方式')
    employee_type = db.Column(db.Enum('管理员', '仓库管理员', '销售管理员'), nullable=False, comment='员工类型')


@app.route('/')
def home():
    return render_template('home.html', title="主页")


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    # 假设通过数据库验证用户
    user = Employee.query.filter_by(employee_id=username, password=password).first()
    if user:
        session['logged_in'] = True
        session['user_role'] = user.employee_type
        return jsonify({'success': True, 'role': user.employee_type})
    else:
        return jsonify({'success': False, 'message': '账号或密码错误'})


# @app.route('/home')
# def home():
#     if 'logged_in' not in session:
#         return redirect(url_for('login'))
#     return render_template('home.html', user_role=session.get('user_role'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # 清除会话
    return jsonify({'success': True})  # 返回成功信息


# 仓库相关路由
@app.route('/warehouses', methods=['GET'])
def get_warehouses_page():
    # 获取所有的仓库和车辆信息
    warehouses = Warehouse.query.all()
    cars = Car.query.all()
    inventoryinfos = InventoryInfo.query.all()

    # 创建一个字典，快速查找仓库和车辆的名称
    warehouse_dict = {warehouse.id: warehouse.name for warehouse in warehouses}
    car_dict = {car.id: car.model for car in cars}

    # 渲染模板并传递这些数据
    return render_template(
        'warehouses.html',
        warehouses=warehouses,
        inventoryinfos=inventoryinfos,
        warehouse_dict=warehouse_dict,
        car_dict=car_dict,
        cars=cars
    )


# 厂商相关路由
@app.route('/factories', methods=['GET'])
def get_factories_page():
    factories = Factory.query.all()
    return render_template('factories.html', factories=factories)


@app.route('/factories', methods=['GET', 'POST'])
def manage_factories():
    if request.method == 'POST':
        # 获取表单数据
        name = request.form['name']
        address = request.form.get('address', '')
        contact_info = request.form.get('contact_info', '')

        # 保存到数据库
        new_factory = Factory(name=name, address=address, contact_info=contact_info)
        db.session.add(new_factory)
        db.session.commit()

        # 提交后重定向到当前页面，避免重复提交
        return redirect(url_for('manage_factories'))
    else:
        # GET 请求时返回页面
        factories = Factory.query.all()
        return render_template('factories.html', factories=factories)


# 添加库存
@app.route('/add_inventory', methods=['POST'])
def add_inventory():
    warehouse_id = request.form['warehouse_id']
    car_id = request.form['car_id']
    add_quantity = int(request.form['quantity'])

    # 获取对应的仓库和车辆
    warehouse = Warehouse.query.get(warehouse_id)
    inventory_info = InventoryInfo.query.filter_by(warehouse_id=warehouse_id, car_id=car_id).first()

    # 检查是否存在该车辆的库存记录
    if inventory_info is None:
        inventory_info = InventoryInfo(warehouse_id=warehouse_id, car_id=car_id, car_quantity=0)
        db.session.add(inventory_info)

    # 计算可用的库存空间
    remaining_inventory = warehouse.total_inventory - warehouse.used_inventory

    # 检查是否能添加该数量的库存
    if remaining_inventory >= add_quantity:
        # 更新库存信息
        inventory_info.car_quantity += add_quantity
        warehouse.used_inventory += add_quantity

        db.session.commit()
        flash('库存已成功添加！', 'success')
    else:
        flash('库存添加失败：仓库剩余空间不足！', 'error')

    return redirect(url_for('get_warehouses_page'))

# 减少库存
@app.route('/remove_inventory', methods=['POST'])
def remove_inventory():
    warehouse_id = request.form['warehouse_id']
    car_id = request.form['car_id']
    remove_quantity = int(request.form['quantity'])

    # 获取对应的仓库和车辆
    warehouse = Warehouse.query.get(warehouse_id)
    inventory_info = InventoryInfo.query.filter_by(warehouse_id=warehouse_id, car_id=car_id).first()

    if inventory_info is None:
        flash('该库存信息不存在！', 'error')
        return redirect(url_for('get_warehouses_page'))

    # 检查库存数量是否足够
    if inventory_info.car_quantity >= remove_quantity:
        # 更新库存信息
        inventory_info.car_quantity -= remove_quantity
        warehouse.used_inventory -= remove_quantity

        db.session.commit()
        flash('库存已成功减少！', 'success')
    else:
        flash('库存减少失败：库存不足！', 'error')

    return redirect(url_for('get_warehouses_page'))



@app.route('/factories/<int:factory_id>/delete', methods=['POST'])
def delete_factory(factory_id):
    factory = Factory.query.get_or_404(factory_id)
    db.session.delete(factory)
    db.session.commit()
    return redirect(url_for('manage_factories'))


@app.route('/factories/<int:factory_id>/cars', methods=['GET'])
def get_cars_by_factory(factory_id):
    cars = Car.query.filter_by(factory_id=factory_id).all()
    return jsonify([{'id': c.id, 'model': c.model, 'price': c.price, 'warehouse_id': c.warehouse_id} for c in cars])


# 汽车相关路由
@app.route('/cars', methods=['GET', 'POST'])
def manage_cars():
    if request.method == 'POST':
        # 获取表单数据
        model = request.form['model']
        price = request.form['price']
        factory_id = request.form['factory_id']

        # 保存到数据库
        new_car = Car(model=model, price=price, factory_id=factory_id)
        db.session.add(new_car)
        db.session.commit()

        # 提交后重定向到当前页面，避免重复提交
        return redirect(url_for('manage_cars'))
    else:
        # GET 请求时返回页面
        cars = Car.query.all()
        return render_template('car.html', cars=cars)


@app.route('/cars/<int:car_id>/delete', methods=['POST'])
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    db.session.delete(car)
    db.session.commit()
    return redirect(url_for('manage_cars'))


# 客户相关路由
@app.route('/customers', methods=['GET', 'POST'])
def manage_customers():
    if request.method == 'POST':
        # 获取表单数据
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']

        # 保存到数据库
        new_customer = Customer(name=name, phone=phone, address=address)
        db.session.add(new_customer)
        db.session.commit()

        # 提交后重定向到当前页面，避免重复提交
        return redirect(url_for('manage_customers'))
    else:
        # GET 请求时返回页面
        customers = Customer.query.all()
        return render_template('customer.html', customers=customers)


@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        # 获取表单数据
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.address = request.form['address']

        # 保存修改
        db.session.commit()

        # 提交后重定向到客户管理页面
        return redirect(url_for('manage_customers'))

    return render_template('edit_customer.html', customer=customer)


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('manage_customers'))


# 订单相关路由
@app.route('/orders', methods=['GET', 'POST'])
def manage_orders():
    if request.method == 'POST':
        # 获取表单数据
        customer_id = request.form['customer_id']
        car_id = request.form['car_id']
        quantity = request.form['quantity']

        # 保存到数据库
        new_order = Orders(customer_id=customer_id, car_id=car_id, quantity=quantity)
        db.session.add(new_order)
        db.session.commit()

        # 提交后重定向到当前页面，避免重复提交
        return redirect(url_for('manage_orders'))
    else:
        # GET 请求时返回页面
        orders = Orders.query.all()
        return render_template('orders.html', orders=orders)


@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    order = Orders.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('manage_orders'))


# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, port=3389)
