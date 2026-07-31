import hmacimport hashlibimport jsonimport osimport uuidfrom datetime import datetimefrom functools import wrapsfrom dotenv import load_dotenvimport os

Load environment variables from .env

load_dotenv()

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, sessionfrom flask_sqlalchemy import SQLAlchemyfrom werkzeug.utils import secure_filenamefrom sqlalchemy import inspect

from ai.disease_model import predict_leaf_diseasefrom ai.chatbot import generate_chat_response

try:import razorpayexcept Exception:  # razorpay is optional until keys are addedrazorpay = None

BASE_DIR = os.path.abspath(os.path.dirname(file))

app = Flask(name)app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-for-production")app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///plants.db"app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = Falseapp.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

-------------------------

Database Models

-------------------------

class Plant(db.Model):id = db.Column(db.Integer, primary_key=True)name = db.Column(db.String(120), nullable=False)category = db.Column(db.String(80), nullable=False)price = db.Column(db.Integer, nullable=False)stock = db.Column(db.Integer, nullable=False, default=10)sunlight = db.Column(db.String(160), nullable=False)water = db.Column(db.String(160), nullable=False)soil = db.Column(db.String(160), nullable=False)fertilizer = db.Column(db.String(160), nullable=False)benefits = db.Column(db.String(400), nullable=False)description = db.Column(db.String(700), nullable=False)difficulty = db.Column(db.String(40), default="Easy")size = db.Column(db.String(60), default="Medium")image_emoji = db.Column(db.String(20), default="🌿")created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):id = db.Column(db.Integer, primary_key=True)order_no = db.Column(db.String(50), unique=True, nullable=False)customer_name = db.Column(db.String(120), nullable=False)email = db.Column(db.String(120), nullable=False)phone = db.Column(db.String(30), nullable=False)address = db.Column(db.String(500), nullable=False)city = db.Column(db.String(80), nullable=False)pincode = db.Column(db.String(20), nullable=False)items_json = db.Column(db.Text, nullable=False)subtotal = db.Column(db.Integer, nullable=False)delivery_fee = db.Column(db.Integer, nullable=False, default=0)total = db.Column(db.Integer, nullable=False)payment_method = db.Column(db.String(50), nullable=False)payment_status = db.Column(db.String(50), default="Pending")razorpay_order_id = db.Column(db.String(120))razorpay_payment_id = db.Column(db.String(120))created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PlantRequest(db.Model):id = db.Column(db.Integer, primary_key=True)name = db.Column(db.String(120), nullable=False)phone = db.Column(db.String(30), nullable=False)plant_name = db.Column(db.String(120), nullable=False)message = db.Column(db.String(600))created_at = db.Column(db.DateTime, default=datetime.utcnow)

-------------------------

Seed Data

-------------------------

PLANT_DATA = [("Areca Palm", "Indoor", 499, 18, "Bright indirect light", "Water when top soil feels dry", "Well-drained loamy soil", "Liquid fertilizer once a month", "Purifies air and adds a tropical look", "A graceful indoor palm suitable for homes, offices and balconies. It improves visual freshness and is beginner friendly.", "Easy", "Medium", "🌴"),("Money Plant", "Indoor", 199, 35, "Low to bright indirect light", "Water once in 5 to 7 days", "Regular potting mix", "Organic compost monthly", "Popular air-purifying and decorative plant", "Money Plant is one of the easiest indoor plants. It grows well in soil and water and is ideal for desks and living rooms.", "Very Easy", "Small", "🪴"),("Snake Plant", "Indoor", 349, 28, "Low to bright indirect light", "Water once in 10 to 14 days", "Sandy well-draining soil", "Mild fertilizer every 2 months", "Releases oxygen and needs low maintenance", "A strong architectural plant that survives neglect and is perfect for bedrooms and offices.", "Very Easy", "Medium", "🌵"),("Peace Lily", "Flowering", 449, 16, "Medium indirect light", "Keep soil slightly moist", "Rich moist potting soil", "Balanced fertilizer monthly", "Elegant white flowers and air purification", "Peace Lily brings a calm elegant look indoors with glossy leaves and white blooms.", "Medium", "Medium", "🌸"),("Aloe Vera", "Medicinal", 249, 30, "Bright light or morning sun", "Water once in 12 to 15 days", "Cactus or sandy soil", "Very light fertilizer", "Useful gel for skin care and home remedies", "Aloe Vera is a hardy medicinal succulent with thick useful leaves and very low water requirement.", "Very Easy", "Small", "🌱"),("Tulsi Holy Basil", "Medicinal", 99, 42, "4 to 6 hours sunlight", "Water daily in summer", "Fertile garden soil", "Organic compost every month", "Medicinal, spiritual and aromatic value", "Tulsi is a traditional Indian medicinal plant suitable for balconies and terraces.", "Easy", "Small", "🌿"),("Jade Plant", "Succulent", 299, 25, "Bright indirect light", "Water once in 10 days", "Fast-draining succulent mix", "Low nitrogen fertilizer", "Symbol of prosperity and easy decor", "A compact succulent with thick glossy leaves. It is perfect for tabletops and sunny windows.", "Easy", "Small", "🪴"),("Rubber Plant", "Indoor", 599, 14, "Bright indirect light", "Water once a week", "Well-aerated potting mix", "Fertilizer every 4 weeks", "Bold glossy leaves and air purification", "Rubber Plant is a premium indoor foliage plant that gives a stylish modern look to interiors.", "Medium", "Large", "🌳"),("Spider Plant", "Indoor", 299, 22, "Moderate indirect light", "Water weekly", "Loose potting soil", "Fertilizer twice a month in growing season", "Safe-looking hanging plant with air benefits", "Spider Plant produces baby plantlets and looks beautiful in hanging pots.", "Easy", "Small", "🌿"),("ZZ Plant", "Indoor", 549, 19, "Low to medium light", "Water every 2 weeks", "Well-draining soil", "Slow-release fertilizer", "Excellent for low-light rooms", "ZZ Plant is a glossy, premium and drought-tolerant plant suitable for beginners.", "Very Easy", "Medium", "🌱"),("Lucky Bamboo", "Indoor", 249, 40, "Filtered indoor light", "Change water weekly", "Water or pebbles", "Liquid feed once a month", "Feng shui plant for positivity", "Lucky Bamboo is easy to keep in water and makes a neat gift plant.", "Very Easy", "Small", "🎋"),("Monstera Deliciosa", "Indoor", 899, 10, "Bright indirect light", "Water when top inch is dry", "Peat-based airy soil", "Monthly fertilizer", "Premium decor plant with split leaves", "A statement plant known for large split leaves, ideal for stylish interiors.", "Medium", "Large", "🍃"),("Bougainvillea", "Outdoor", 399, 18, "Full sunlight", "Water deeply but less often", "Sandy garden soil", "Low nitrogen fertilizer", "Bright colorful outdoor flowering plant", "Bougainvillea is perfect for gardens, terraces and sunny balconies with vibrant flowers.", "Medium", "Large", "🌺"),("Hibiscus", "Flowering", 349, 20, "Full to partial sun", "Water regularly", "Nutrient-rich garden soil", "Flower booster every month", "Large colorful flowers", "Hibiscus adds bright flowers and is a popular choice for home gardens.", "Medium", "Medium", "🌺"),("Rose Plant", "Flowering", 299, 24, "5 to 6 hours sunlight", "Water daily in hot weather", "Fertile well-drained soil", "Rose fertilizer monthly", "Classic fragrant flowers", "A beautiful flowering plant for garden beds and balcony pots.", "Medium", "Medium", "🌹"),("Marigold", "Flowering", 89, 50, "Full sun", "Water moderately", "Garden soil with compost", "Organic compost", "Bright seasonal flowers and pest control", "Marigold is affordable, colorful and useful for gardens and festive decoration.", "Easy", "Small", "🌼"),("Curry Leaf Plant", "Herb", 199, 32, "Full to partial sunlight", "Water when soil dries", "Fertile garden soil", "Compost monthly", "Fresh leaves for cooking", "A useful kitchen garden plant for Indian homes with aromatic leaves.", "Easy", "Medium", "🌿"),("Mint Plant", "Herb", 79, 45, "Morning sun or partial shade", "Keep soil moist", "Rich moist soil", "Organic compost", "Fresh herb for drinks and cooking", "Mint grows quickly and is perfect for kitchen gardens and balcony planters.", "Easy", "Small", "🌿"),("Lavender", "Herb", 399, 15, "Full sun", "Water when dry", "Sandy alkaline soil", "Light fertilizer", "Aromatic and calming fragrance", "Lavender is a fragrant plant suitable for sunny balconies and outdoor pots.", "Medium", "Small", "💜"),("Cactus Mix", "Succulent", 199, 34, "Bright light", "Water once in 15 to 20 days", "Cactus soil", "Minimal fertilizer", "Low-maintenance decorative plant", "A compact cactus collection for desks and windows. Ideal for low water care.", "Very Easy", "Small", "🌵"),("Calathea", "Indoor", 699, 12, "Medium indirect light", "Keep evenly moist", "Rich airy soil", "Diluted fertilizer monthly", "Attractive patterned leaves", "Calathea has beautiful leaf patterns and gives a premium indoor aesthetic.", "Medium", "Medium", "🍂"),("Fern", "Indoor", 299, 21, "Shade or indirect light", "Keep moist", "Moist organic soil", "Light fertilizer", "Soft lush green foliage", "Fern is ideal for shaded corners and gives a fresh forest-like feel.", "Medium", "Small", "🌿"),("Orchid", "Flowering", 999, 8, "Bright filtered light", "Water weekly", "Orchid bark mix", "Orchid fertilizer", "Premium long-lasting flowers", "Orchid is a premium flowering plant for gifting and elegant indoor decoration.", "Advanced", "Small", "🌷"),("Bonsai Ficus", "Premium", 1299, 7, "Bright indirect light", "Water when top soil dries", "Bonsai soil mix", "Bonsai fertilizer monthly", "Premium decorative miniature tree", "A beautiful bonsai plant that gives a professional and artistic look to any space.", "Medium", "Small", "🌳"),]

def seed_plants():if Plant.query.count() >= 20:returnPlant.query.delete()for p in PLANT_DATA:plant = Plant(name=p[0], category=p[1], price=p[2], stock=p[3], sunlight=p[4], water=p[5], soil=p[6],fertilizer=p[7], benefits=p[8], description=p[9], difficulty=p[10], size=p[11], image_emoji=p[12])db.session.add(plant)db.session.commit()

-------------------------

Helpers

-------------------------

def admin_required(view):@wraps(view)def wrapped(*args, **kwargs):if not session.get("admin_logged_in"):flash("Please login to access admin dashboard.", "warning")return redirect(url_for("admin_login"))return view(*args, **kwargs)return wrapped

def get_cart_items_from_request():data = request.get_json(silent=True) or request.formraw_items = data.get("items", "[]") if hasattr(data, "get") else "[]"if isinstance(raw_items, list):item_list = raw_itemselse:item_list = json.loads(raw_items or "[]")clean_items = []subtotal = 0for item in item_list:plant_id = int(item.get("id", 0))qty = max(1, int(item.get("quantity", 1)))plant = Plant.query.get(plant_id)if not plant:continueqty = min(qty, plant.stock)line_total = plant.price * qtysubtotal += line_totalclean_items.append({"id": plant.id,"name": plant.name,"price": plant.price,"quantity": qty,"line_total": line_total,"emoji": plant.image_emoji,})return clean_items, subtotal

def plant_to_chat_dict(plant):return {"id": plant.id,"name": plant.name,"category": plant.category,"price": plant.price,"stock": plant.stock,"sunlight": plant.sunlight,"water": plant.water,"soil": plant.soil,"fertilizer": plant.fertilizer,"benefits": plant.benefits,"description": plant.description,"difficulty": plant.difficulty,"size": plant.size,"emoji": plant.image_emoji,}

def chatbot_reply(message):plants = [plant_to_chat_dict(p) for p in Plant.query.order_by(Plant.name.asc()).all()]chat_context = session.get("chat_context", {})result = generate_chat_response(message, plants, chat_context)session["chat_context"] = result.get("context", {})session.modified = Truereturn result

-------------------------

Public Routes

-------------------------

@app.route("/")def home():featured = Plant.query.order_by(Plant.id.asc()).limit(8).all()categories = [row[0] for row in db.session.query(Plant.category).distinct().all()]return render_template("index.html", plants=featured, categories=categories)

@app.route("/plants")def plants():query = request.args.get("q", "").strip()category = request.args.get("category", "").strip()sort = request.args.get("sort", "name")plant_query = Plant.queryif query:plant_query = plant_query.filter(Plant.name.ilike(f"%{query}%") | Plant.benefits.ilike(f"%{query}%") | Plant.category.ilike(f"%{query}%"))if category:plant_query = plant_query.filter_by(category=category)if sort == "low":plant_query = plant_query.order_by(Plant.price.asc())elif sort == "high":plant_query = plant_query.order_by(Plant.price.desc())else:plant_query = plant_query.order_by(Plant.name.asc())plants = plant_query.all()categories = [row[0] for row in db.session.query(Plant.category).distinct().all()]return render_template("plants.html", plants=plants, categories=categories, query=query, selected_category=category, sort=sort)

@app.route("/plant/int:id")def plant_details(id):plant = Plant.query.get_or_404(id)related = Plant.query.filter(Plant.category == plant.category, Plant.id != plant.id).limit(4).all()return render_template("plant_details.html", plant=plant, related=related)

@app.route("/cart")def cart():return render_template("cart.html")@app.route("/checkout")def checkout():key_id = os.environ.get("RAZORPAY_KEY_ID")return render_template("checkout.html", razorpay_key_id=key_id)

@app.route("/care-tips")def care_tips():return render_template("care_tips.html")

@app.route("/disease")def disease():return render_template("disease.html")

@app.route("/reminders")def reminders():return render_template("reminders.html")

@app.route("/request-plant", methods=["GET", "POST"])def request_plant():if request.method == "POST":req = PlantRequest(name=request.form.get("name", "").strip(),phone=request.form.get("phone", "").strip(),plant_name=request.form.get("plant_name", "").strip(),message=request.form.get("message", "").strip(),)if not req.name or not req.phone or not req.plant_name:flash("Please fill name, phone and plant name.", "danger")else:db.session.add(req)db.session.commit()flash("Plant request submitted successfully. We will contact you soon.", "success")return redirect(url_for("request_plant"))return render_template("request_plant.html")

@app.route("/contact", methods=["GET", "POST"])def contact():if request.method == "POST":flash("Thank you! Your message has been received.", "success")return redirect(url_for("contact"))return render_template("contact.html")

-------------------------

API Routes

-------------------------

@app.route("/api/plants")def api_plants():plants = Plant.query.order_by(Plant.name.asc()).all()return jsonify([{"id": p.id,"name": p.name,"category": p.category,"price": p.price,"stock": p.stock,"emoji": p.image_emoji,"sunlight": p.sunlight,"water": p.water,"benefits": p.benefits,} for p in plants])

@app.route("/api/cart/summary", methods=["POST"])def cart_summary():items, subtotal = get_cart_items_from_request()delivery_fee = 0 if subtotal >= 999 or subtotal == 0 else 79return jsonify({"items": items, "subtotal": subtotal, "delivery_fee": delivery_fee, "total": subtotal + delivery_fee})

@app.route("/chatbot", methods=["POST"])def chatbot():data = request.get_json(silent=True) or {}result = chatbot_reply(data.get("message", ""))return jsonify(result)

@app.route("/chatbot/reset", methods=["POST"])def chatbot_reset():session.pop("chat_context", None)return jsonify({"success": True, "message": "Chat memory cleared."})

@app.route("/detect", methods=["POST"])def detect():file = request.files.get("image")if not file or not file.filename:return jsonify({"success": False, "message": "Please upload a clear plant leaf image."}), 400

filename = secure_filename(file.filename)
ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
if ext not in {"jpg", "jpeg", "png", "webp"}:
    return jsonify({"success": False, "message": "Only JPG, JPEG, PNG or WEBP images are allowed."}), 400

saved_name = f"{uuid.uuid4().hex}_{filename}"
path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
file.save(path)

try:
    prediction = predict_leaf_disease(path)
    return jsonify({
        "success": True,
        "disease": prediction["disease"],
        "confidence": prediction["confidence"],
        "advice": prediction["advice"],
        "mode": prediction.get("mode", "Image analysis demo"),
        "filename": saved_name,
    })
except Exception as exc:
    return jsonify({
        "success": False,
        "message": "Could not analyse this image. Please upload a clear JPG/PNG leaf photo.",
        "error": str(exc),
    }), 500

@app.route("/api/order", methods=["POST"])def create_order():data = request.get_json(silent=True) or {}items, subtotal = get_cart_items_from_request()if not items:return jsonify({"success": False, "message": "Cart is empty."}), 400required = ["customer_name", "email", "phone", "address", "city", "pincode", "payment_method"]missing = [field for field in required if not str(data.get(field, "")).strip()]if missing:return jsonify({"success": False, "message": "Please fill all checkout fields."}), 400delivery_fee = 0 if subtotal >= 999 else 79total = subtotal + delivery_feeorder = Order(order_no="AKS" + datetime.utcnow().strftime("%Y%m%d") + uuid.uuid4().hex[:6].upper(),customer_name=data["customer_name"].strip(),email=data["email"].strip(),phone=data["phone"].strip(),address=data["address"].strip(),city=data["city"].strip(),pincode=data["pincode"].strip(),items_json=json.dumps(items),subtotal=subtotal,delivery_fee=delivery_fee,total=total,payment_method=data["payment_method"],payment_status="Paid" if data["payment_method"] == "razorpay" and data.get("payment_verified") else "Cash on Delivery",razorpay_order_id=data.get("razorpay_order_id"),razorpay_payment_id=data.get("razorpay_payment_id"),)db.session.add(order)for item in items:plant = Plant.query.get(item["id"])if plant:plant.stock = max(0, plant.stock - item["quantity"])db.session.commit()return jsonify({"success": True, "order_no": order.order_no, "total": total, "payment_status": order.payment_status})

@app.route("/api/payment/create-razorpay-order", methods=["POST"])def create_razorpay_order():

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

print("KEY ID:", key_id)
print("KEY SECRET:", key_secret)
print("Razorpay Module:", razorpay)

if razorpay is None:
    return jsonify({
        "success": False,
        "message": "Razorpay package is not installed."
    }), 400

if not key_id or not key_secret:
    return jsonify({
        "success": False,
        "message": "Razorpay API Keys are missing. Check your .env file."
    }), 400

items, subtotal = get_cart_items_from_request()

if not items:
    return jsonify({
        "success": False,
        "message": "Cart is empty."
    }), 400

delivery_fee = 0 if subtotal >= 999 else 79
total = subtotal + delivery_fee

client = razorpay.Client(auth=(key_id, key_secret))

razor_order = client.order.create({
    "amount": total * 100,
    "currency": "INR",
    "payment_capture": 1
})

session["pending_razorpay_order_id"] = razor_order["id"]

return jsonify({
    "success": True,
    "key_id": key_id,
    "order_id": razor_order["id"],
    "amount": total * 100,
    "currency": "INR"
})

@app.route("/api/payment/verify", methods=["POST"])def verify_payment():data = request.get_json(silent=True) or {}secret = os.environ.get("RAZORPAY_KEY_SECRET")if not secret:return jsonify({"success": False, "message": "Payment secret not configured."}), 400order_id = data.get("razorpay_order_id", "")payment_id = data.get("razorpay_payment_id", "")signature = data.get("razorpay_signature", "")if session.get("pending_razorpay_order_id") != order_id:return jsonify({"success": False, "message": "Payment order mismatch."}), 400generated = hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()if hmac.compare_digest(generated, signature):session.pop("pending_razorpay_order_id", None)return jsonify({"success": True, "message": "Payment verified successfully."})return jsonify({"success": False, "message": "Payment verification failed."}), 400

-------------------------

Admin Routes

-------------------------

@app.route("/admin/login", methods=["GET", "POST"])def admin_login():if request.method == "POST":username = request.form.get("username", "")password = request.form.get("password", "")admin_user = os.environ.get("ADMIN_USERNAME", "admin")admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")if username == admin_user and password == admin_password:session["admin_logged_in"] = Trueflash("Admin login successful.", "success")return redirect(url_for("admin"))flash("Invalid username or password.", "danger")return render_template("admin_login.html")

@app.route("/admin/logout")def admin_logout():session.pop("admin_logged_in", None)flash("Admin logged out.", "success")return redirect(url_for("home"))

@app.route("/admin")@admin_requireddef admin():plants = Plant.query.order_by(Plant.id.desc()).all()orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()requests = PlantRequest.query.order_by(PlantRequest.created_at.desc()).limit(10).all()return render_template("admin.html", plants=plants, orders=orders, requests=requests)

@app.route("/admin/plant/new", methods=["GET", "POST"])@admin_requireddef admin_plant_new():return save_plant()

@app.route("/admin/plant/int:id/edit", methods=["GET", "POST"])@admin_requireddef admin_plant_edit(id):plant = Plant.query.get_or_404(id)return save_plant(plant)

def save_plant(plant=None):if plant is None:plant = Plant()if request.method == "POST":plant.name = request.form.get("name", "").strip()plant.category = request.form.get("category", "").strip() or "Indoor"plant.price = int(request.form.get("price") or 0)plant.stock = int(request.form.get("stock") or 0)plant.sunlight = request.form.get("sunlight", "").strip()plant.water = request.form.get("water", "").strip()plant.soil = request.form.get("soil", "").strip()plant.fertilizer = request.form.get("fertilizer", "").strip()plant.benefits = request.form.get("benefits", "").strip()plant.description = request.form.get("description", "").strip()plant.difficulty = request.form.get("difficulty", "Easy").strip()plant.size = request.form.get("size", "Medium").strip()plant.image_emoji = request.form.get("image_emoji", "🌿").strip() or "🌿"if not plant.name or not plant.price:flash("Plant name and price are required.", "danger")else:db.session.add(plant)db.session.commit()flash("Plant saved successfully.", "success")return redirect(url_for("admin"))return render_template("admin_plant_form.html", plant=plant)

@app.route("/admin/plant/int:id/delete", methods=["POST"])@admin_requireddef admin_plant_delete(id):plant = Plant.query.get_or_404(id)db.session.delete(plant)db.session.commit()flash("Plant deleted successfully.", "success")return redirect(url_for("admin"))

-------------------------

App Start

-------------------------

def ensure_database():db.create_all()inspector = inspect(db.engine)columns = {col["name"] for col in inspector.get_columns("plant")} if inspector.has_table("plant") else set()required = {"id", "name", "category", "price", "stock", "sunlight", "water", "soil", "fertilizer", "benefits", "description", "difficulty", "size", "image_emoji"}if not required.issubset(columns):db.drop_all()db.create_all()seed_plants()

with app.app_context():ensure_database()

if name == "main":app.run(debug=True)