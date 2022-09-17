from datetime import date, time, datetime, timezone
from api.models import db, User, TokenBlockedList
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from api.utils import generate_sitemap, APIException
from flask_bcrypt import Bcrypt
from flask import Flask, Blueprint, request, jsonify
#from ..routes import bcrypt

app=Flask(__name__)
bcrypt=Bcrypt(app)

apiUser = Blueprint('apiUser', __name__)

@apiUser.route("/helloUser",methods=["GET"])
def helloUser():
    print("HelloUser")
    return "Hello User", 200

@apiUser.route('/login', methods=['POST'])
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

@apiUser.route('/signup', methods=['POST'])
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

@apiUser.route('/logout', methods=['POST'])
@jwt_required()
def destroyToken():
    jwt = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    tokenBlocked = TokenBlockedList(token=jwt, created_at=now, email=get_jwt_identity())
    db.session.add(tokenBlocked)
    db.session.commit()

    return jsonify(msg="Acceso revocado")
