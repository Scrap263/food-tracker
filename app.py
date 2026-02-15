from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-this-in-production' # Required for sessions

# DB Config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'food_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, default=0.0)
    # Optional: created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbs': self.carbs,
            'fiber': self.fiber
        }

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Link to User
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    weight_g = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    dish = db.relationship('Dish', backref='meals')
    user = db.relationship('User', backref='meals')

    def to_dict(self):
        return {
            'id': self.id,
            'dish': self.dish.to_dict(),
            'weight_g': self.weight_g,
            'timestamp': self.timestamp.isoformat()
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Такой пользователь уже существует')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main Routes ---
@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/api/dishes', methods=['GET', 'POST'])
@login_required
def handle_dishes():
    if request.method == 'POST':
        data = request.json
        new_dish = Dish(
            name=data['name'],
            calories=float(data['calories']),
            protein=float(data['protein']),
            fat=float(data['fat']),
            carbs=float(data['carbs']),
            fiber=float(data.get('fiber', 0))
        )
        db.session.add(new_dish)
        db.session.commit()
        return jsonify(new_dish.to_dict()), 201
    
    query = request.args.get('q', '')
    if query:
        dishes = Dish.query.filter(Dish.name.ilike(f'%{query}%')).all()
    else:
        dishes = Dish.query.all()
    return jsonify([d.to_dict() for d in dishes])

@app.route('/api/meals', methods=['POST'])
@login_required
def add_meal():
    data = request.json
    dish_id = data.get('dish_id')
    weight = float(data.get('weight_g'))
    
    target_date_str = data.get('date')
    if target_date_str:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        meal_time = datetime.combine(target_date, datetime.now().time())
    else:
        meal_time = datetime.now()

    # Link meal to current_user
    new_meal = Meal(
        user_id=current_user.id,
        dish_id=dish_id, 
        weight_g=weight, 
        timestamp=meal_time
    )
    db.session.add(new_meal)
    db.session.commit()
    return jsonify(new_meal.to_dict()), 201

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    date_str = request.args.get('date', date.today().isoformat())
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Filter meals by date AND current_user
    meals = Meal.query.filter(
        db.func.date(Meal.timestamp) == target_date,
        Meal.user_id == current_user.id
    ).all()
    
    stats = {
        'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0, 'fiber': 0
    }
    
    meal_list = []
    for m in meals:
        ratio = m.weight_g / 100.0
        stats['calories'] += m.dish.calories * ratio
        stats['protein'] += m.dish.protein * ratio
        stats['fat'] += m.dish.fat * ratio
        stats['carbs'] += m.dish.carbs * ratio
        stats['fiber'] += m.dish.fiber * ratio
        
        meal_list.append({
            'id': m.id,
            'name': m.dish.name,
            'weight': m.weight_g,
            'calories': round(m.dish.calories * ratio, 1),
            'protein': round(m.dish.protein * ratio, 1),
            'fat': round(m.dish.fat * ratio, 1),
            'carbs': round(m.dish.carbs * ratio, 1),
            'fiber': round(m.dish.fiber * ratio, 1)
        })
    
    for k in stats:
        stats[k] = round(stats[k], 1)
        
    return jsonify({
        'date': date_str,
        'totals': stats,
        'meals': meal_list
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
