from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from marshmallow import Schema, fields, ValidationError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db = SQLAlchemy(app)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    pizza = db.relationship('Pizza', secondary='pizza_restaurant', back_populates='restaurants')

class Pizza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    ingredients = db.Column(db.String(120), nullable=False)
    restaurants = db.relationship('Restaurant', secondary='pizza_restaurant', back_populates='pizza')

class PizzaRestaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizza.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    pizza = db.relationship('Pizza', backref='restaurants')
    restaurant = db.relationship('Restaurant', backref='pizza')

class PizzaSchema(Schema):
    price = fields.Float(required=True, validate=lambda price: 1 <= price <= 100)
    pizza_id = fields.Integer(required=True)
    restaurant_id = fields.Integer(required=True)


@app.route('/restuarants', methods = ['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    result = [{'id': restaurant.id, 'name': restaurant.name, 'location': restaurant.location} for restaurant in restaurants]
    return jsonify(result)

@app.route('/restuarants/<int:id>', methods = ['GET'])
def get_restaurant(id):
    try:
        restaurant = Restaurant.query.filter_by(id=id).one()
        return jsonify({'id': restaurant.id, 'name': restaurant.name, 'location': restaurant.location})
    except NoResultFound:
        return jsonify({'message': 'restaurant not found'}), 404
    
@app.route('/restuarants', methods = ['POST'])
def create_restaurant():
    try:
        data = request.get_json()
        schema = PizzaSchema()
        schema.load(data)
        pizza = Pizza.query.get(data['pizza_id'])
        restaurant = Restaurant.query.get(data['restaurant_id'])
        if pizza and restaurant:
            restaurant_pizza = PizzaRestaurant(price=data['price'], pizza=pizza, restaurant=restaurant)
            db.session.add(restaurant_pizza)
            db.session.commit()
            return jsonify({'id': pizza.id, 'name': pizza.name, 'ingredients': pizza.ingredients})
        else:
            return jsonify({'error': 'Pizza or Restaurant not found'}), 404
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except IntegrityError:
        return jsonify({'errors': ['RestaurantPizza with the same Pizza and Restaurant already exists']}), 400
    
@app.route('/restuarants/<int:id>', methods = ['DELETE'])
def delete_restaurant(id):
    try:
        restaurant = Restaurant.query.filter_by(id=id).one()
        db.session.delete(restaurant)
        db.session.commit()
        return jsonify({'message': 'restaurant deleted'}), 204
    except NoResultFound:
        return jsonify({'message': 'restaurant not found'}), 404
    
@app.route('/restuarants/<int:id>', methods = ['PUT'])
def get_pizzas():
    pizzas = Pizza.query.all()
    result = [{'id': pizza.id, 'name': pizza.name, 'ingredients': pizza.ingredients} for pizza in pizzas]
    return jsonify(result)

if '__name__' == '__main__':
    db.create_all()
    app.run(debug=True)