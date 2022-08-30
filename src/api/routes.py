"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User, TokenBlockedList
from api.utils import generate_sitemap, APIException
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt
from datetime import date, time, datetime, timezone

api = Blueprint('api', __name__)

app=Flask(__name__)
bcrypt=Bcrypt(app)



@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200

@api.route('/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(email=email).first()
    print(password)
    # Verificamos el nombre de usuario
    if user is None:
        return jsonify({"message":"Login failed"}), 401
    
    # Validar clave
    print(user.password)
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message":"Wrong password"}), 401
    
    access_token = create_access_token(identity=user.id,additional_claims={"role":"admin"})
    return jsonify({"token":access_token})

@api.route('/signup', methods=['POST'])
def signup():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    try:
        password=bcrypt.generate_password_hash(password,10).decode("utf-8")
        user = User(email=email, password=password, is_active=True)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message":"Usuario registrado"}), 201
    except Exception as err:
        db.session.rollback()
        print(err)
        return jsonify({"message":"internal error"}), 500

@api.route('/helloprotected', methods=['GET'])
@jwt_required()
def handle_hello_protected():
    claims=get_jwt()
    user = User.query.get(get_jwt_identity())
    response_body = {
        "message": "token válido",
        "user_id": get_jwt_identity(),
        "role":claims["role"],
        "user_email": user.email
    }
    TokenBlocked = TokenBlockedList.query.filter_by(token=get_jwt()['jti']).first()
    if isinstance(TokenBlocked, TokenBlockedList):
        return jsonify(msg="Acceso revocado")

    return jsonify(user.serialize()), 200

@api.route('/logout', methods=['POST'])
@jwt_required()
def destroyToken():
    jwt = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    tokenBlocked = TokenBlockedList(token=jwt, created_at=now, email=get_jwt_identity())
    db.session.add(tokenBlocked)
    db.session.commit()

    return jsonify(msg="Acceso revocado")

