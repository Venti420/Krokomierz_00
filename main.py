import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

if os.environ["FLASK_ENV"] == "production":
    app.secret_key = os.environ["SECRET_KEY"]
    DB_USERNAME = os.environ["DB_USERNAME"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    HOSTNAME = f"{DB_USERNAME}.mysql.pythonanywhere-services.com"
    DATABASE = f"{DB_USERNAME}$czujnik"
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{HOSTNAME}/{DATABASE}"
else:
    app.secret_key = 'development'
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    address = db.Column(db.String(255))
    telephone = db.Column(db.String(9))
    PESEL = db.Column(db.String(11))
    # implant_id = db.Column(db.Integer) # ?

    implant_id = db.relationship("Implant", backref="User", lazy=False)

class Implant(db.Model):
    __tablename__ = "implants"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(255), default="pedometer")
    placement_date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    measurements = db.relationship("Measurement", backref="Implant", lazy=False)

class Measurement(db.Model):
    __tablename__ = "measurements"
    number = db.Column(db.Integer, primary_key=True) # czy to sie nie powinno nazywać id? :/
    time = db.Column(db.DateTime)
    steps = db.Column(db.Integer)

    implant_id = db.Column(db.Integer, db.ForeignKey("implants.id"), nullable=False)

with app.app_context():
    db.create_all()

class UsersSchema(ma.Schema):
     class Meta:
        fields = ("id" ,"full_name", "created_at", "address", "telephone", "PESEL")

class ImplantsSchema(ma.Schema):
    class Meta:
        fields = ("id", "type", "placement_date", "user_id")

class MeasurementsSchema(ma.Schema):
    class Meta:
        fields = ("number", "time", "steps", "implant_id")


user_schema = UsersSchema()
users_schema = UsersSchema(many=True)
implant_schema = ImplantsSchema()
implants_schema = ImplantsSchema(many=True)
measurement_schema = MeasurementsSchema()
measurements_schema = MeasurementsSchema(many=True)

@app.route("/")
def main():
    return ":)", 200

@app.route("/user/add", methods=["POST"])
def add_user():
    try:
        if request.json:
            user = User(
                full_name = request.json.get("full_name"),
                created_at = datetime.now(),
                address = request.json.get("address"),
                telephone = request.json.get("telephone"),
                PESEL = request.json.get("PESEL")
            )
            db.session.add(user)
            db.session.commit()
            return jsonify(user_schema.dump(user))
    except KeyError:
        pass
    return jsonify({"error": "malformed or missing data"}), 404

@app.route("/user/<int:id>", methods=["GET"])
def get_user(id):
    if (user := User.query.filter_by(id=id).first()):
        return jsonify(user_schema.dump(user))
    return jsonify({"error": "user not found"}), 404

@app.route("/implant/add", methods=["POST"])
def add_implant():
    try:
        if request.json:
            implant = Implant(
                type = request.json.get("type") or None,
                placement_date = datetime.fromtimestamp(request.json.get("placement_date")),
                user_id = request.json.get("user_id"),
            )
            db.session.add(implant)
            db.session.commit()
            return jsonify(implant_schema.dump(implant))
    except KeyError:
        pass
    return jsonify({"error": "malformed or missing data"}), 404

@app.route("/implant/<int:id>", methods=["GET"])
def get_implant(id):
    if (implant := Implant.query.filter_by(id=id).first()):
        return jsonify(implant_schema.dump(implant))
    return jsonify({"error": "implant not found"}), 404

@app.route("/measurement/add", methods=["POST"])
def add_measurement():
    try:
        if request.json:
            measurement = Measurement(
                time = datetime.fromtimestamp(request.json.get("time")),
                steps = request.json.get("steps"),
                implant_id = request.json.get("implant_id")
            )
            db.session.add(measurement)
            db.session.commit()
            return jsonify(measurement_schema.dump(measurement))
    except KeyError:
        pass
    return jsonify({"error": "malformed or missing data"}), 404

@app.route("/measurement/<int:number>", methods=["GET"])
def get_measurement(number):
    if (implant := Measurement.query.filter_by(number=number).first()):
        return jsonify(measurement_schema.dump(implant))
    return jsonify({"error": "measurement not found"}), 404


@app.route("/web/users")
def list_users():
    users = User.query.all()
    return render_template("users.jinja", users=users_schema.dump(users))

@app.route("/web/implants")
def list_implants():
    implants = Implant.query.all()
    return render_template("implants.jinja", implants=implants_schema.dump(implants))

@app.route("/web/measurements")
def list_measurements():
    measurements = Measurement.query.all()
    return render_template("measurements.jinja", measurements=measurements_schema.dump(measurements))

if __name__ == "__main__":
    app.run(host=os.environ["HOSTNAME"], port=os.environ["PORT"])