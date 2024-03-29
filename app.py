import json

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from passlib.context import CryptContext
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_cors import CORS
import datetime
from prediction_model import Stock_performance


app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisisasecretkey'
app.permanent_session_lifetime = datetime.timedelta(minutes=30)
CORS(app)  # Initialize CORS with default settings|


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database initialization

db_user = 'zero'
db_password = 'zero'
db_host = 'localhost'
db_port = '3306'
db_name = 'Stocks'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)



    def __repr__(self):
        return f'<User : {self.email} >'
class Forecasts(db.Model):
    status_id = db.Column(db.Integer, primary_key=True)
    stock_data = db.Column(db.Text(2000000), nullable=False)





# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Utility functions
def hash_password(password):
    return pwd_context.hash(password)


# Database Initialization
def create_db_and_tables():
    with app.app_context():
        db.create_all()
        print("Tables created successfully!")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    print("Unauthorized User")
    return render_template('401.html'), 401

@app.route('/')
@login_required
def main_page():

    return render_template("main_page.html")



# User Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    email = data.get('email')
    name = data.get('name')
    surname = data.get('surname')
    password = data.get('password')
    full_name = name + " " + surname


    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({"message": "Email already registered"})

    hashed_password = hash_password(password)
    new_user = User( email=email, hashed_password=hashed_password, full_name=full_name)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User successfully registered"}), 201

# User Login Endpoint
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not pwd_context.verify(password, user.hashed_password):
            return jsonify({"message": "Invalid email or password"}), 401
        login_user(user)
        session.permanent = True
        return redirect(url_for('main_page')), 200
    return "Not allowed method", 404


# Token refresh endpoint
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))



@app.route('/get-forecast')
def get_forecast():

    response = {}

    length = Forecasts.query.count()


    for index in range(1, length+1):

        item = Forecasts.query.filter_by(status_id=index).first()

        response[index] = item.stock_data

    response["length"] = Forecasts.query.count()
    json_response = json.dumps(response, indent=2)

    return json_response

@app.route('/get-train')
@login_required
def get_train():

    user = current_user

    if (user.is_admin):

        print("Admin User Start")

        stock = Stock_performance()
        stock.get_data()
        stock.feed_model()
        forecasts = stock.plot_model()
        data = json.loads(forecasts)
        length = int(data['length'])
        try:
            db.session.query(Forecasts).delete()
            db.session.commit()

            for index in range(1, length+1):

                json_data = json.dumps(data[f"{index}"])

                stocks = Forecasts(status_id=index, stock_data=json_data)
                db.session.add(stocks)
            db.session.commit()

            return jsonify({"message": "success"})
        except Exception as e:
            return jsonify({"message": e})
    else:
        return 401



with app.app_context():
    create_db_and_tables()





if __name__ == '__main__':
    app.run(debug=True, port=5000)










