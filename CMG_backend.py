from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:530336@localhost:3306/CMG'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_inventory = db.Column(db.Integer, default=0)
    manager_id = db.Column(db.Integer, nullable=False)


class Factory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    contact_info = db.Column(db.String(100), nullable=True)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
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

@app.route('/')
def home():
    return render_template('home.html', title="主页")

# 仓库相关路由
@app.route('/warehouses', methods=['GET'])
def get_warehouses_page():
    warehouses = Warehouse.query.all()
    return render_template('warehouses.html', warehouses=warehouses)

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




@app.route('/factories/<int:factory_id>/cars', methods=['GET'])
def get_cars_by_factory(factory_id):
    cars = Car.query.filter_by(factory_id=factory_id).all()
    return jsonify([{'id': c.id, 'model': c.model, 'price': c.price, 'warehouse_id': c.warehouse_id} for c in cars])


# 汽车相关路由
@app.route('/cars', methods=['GET'])
def get_cars():
    cars = Car.query.all()
    return jsonify([{'id': c.id, 'model': c.model, 'price': c.price, 'warehouse_id': c.warehouse_id, 'factory_id': c.factory_id} for c in cars])


@app.route('/cars', methods=['POST'])
def add_car():
    data = request.json
    car = Car(model=data['model'], price=data['price'], warehouse_id=data['warehouse_id'], factory_id=data['factory_id'])
    db.session.add(car)
    db.session.commit()
    return jsonify({'message': 'Car added successfully!'})


# 客户相关路由
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'phone': c.phone, 'address': c.address} for c in customers])


@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.json
    customer = Customer(name=data['name'], phone=data['phone'], address=data['address'])
    db.session.add(customer)
    db.session.commit()
    return jsonify({'message': 'Customer added successfully!'})


# 订单相关路由
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Orders.query.all()
    return jsonify([{'id': o.id, 'customer_id': o.customer_id, 'car_id': o.car_id, 'quantity': o.quantity} for o in orders])


@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    order = Orders(customer_id=data['customer_id'], car_id=data['car_id'], quantity=data['quantity'])
    db.session.add(order)
    db.session.commit()
    return jsonify({'message': 'Order added successfully!'})


# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, port=3389)


