'''

from flask import Flask 
# Flask is a web-server application | essentially just a 
# python class w/ a bunch of methods & attributes that are essential to web-server communication

from flask_sqlalchemy import SQLAlchemy 
# SQLAlchemy is a ORM (Obj relational mapper) that makes interacting w/ 
# databases using python instead of raw SQL possible
# Note: **flask has built-in tools to interact w/ dbs**

app = Flask(__name__) # Flask web-app obj

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
db = SQLAlchemy(app)
# lines 12-13 tells flask & db tool to CRUD data from a 
# sqlite db named 'database.db'

'''


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)

class UserModel(db.Model): #each row in new db is a UserModel obj w/ repective attributes
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self): #repr method to display suitable info
        return f'User(name = {self.name}, email = {self.email})'
    
user_args = reqparse.RequestParser()
user_args.add_argument('name', type=str, required=True, help='Name can not be blank')
user_args.add_argument('email', type=str, required=True, help='Email can not be blank')


userFields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,

}

class Users(Resource):
    @marshal_with(userFields)
    def get(self):
        users = UserModel.query.all()
        return users
    
    @marshal_with(userFields)
    def post(self):
        args = user_args.parse_args()
        user = UserModel(name=args['name'], email=args['email'])
        db.session.add(user)
        db.session.commit()

        users = UserModel.query.all()
        return users, 201
    
class User(Resource):
    @marshal_with(userFields)
    def get(self, id):
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, 'User not found.')
        return user
    
    @marshal_with(userFields)
    def patch(self, id):
        args = user_args.parse_args()
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, 'User not found.')
        user.name = args['name']
        user.email = args['email']
        db.session.commit()
        return user
    
    @marshal_with(userFields)
    def delete(self, id):
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, 'User not found.')
        db.session.delete(user)
        db.session.commit()

        users = UserModel.query.all()
        return users

api.add_resource(User, '/api/users/<int:id>')
api.add_resource(Users, '/api/users/')

@app.route('/') #establishes the path to the homepage (aka. 'root') website directory | since route = '/'
def home():
    return 'homepage'

#run script
if __name__ == '__main__':
    app.run(debug=True)