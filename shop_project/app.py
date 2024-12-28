import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Папка для загрузки изображений
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Статичные пользователи
users = {
    'admin': {'password': generate_password_hash('admin_pass'), 'role': 'admin'},
}

# Класс UserMixin для интеграции с Flask-Login
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.role = users[username]['role']

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# Статичные товары для отображения
products = [
    {'id': 1, 'name': 'Товар 1', 'price': 1000, 'image': 'product1.jpg'},
    {'id': 2, 'name': 'Товар 2', 'price': 2000, 'image': 'product2.jpg'},
]

# Главная страница (выбор пользователя или администратора)
@app.route('/')
def home():
    return render_template('index.html')

# Страница регистрации (только для админа)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash('User already exists', 'danger')
        else:
            users[username] = {'password': generate_password_hash(password), 'role': 'admin'}
            flash('Registration successful', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Страница входа (только для админа)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username]['password'], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('admin_panel'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Страница магазина для обычных пользователей (без регистрации)
@app.route('/shop')
def shop():
    return render_template('shop.html', products=products)

# Добавление товара в корзину
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        cart = session.get('cart', [])
        cart.append(product)
        session['cart'] = cart
        flash(f'{product["name"]} добавлен в корзину', 'success')
    return redirect(url_for('shop'))

# Отображение корзины
@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    return render_template('cart.html', cart=cart)

# Панель администратора (только для админа)
@app.route('/admin_panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return redirect(url_for('shop'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']
        if image:
            filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product_id = len(products) + 1
            products.append({'id': product_id, 'name': name, 'price': price, 'image': filename})
            flash(f"Product {name} added successfully", 'success')
    
    return render_template('admin_panel.html', products=products)

# Удаление товара (только для админа)
@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        return redirect(url_for('shop'))
    
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        products.remove(product)
        flash(f'Продукт {product["name"]} удален', 'success')
    return redirect(url_for('admin_panel'))

# Выход из аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

