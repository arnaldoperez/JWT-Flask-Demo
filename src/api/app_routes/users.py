from datetime import date, time, datetime, timezone, timedelta
from api.models import db, User, TokenBlockedList
from flask_jwt_extended import create_access_token, create_refresh_token,get_jti, jwt_required, get_jwt_identity, get_jwt
from api.utils import generate_sitemap, APIException
from flask_bcrypt import Bcrypt
from flask import Flask, Blueprint, request, jsonify
from firebase_admin import storage
import tempfile


app=Flask(__name__)
bcrypt=Bcrypt(app)

apiUser = Blueprint('apiUser', __name__)

@apiUser.route("/helloUser",methods=["GET"])
def helloUser():
    
    return "Hello User", 200

@apiUser.route('/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(email=email).first()
    
    # Verificamos el nombre de usuario
    if user is None:
        return jsonify({"message":"Login failed"}), 401
    
    # Validar clave
    
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message":"Wrong password"}), 401
    
    access_token = create_access_token(identity=user.id,additional_claims={"role":"admin"})
    access_token_jti=get_jti(access_token)
    refresh_token=create_refresh_token(identity=user.id, additional_claims={"accessToken":access_token_jti,"role":"admin"})
    return jsonify({"token":access_token, "refreshToken":refresh_token})

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

@apiUser.route('/refresh',methods=['POST'])
@jwt_required(refresh=True)
def refreshToken():
    claims=get_jwt()
    refreshToken = claims["jti"]
    accessToken = claims["accessToken"]
    role=claims['role']
    now = datetime.now(timezone.utc)
    id=get_jwt_identity()
    accessTokenBlocked = TokenBlockedList(token=accessToken, created_at=now, email=get_jwt_identity())
    refreshTokenBlocked = TokenBlockedList(token=refreshToken, created_at=now, email=get_jwt_identity())
    db.session.add(accessTokenBlocked)
    db.session.add(refreshTokenBlocked)
    db.session.commit()
    access_token = create_access_token(identity=id,additional_claims={"role":role})
    access_token_jti=get_jti(access_token)
    refresh_token=create_refresh_token(identity=id, additional_claims={"accessToken":access_token_jti, "role":role})
    return jsonify({"token":access_token, "refreshToken":refresh_token})




@apiUser.route('/uploadPhoto', methods=['POST'])
@jwt_required()
def uploadPhoto():
    # Se recibe un archivo en la peticion
    file=request.files['profilePic']
    # Extraemos la extension del archivo
    extension=file.filename.split(".")[1]
    # Se genera el nombre de archivo con el id de la imagen y la extension
    filename="profiles/" + str(get_jwt_identity()) + "." + extension
    # Guardar el archivo recibido en un archivo temporal
    temp = tempfile.NamedTemporaryFile(delete=False)
    file.save(temp.name)
    # Subir el archivo a firebase
    ## Se llama al bucket
    bucket=storage.bucket(name="testflask-680bf.appspot.com")
    ## Se hace referencia al espacio dentro del bucket
    blob = bucket.blob(filename)
    ## Se sube el archivo temporal al espacio designado en el bucket
    # Se debe especificar el tipo de contenido en base a la extension
    blob.upload_from_filename(temp.name,content_type="image/"+extension)
    
    #Buscamos el usuario en la BD partiendo del id del token
    user = User.query.get(get_jwt_identity())
    if user is None:
        return "Usuario no encontrado", 403
    # Actualizar el campo de la foto
    user.picture=filename
    # Se crear el registro en la base de datos 
    db.session.add(user)
    db.session.commit()
    
    return "Ok", 200


@apiUser.route('/helloprotected', methods=['GET'])
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

    return jsonify(user.serialize()), 200


@apiUser.route('/getPhoto', methods=['GET'])
@jwt_required()
def getPhoto():
    #Buscamos el usuario en la BD partiendo del id del token
    user = User.query.get(get_jwt_identity())
    if user is None:
        return "Usuario no encontrado", 403
   
    # Subir el archivo a firebase
    ## Se llama al bucket
    bucket=storage.bucket(name="testflask-680bf.appspot.com")
    ## Se hace referencia al espacio dentro del bucket
    blob = bucket.blob(user.picture)
    ## Se sube el archivo temporal al espacio designado en el bucket
    url=blob.generate_signed_url(version="v4",
        # This URL is valid for 15 minutes
        expiration=timedelta(minutes=15),
        # Allow GET requests using this URL.
        method="GET")
        
    return jsonify({"pictureUrl":url}), 200


@apiUser.route('/logout', methods=['POST'])
@jwt_required()
def destroyToken():
    jwt = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    tokenBlocked = TokenBlockedList(token=jwt, created_at=now, email=get_jwt_identity())
    db.session.add(tokenBlocked)
    db.session.commit()

    return jsonify(msg="Acceso revocado")
