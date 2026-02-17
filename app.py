from flask import Flask, render_template, request, redirect, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Station
import csv
from collections import Counter

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ev.db"

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

@app.before_first_request
def create():
    db.create_all()

# ---------- AUTH ----------

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db.session.add(User(
            username=request.form["username"],
            password=request.form["password"]
        ))
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if u:
            login_user(u)
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------- DASHBOARD ----------

@app.route("/")
@login_required
def dashboard():
    stations = Station.query.all()
    total = len(stations)
    avg_price = round(sum(s.price for s in stations)/total,2) if total else 0
    types = Counter(s.charger_type for s in stations)

    return render_template(
        "dashboard.html",
        total=total,
        avg_price=avg_price,
        types=dict(types)
    )

# ---------- ADD STATION ----------

@app.route("/add", methods=["GET","POST"])
@login_required
def add_station():
    if request.method == "POST":
        db.session.add(Station(
            name=request.form["name"],
            city=request.form["city"],
            charger_type=request.form["charger"],
            slots=int(request.form["slots"]),
            price=float(request.form["price"]),
            lat=float(request.form["lat"]),
            lng=float(request.form["lng"])
        ))
        db.session.commit()
        return redirect("/map")
    return render_template("add_station.html")

# ---------- MAP VIEW ----------

@app.route("/map")
@login_required
def map_view():
    stations = Station.query.all()
    return render_template("map.html", stations=stations)

# ---------- CSV EXPORT ----------

@app.route("/export")
@login_required
def export():
    rows = Station.query.all()
    def gen():
        yield "name,city,type,slots,price,lat,lng\n"
        for s in rows:
            yield f"{s.name},{s.city},{s.charger_type},{s.slots},{s.price},{s.lat},{s.lng}\n"

    return Response(gen(), headers={"Content-Disposition":"attachment; filename=stations.csv"})
    

app.run(debug=True)
