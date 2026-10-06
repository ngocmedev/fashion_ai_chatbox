import os
import re
import json
import sqlite3
import random
import uuid
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from ai.chatbot import FashionChatbot
from database.init_db import init_database

app = Flask(__name__, template_folder="ui_ux", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "evern_fashion_secret_key_2026_genz_vibes")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Ensure database is initialized
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database", "database.db")
if not os.path.exists(DB_FILE):
    init_database()

# Uploads directory for user/admin uploaded files
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def save_uploaded_image(file_storage):
    """Lưu ảnh tải lên từ máy tính vào thư mục static/uploads và trả về đường dẫn URL."""
    if not file_storage or not getattr(file_storage, "filename", None):
        return None
    orig_name = file_storage.filename.strip()
    if not orig_name:
        return None
    ext = os.path.splitext(orig_name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".jpg"
    safe_name = f"prod_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, safe_name)
    file_storage.save(filepath)
    return f"/static/uploads/{safe_name}"

def save_uploaded_images(file_storages):
    """Lưu danh sách nhiều ảnh tải lên từ máy tính vào thư mục static/uploads và trả về list đường dẫn URL."""
    urls = []
    if not file_storages:
        return urls
    for f in file_storages:
        url = save_uploaded_image(f)
        if url:
            urls.append(url)
    return urls

# Initialize Chatbot engine
chatbot = FashionChatbot()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    current_user = None
    pending_orders_count = 0
    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                current_user = dict(row)
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending_confirmation'")
            p_row = cursor.fetchone()
            if p_row:
                pending_orders_count = p_row[0]
            conn.close()
        except Exception as e:
            print(f"Error fetching current_user: {e}")
    return {"current_user": current_user, "pending_orders_count": pending_orders_count}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products_page():
    return render_template("products.html")

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return redirect(url_for("index"))

    product = dict(row)

    # Gallery images: parse from product["images"] or fallback to product["image_url"]
    gallery_images = []
    if product.get("images"):
        try:
            parsed = json.loads(product["images"])
            if isinstance(parsed, list):
                gallery_images = [str(img).strip() for img in parsed if img and str(img).strip()]
        except Exception:
            gallery_images = [img.strip() for img in product["images"].split(",") if img.strip()]
            
    if not gallery_images and product.get("image_url"):
        gallery_images = [product["image_url"].strip()]
        
    if not gallery_images:
        gallery_images = ["/static/images/placeholder.jpg"]

    product["gallery_images"] = gallery_images

    # Query related products (excluding current product, prioritize same category)
    cursor.execute("""
        SELECT * FROM products 
        WHERE id != ? 
        ORDER BY CASE WHEN category = ? THEN 0 ELSE 1 END, id DESC 
        LIMIT 4
    """, (product_id, product.get("category", "")))
    related_products = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template("product_detail.html", product=product, related_products=related_products)

@app.route("/register", methods=["GET", "POST"])
def register():
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")
    if not next_url.startswith("/"):
        next_url = url_for("index")

    if session.get("user_id"):
        return redirect(next_url)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not full_name or not username or not email or not password:
            return render_template(
                "register.html",
                error="Vui lòng điền đầy đủ các thông tin bắt buộc.",
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
                next_url=next_url
            )

        if len(username) < 3 or not re.match(r"^[a-zA-Z0-9_]+$", username):
            return render_template(
                "register.html",
                error="Tên người dùng phải từ 3 ký tự và chỉ chứa chữ, số, gạch dưới.",
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
                next_url=next_url
            )

        if len(password) < 6:
            return render_template(
                "register.html",
                error="Mật khẩu phải có ít nhất 6 ký tự.",
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
                next_url=next_url
            )

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email FROM users WHERE username = ? OR email = ?", (username, email))
            existing = cursor.fetchone()
            if existing:
                if existing["username"] == username:
                    conn.close()
                    return render_template(
                        "register.html",
                        error="Tên người dùng này đã tồn tại.",
                        full_name=full_name,
                        username=username,
                        email=email,
                        phone=phone,
                        next_url=next_url
                    )
                if existing["email"] == email:
                    conn.close()
                    return render_template(
                        "register.html",
                        error="Email này đã được đăng ký tài khoản.",
                        full_name=full_name,
                        username=username,
                        email=email,
                        phone=phone,
                        next_url=next_url
                    )

            pw_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, pw_hash, full_name, phone))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            session["user_id"] = user_id
            session["username"] = username
            return redirect(next_url)
        except Exception as e:
            return render_template(
                "register.html",
                error=f"Đã xảy ra lỗi khi tạo tài khoản: {str(e)}",
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
                next_url=next_url
            )

    return render_template("register.html", next_url=next_url)

@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")
    if not next_url.startswith("/"):
        next_url = url_for("index")

    if session.get("user_id"):
        return redirect(next_url)

    if request.method == "POST":
        identifier = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template("login.html", error="Vui lòng nhập tên đăng nhập/email và mật khẩu.", username=identifier, next_url=next_url)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, password_hash, full_name FROM users WHERE username = ? OR email = ?", (identifier, identifier))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(next_url)
            else:
                return render_template("login.html", error="Tên đăng nhập hoặc mật khẩu không chính xác.", username=identifier, next_url=next_url)
        except Exception as e:
            return render_template("login.html", error=f"Lỗi đăng nhập: {str(e)}", username=identifier, next_url=next_url)

    return render_template("login.html", next_url=next_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login", next="/profile"))

    conn = get_db_connection()
    cursor = conn.cursor()

    success_msg = None
    error_msg = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "").strip()
        birthday = request.form.get("birthday", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        district = request.form.get("district", "").strip()
        ward = request.form.get("ward", "").strip()
        notes = request.form.get("notes", "").strip()

        # Password change fields (optional)
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()

        if new_password:
            if not current_password:
                error_msg = "Vui lòng nhập mật khẩu hiện tại để đổi sang mật khẩu mới."
            elif not check_password_hash(user_row["password_hash"], current_password):
                error_msg = "Mật khẩu hiện tại không chính xác."
            elif len(new_password) < 6:
                error_msg = "Mật khẩu mới phải có ít nhất 6 ký tự."
            elif new_password != confirm_password:
                error_msg = "Xác nhận mật khẩu mới không trùng khớp."
            else:
                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))

        if not error_msg:
            try:
                cursor.execute("""
                    UPDATE users 
                    SET full_name = ?, phone = ?, gender = ?, birthday = ?,
                        address = ?, city = ?, district = ?, ward = ?, notes = ?
                    WHERE id = ?
                """, (full_name, phone, gender, birthday, address, city, district, ward, notes, user_id))
                conn.commit()
                success_msg = "Cập nhật thông tin cá nhân thành công!"
            except Exception as e:
                error_msg = f"Đã xảy ra lỗi khi lưu thông tin: {str(e)}"

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())
    conn.close()

    return render_template("profile.html", user=user, success_msg=success_msg, error_msg=error_msg)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get("message", "").strip()
    current_product = data.get("current_product")

    if not user_message:
        return jsonify({
            "reply": "Vui lòng nhập nội dung tin nhắn.",
            "intent": "empty",
            "products": []
        }), 400

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session.get("session_id")
    user_id = session.get("user_id")

    response = chatbot.respond(user_message, user_id=user_id, session_id=session_id, current_product=current_product)
    return jsonify(response)

@app.route("/api/chat/history", methods=["GET"])
def get_chat_history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "is_logged_in": False,
            "user_name": None,
            "history": []
        })

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_message, bot_response, intent, created_at 
            FROM chat_history 
            WHERE user_id = ? 
            ORDER BY id ASC 
            LIMIT 60
        """, (user_id,))
        rows = cursor.fetchall()

        cursor.execute("SELECT username, full_name FROM users WHERE id = ?", (user_id,))
        u = cursor.fetchone()
        user_name = (u["full_name"] or u["username"]) if u else "Bạn"
        conn.close()

        history = []
        for r in rows:
            history.append({
                "id": r["id"],
                "user_message": r["user_message"],
                "bot_response": r["bot_response"],
                "intent": r["intent"],
                "time": r["created_at"]
            })

        return jsonify({
            "is_logged_in": True,
            "user_name": user_name,
            "history": history
        })
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return jsonify({"is_logged_in": True, "user_name": "Bạn", "history": []})

@app.route("/api/chat/clear", methods=["POST"])
def clear_chat_history():
    user_id = session.get("user_id")
    session_id = session.get("session_id")
    chatbot.clear_context(user_id=user_id, session_id=session_id)
    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": True})

@app.route("/api/products", methods=["GET"])
def get_products():
    from ai.recommendation import FashionRecommender
    recommender = FashionRecommender()
    products = recommender.get_all_products()
    return jsonify(products)

@app.route("/api/admin/reindex-rag", methods=["POST"])
def admin_reindex_rag():
    try:
        count = chatbot.reindex_rag()
        return jsonify({
            "success": True,
            "message": f"Đã nạp và 'train' thành công {count} vector tri thức vào FAISS!",
            "vector_count": count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/reload-ai", methods=["GET", "POST"])
def admin_reload_ai():
    global chatbot
    try:
        import importlib
        import ai.entity
        import ai.recommendation
        import ai.response_generator
        import ai.chatbot
        importlib.reload(ai.entity)
        importlib.reload(ai.recommendation)
        importlib.reload(ai.response_generator)
        importlib.reload(ai.chatbot)
        chatbot = ai.chatbot.FashionChatbot()
        return jsonify({
            "success": True,
            "message": "Đã reload toàn bộ module AI và cập nhật logic mới nhất!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/checkout", methods=["GET"])
def checkout_view():
    user_id = session.get("user_id")
    # Khách vãng lai bắt buộc phải đăng nhập mới được vào trang thanh toán
    if not user_id:
        return redirect(url_for("login", next="/checkout"))

    user_info = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            user_info = dict(row)
        conn.close()
    except Exception as e:
        print(f"Error loading user for checkout: {e}")

    return render_template("checkout.html", user_info=user_info)

@app.route("/api/checkout", methods=["POST"])
def process_checkout():
    try:
        user_id = session.get("user_id")
        # Khách vãng lai bắt buộc phải đăng nhập mới được mua hàng
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Vui lòng đăng nhập để tiến hành mua hàng!"
            }), 401
        data = request.get_json(force=True, silent=True) or {}
        customer_name = data.get("customer_name", "").strip()
        customer_phone = data.get("customer_phone", "").strip()
        customer_email = data.get("customer_email", "").strip()
        shipping_address = data.get("shipping_address", "").strip()
        shipping_city = data.get("shipping_city", "").strip()
        order_notes = data.get("order_notes", "").strip()
        payment_method = data.get("payment_method", "COD").strip()
        items = data.get("items", [])
        total_amount = data.get("total_amount", 0)

        if not customer_name:
            return jsonify({"success": False, "error": "Vui lòng nhập Họ và tên người nhận."}), 400
        if not customer_phone:
            return jsonify({"success": False, "error": "Vui lòng nhập Số điện thoại liên hệ."}), 400
        if not shipping_address:
            return jsonify({"success": False, "error": "Vui lòng nhập Địa chỉ giao hàng."}), 400
        if not items or len(items) == 0:
            return jsonify({"success": False, "error": "Giỏ hàng đang trống."}), 400

        # Generate unique order code: EVN-YYMMDD-XXXX
        order_code = f"EVN-{datetime.now().strftime('%y%m%d')}-{random.randint(1000, 9999)}"
        user_id = session.get("user_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO orders (
                order_code, user_id, customer_name, customer_email, customer_phone,
                shipping_address, shipping_city, order_notes, payment_method, total_amount, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_code, user_id, customer_name, customer_email, customer_phone,
            shipping_address, shipping_city, order_notes, payment_method, int(total_amount), 'pending_confirmation'
        ))

        order_id = cursor.lastrowid

        for item in items:
            p_id = item.get("id")
            cat_id = None
            if p_id:
                cursor.execute("SELECT category_id FROM products WHERE id = ?", (p_id,))
                p_row = cursor.fetchone()
                if p_row and p_row["category_id"]:
                    cat_id = p_row["category_id"]

            cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, category_id, product_name, product_image, size, color, price, quantity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                p_id,
                cat_id,
                item.get("name", "Sản phẩm"),
                item.get("image_url", ""),
                item.get("size", "L"),
                item.get("color", "Mặc định"),
                int(item.get("price", 0)),
                int(item.get("quantity", 1))
            ))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "order_code": order_code,
            "order_id": order_id,
            "redirect_url": f"/order-success/{order_code}"
        })
    except Exception as e:
        print(f"Checkout error: {e}")
        return jsonify({"success": False, "error": f"Lỗi xử lý đơn hàng: {str(e)}"}), 500

@app.route("/order-success/<order_code>", methods=["GET"])
def order_success(order_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,))
    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return redirect(url_for("index"))

    order = dict(order_row)
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
    items = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template("order_success.html", order=order, items=items)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login", next=request.path))
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        u = cur.fetchone()
        conn.close()
        if not u or u["role"] != "admin":
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin")
@admin_required
def admin_root():
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. KPIs
    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'cancelled'")
    total_revenue = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending_confirmation'")
    pending_orders = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM products WHERE stock <= 10")
    low_stock_count = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0] or 0

    # 2. Recent orders
    cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 6")
    recent_orders = [dict(r) for r in cur.fetchall()]

    # 3. Order status counts
    cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
    status_map = dict(cur.fetchall())
    status_counts = {
        "delivered": status_map.get("delivered", 0),
        "pending": status_map.get("pending_confirmation", 0),
        "shipping": status_map.get("shipping", 0),
        "preparing": status_map.get("preparing", 0),
        "cancelled": status_map.get("cancelled", 0)
    }

    # 4. Monthly revenues for the current year
    months_labels = ["Th 1", "Th 2", "Th 3", "Th 4", "Th 5", "Th 6", "Th 7", "Th 8", "Th 9", "Th 10", "Th 11", "Th 12"]
    now = datetime.now()
    year_str = str(now.year)
    monthly_rev = [0] * 12

    cur.execute("""
        SELECT strftime('%m', created_at) as m, SUM(total_amount) 
        FROM orders 
        WHERE status != 'cancelled' AND strftime('%Y', created_at) = ?
        GROUP BY m
    """, (year_str,))
    for row in cur.fetchall():
        try:
            m_idx = int(row[0]) - 1
            if 0 <= m_idx < 12:
                monthly_rev[m_idx] = row[1] or 0
        except Exception:
            pass

    conn.close()

    return render_template(
        "admin/dashboard.html",
        active_page="dashboard",
        total_revenue=total_revenue,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_products=total_products,
        low_stock_count=low_stock_count,
        total_users=total_users,
        recent_orders=recent_orders,
        chart_months=months_labels,
        chart_revenues=monthly_rev,
        status_counts=status_counts
    )

# ----------------- 2. QUẢN LÝ DANH MỤC -----------------
@app.route("/admin/categories")
@admin_required
def admin_categories():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, 
               (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id OR LOWER(TRIM(p.category)) = LOWER(TRIM(c.name))) as product_count,
               COALESCE((
                   SELECT SUM(oi.quantity) 
                   FROM order_items oi 
                   JOIN orders o ON oi.order_id = o.id 
                   WHERE (oi.category_id = c.id OR oi.product_id IN (SELECT id FROM products WHERE category_id = c.id))
                     AND o.status != 'cancelled'
               ), 0) as total_sold,
               COALESCE((
                   SELECT SUM(oi.quantity * oi.price) 
                   FROM order_items oi 
                   JOIN orders o ON oi.order_id = o.id 
                   WHERE (oi.category_id = c.id OR oi.product_id IN (SELECT id FROM products WHERE category_id = c.id))
                     AND o.status != 'cancelled'
               ), 0) as total_revenue
        FROM categories c 
        ORDER BY c.id ASC
    """)
    categories = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template("admin/categories.html", active_page="categories", categories=categories)

@app.route("/admin/categories/add", methods=["POST"])
@admin_required
def admin_add_category():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower()
    desc = request.form.get("description", "").strip()
    if name:
        conn = get_db_connection()
        conn.execute("INSERT OR IGNORE INTO categories (name, slug, description) VALUES (?, ?, ?)", (name, slug or name.lower(), desc))
        conn.commit()
        conn.close()
    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/edit/<int:cat_id>", methods=["POST"])
@admin_required
def admin_edit_category(cat_id):
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower()
    desc = request.form.get("description", "").strip()
    if name:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE categories SET name = ?, slug = ?, description = ? WHERE id = ?", (name, slug, desc, cat_id))
        cur.execute("UPDATE products SET category = ? WHERE category_id = ?", (name, cat_id))
        conn.commit()
        conn.close()
    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/delete/<int:cat_id>", methods=["POST"])
@admin_required
def admin_delete_category(cat_id):
    conn = get_db_connection()
    conn.execute("UPDATE products SET category_id = NULL WHERE category_id = ?", (cat_id,))
    conn.execute("UPDATE order_items SET category_id = NULL WHERE category_id = ?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_categories"))

# ----------------- 3. QUẢN LÝ SẢN PHẨM -----------------
@app.route("/admin/products")
@admin_required
def admin_products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    category_id = request.args.get("category_id", "").strip()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name ASC")
    categories = [dict(r) for r in cur.fetchall()]

    query = """
        SELECT p.*, COALESCE(c.name, p.category) as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (p.name LIKE ? OR p.code LIKE ? OR p.tags LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if category_id and category_id.isdigit():
        query += " AND p.category_id = ?"
        params.append(int(category_id))
    elif category:
        query += " AND (p.category = ? OR c.name = ?)"
        params.extend([category, category])
    query += " ORDER BY p.id DESC"

    cur.execute(query, params)
    products = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template(
        "admin/products.html",
        active_page="products",
        products=products,
        categories=categories,
        selected_category=category,
        selected_category_id=int(category_id) if category_id and category_id.isdigit() else None,
        search_query=search
    )

@app.route("/admin/products/add", methods=["POST"])
@admin_required
def admin_add_product():
    try:
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        category_id_raw = request.form.get("category_id", "").strip()
        category_raw = request.form.get("category", "").strip()
        try:
            stock = int(request.form.get("stock", 50))
        except (ValueError, TypeError):
            stock = 50
        try:
            price = int(request.form.get("price", 0))
        except (ValueError, TypeError):
            price = 0
        try:
            old_price = int(request.form.get("old_price", 0)) if request.form.get("old_price") else int(price * 1.15)
        except (ValueError, TypeError):
            old_price = int(price * 1.15)
        color = request.form.get("color", "").strip()
        color_hex = request.form.get("color_hex", "#111111").strip()
        sizes = request.form.get("sizes", "S, M, L, XL").strip()
        fit = request.form.get("fit", "").strip()
        
        # 1. Thu thập tất cả file ảnh tải lên từ máy tính
        uploaded_files = request.files.getlist("image_files")
        if not uploaded_files:
            single_f = request.files.get("image_file")
            if single_f:
                uploaded_files = [single_f]
        uploaded_urls = save_uploaded_images(uploaded_files)

        # 2. Thu thập các URL người dùng nhập
        input_urls = []
        raw_urls = request.form.get("image_urls", "").strip()
        if raw_urls:
            for line in raw_urls.replace(",", "\n").splitlines():
                clean = line.strip()
                if clean:
                    input_urls.append(clean)
        single_url = request.form.get("image_url", "").strip()
        if single_url and single_url not in input_urls:
            input_urls.append(single_url)

        # Gộp tất cả ảnh: file tải lên trước, sau đó là URL nhập
        all_images = []
        for u in uploaded_urls + input_urls:
            if u and u not in all_images:
                all_images.append(u)

        if not all_images:
            all_images = ["/static/images/placeholder.jpg"]

        primary_image = all_images[0]
        images_json = json.dumps(all_images, ensure_ascii=False)
        
        tags = request.form.get("tags", "").strip()
        desc = request.form.get("description", "").strip()

        if name and price > 0:
            conn = get_db_connection()
            cur = conn.cursor()
            cat_id = int(category_id_raw) if category_id_raw and category_id_raw.isdigit() else None
            cat_name = category_raw
            if cat_id:
                cur.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
                c_row = cur.fetchone()
                if c_row:
                    cat_name = c_row["name"]
            elif cat_name:
                cur.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
                c_row = cur.fetchone()
                if c_row:
                    cat_id = c_row["id"]

            cur.execute("""
                INSERT INTO products (
                    name, code, category_id, category, stock, price, old_price, color, color_hex,
                    sizes, fit, image_url, images, tags, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, code or f"EV{random.randint(1000, 9999)}", cat_id, cat_name, stock,
                price, old_price, color, color_hex, sizes, fit, primary_image, images_json, tags, desc
            ))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[Admin] Lỗi thêm sản phẩm: {e}")
    return redirect(url_for("admin_products"))

@app.route("/admin/products/edit/<int:prod_id>", methods=["POST"])
@admin_required
def admin_edit_product(prod_id):
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    category_id_raw = request.form.get("category_id", "").strip()
    category_raw = request.form.get("category", "").strip()
    try:
        stock = int(request.form.get("stock", 50))
    except (ValueError, TypeError):
        stock = 50
    try:
        price = int(request.form.get("price", 0))
    except (ValueError, TypeError):
        price = 0
    try:
        old_price = int(request.form.get("old_price", 0)) if request.form.get("old_price") else price
    except (ValueError, TypeError):
        old_price = price
    color = request.form.get("color", "").strip()
    color_hex = request.form.get("color_hex", "#111111").strip()
    sizes = request.form.get("sizes", "").strip()
    fit = request.form.get("fit", "").strip()
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT image_url, images FROM products WHERE id = ?", (prod_id,))
    old_row = cur.fetchone()
    
    # 1. Giữ lại các ảnh cũ mà người dùng chưa xóa
    existing_images = []
    form_existing = request.form.getlist("existing_images")
    if form_existing:
        existing_images = [img.strip() for img in form_existing if img.strip()]
    elif "has_existing_images_field" not in request.form:
        if old_row:
            if old_row["images"]:
                try:
                    existing_images = json.loads(old_row["images"])
                except Exception:
                    existing_images = [img.strip() for img in old_row["images"].split(",") if img.strip()]
            elif old_row["image_url"]:
                existing_images = [old_row["image_url"]]

    # 2. Thu thập các tệp ảnh mới tải lên
    new_files = request.files.getlist("image_files")
    if not new_files:
        single_f = request.files.get("image_file")
        if single_f:
            new_files = [single_f]
    new_uploaded_urls = save_uploaded_images(new_files)

    # 3. Thu thập các URL mới nhập
    new_urls = []
    raw_urls = request.form.get("image_urls", "").strip()
    if raw_urls:
        for line in raw_urls.replace(",", "\n").splitlines():
            clean = line.strip()
            if clean:
                new_urls.append(clean)
    single_url = request.form.get("image_url", "").strip()
    if single_url and single_url not in new_urls and single_url not in existing_images:
        new_urls.append(single_url)

    # Gộp tất cả ảnh: ảnh cũ giữ lại + ảnh mới tải lên + URL mới
    all_images = []
    for u in existing_images + new_uploaded_urls + new_urls:
        if u and u not in all_images:
            all_images.append(u)

    if not all_images:
        if old_row and old_row["image_url"]:
            all_images = [old_row["image_url"]]
        else:
            all_images = ["/static/images/placeholder.jpg"]

    primary_image = all_images[0]
    images_json = json.dumps(all_images, ensure_ascii=False)

    tags = request.form.get("tags", "").strip()
    desc = request.form.get("description", "").strip()

    cat_id = int(category_id_raw) if category_id_raw and category_id_raw.isdigit() else None
    cat_name = category_raw
    if cat_id:
        cur.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
        c_row = cur.fetchone()
        if c_row:
            cat_name = c_row["name"]
    elif cat_name:
        cur.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        c_row = cur.fetchone()
        if c_row:
            cat_id = c_row["id"]

    cur.execute("""
        UPDATE products 
        SET name = ?, code = ?, category_id = ?, category = ?, stock = ?, price = ?, old_price = ?,
            color = ?, color_hex = ?, sizes = ?, fit = ?, image_url = ?, images = ?, tags = ?, description = ?
        WHERE id = ?
    """, (
        name, code, cat_id, cat_name, stock, price, old_price,
        color, color_hex, sizes, fit, primary_image, images_json, tags, desc, prod_id
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_products"))

@app.route("/api/admin/products/<int:prod_id>")
@admin_required
def api_admin_product_detail(prod_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, COALESCE(c.name, p.category) as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.id = ?
    """, (prod_id,))
    p = cur.fetchone()
    conn.close()
    if not p:
        return jsonify({"error": "Product not found"}), 404
        
    p_dict = dict(p)
    gallery = []
    if p_dict.get("images"):
        try:
            gallery = json.loads(p_dict["images"])
        except Exception:
            gallery = [img.strip() for img in p_dict["images"].split(",") if img.strip()]
    if not gallery and p_dict.get("image_url"):
        gallery = [p_dict["image_url"]]
    p_dict["gallery_images"] = gallery
    return jsonify({"product": p_dict})

@app.route("/admin/products/delete/<int:prod_id>", methods=["POST"])
@admin_required
def admin_delete_product(prod_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_products"))

# ----------------- 4. QUẢN LÝ NGƯỜI DÙNG -----------------
@app.route("/admin/users")
@admin_required
def admin_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template("admin/users.html", active_page="users", users=users)

@app.route("/admin/users/add", methods=["POST"])
@admin_required
def admin_add_user():
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip().lower()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    role = request.form.get("role", "customer").strip()
    password = request.form.get("password", "")

    if username and email and password:
        pw_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone, role, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (username, email, pw_hash, full_name, phone, role))
            conn.commit()
        except Exception as e:
            print(f"Error creating user: {e}")
        conn.close()
    return redirect(url_for("admin_users"))

@app.route("/admin/users/edit/<int:user_id>", methods=["POST"])
@admin_required
def admin_edit_user(user_id):
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    role = request.form.get("role", "customer").strip()
    status = request.form.get("status", "active").strip()
    new_password = request.form.get("new_password", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    if new_password:
        pw_hash = generate_password_hash(new_password)
        cur.execute("""
            UPDATE users SET full_name = ?, email = ?, phone = ?, role = ?, status = ?, password_hash = ?
            WHERE id = ?
        """, (full_name, email, phone, role, status, pw_hash, user_id))
    else:
        cur.execute("""
            UPDATE users SET full_name = ?, email = ?, phone = ?, role = ?, status = ?
            WHERE id = ?
        """, (full_name, email, phone, role, status, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users"))

@app.route("/admin/users/toggle-status/<int:user_id>", methods=["POST"])
@admin_required
def admin_toggle_user_status(user_id):
    current_uid = session.get("user_id")
    if current_uid != user_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            new_status = 'locked' if row['status'] == 'active' else 'active'
            cur.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
            conn.commit()
        conn.close()
    return redirect(url_for("admin_users"))

@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    current_uid = session.get("user_id")
    if current_uid != user_id:
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    return redirect(url_for("admin_users"))

# ----------------- 5. QUẢN LÝ ĐƠN HÀNG -----------------
@app.route("/admin/orders")
@admin_required
def admin_orders():
    status_filter = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status='pending_confirmation' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status='preparing' THEN 1 ELSE 0 END) as preparing,
               SUM(CASE WHEN status='shipping' THEN 1 ELSE 0 END) as shipping,
               SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered,
               SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM orders
    """)
    s_row = cur.fetchone()
    status_counts = {
        "total": s_row["total"] or 0,
        "pending": s_row["pending"] or 0,
        "preparing": s_row["preparing"] or 0,
        "shipping": s_row["shipping"] or 0,
        "delivered": s_row["delivered"] or 0,
        "cancelled": s_row["cancelled"] or 0
    }

    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if search:
        query += " AND (order_code LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    query += " ORDER BY id DESC"

    cur.execute(query, params)
    orders = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template(
        "admin/orders.html",
        active_page="orders",
        orders=orders,
        current_status=status_filter,
        search_query=search,
        status_counts=status_counts
    )

@app.route("/api/admin/orders/<int:order_id>", methods=["GET"])
@admin_required
def api_admin_order_detail(order_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    o = cur.fetchone()
    if not o:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    cur.execute("""
        SELECT oi.*, COALESCE(c.name, 'Thời trang') as category_name
        FROM order_items oi
        LEFT JOIN categories c ON oi.category_id = c.id
        WHERE oi.order_id = ?
    """, (order_id,))
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"order": dict(o), "items": items})

@app.route("/admin/orders/update-status/<int:order_id>", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    new_status = request.form.get("status", "").strip()
    if new_status:
        conn = get_db_connection()
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
    return redirect(request.referrer or url_for("admin_orders"))

@app.route("/admin/orders/delete/<int:order_id>", methods=["POST"])
@admin_required
def admin_delete_order(order_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_orders"))

# ----------------- 6. THỐNG KÊ DOANH THU -----------------
@app.route("/admin/revenue")
@admin_required
def admin_revenue():
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    month_str = datetime.now().strftime("%Y-%m")
    year_str = datetime.now().strftime("%Y")

    cur.execute("SELECT COALESCE(SUM(total_amount), 0), COUNT(*) FROM orders WHERE status != 'cancelled' AND date(created_at) = date(?)", (today_str,))
    t_row = cur.fetchone()
    rev_today = t_row[0] or 0
    orders_today_count = t_row[1] or 0

    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'cancelled' AND strftime('%Y-%m', created_at) = ?", (month_str,))
    rev_this_month = cur.fetchone()[0] or 0

    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'cancelled' AND strftime('%Y', created_at) = ?", (year_str,))
    rev_this_year = cur.fetchone()[0] or 0

    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'cancelled'")
    total_revenue = cur.fetchone()[0] or 0

    q = "SELECT * FROM orders WHERE status != 'cancelled'"
    p = []
    if from_date:
        q += " AND date(created_at) >= date(?)"
        p.append(from_date)
    if to_date:
        q += " AND date(created_at) <= date(?)"
        p.append(to_date)
    q += " ORDER BY id DESC LIMIT 60"

    cur.execute(q, p)
    revenue_orders = [dict(r) for r in cur.fetchall()]

    months_labels = ["Th 1", "Th 2", "Th 3", "Th 4", "Th 5", "Th 6", "Th 7", "Th 8", "Th 9", "Th 10", "Th 11", "Th 12"]
    monthly_values = [0] * 12
    cur.execute("""
        SELECT strftime('%m', created_at) as m, SUM(total_amount) 
        FROM orders 
        WHERE status != 'cancelled' AND strftime('%Y', created_at) = ?
        GROUP BY m
    """, (year_str,))
    for row in cur.fetchall():
        try:
            m_idx = int(row[0]) - 1
            if 0 <= m_idx < 12:
                monthly_values[m_idx] = row[1] or 0
        except Exception:
            pass

    conn.close()

    return render_template(
        "admin/revenue.html",
        active_page="revenue",
        rev_today=rev_today,
        orders_today_count=orders_today_count,
        rev_this_month=rev_this_month,
        rev_this_year=rev_this_year,
        total_revenue=total_revenue,
        from_date=from_date,
        to_date=to_date,
        revenue_orders=revenue_orders,
        chart_labels=months_labels,
        chart_values=monthly_values
    )

# ----------------- 7. QUẢN LÝ PHIẾU NHẬP KHO -----------------
@app.route("/admin/imports")
@admin_required
def admin_imports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM import_receipts ORDER BY id DESC")
    imports = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT id, name, price, stock FROM products ORDER BY name ASC")
    products = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template("admin/imports.html", active_page="imports", imports=imports, products=products)

@app.route("/admin/imports/create", methods=["POST"])
@admin_required
def admin_create_import():
    supplier = request.form.get("supplier_name", "").strip()
    prod_id = request.form.get("product_id")
    qty = int(request.form.get("quantity", 0))
    import_price = int(request.form.get("import_price", 0))
    notes = request.form.get("notes", "").strip()
    created_by = request.form.get("created_by", "").strip() or "Admin"

    if supplier and prod_id and qty > 0:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM products WHERE id = ?", (prod_id,))
        p_row = cur.fetchone()
        prod_name = p_row["name"] if p_row else "Sản phẩm"
        receipt_code = f"PN-{datetime.now().strftime('%y%m%d')}-{random.randint(1000, 9999)}"
        subtotal = qty * import_price

        cur.execute("""
            INSERT INTO import_receipts (receipt_code, supplier_name, total_amount, total_quantity, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (receipt_code, supplier, subtotal, qty, notes, created_by))
        receipt_id = cur.lastrowid

        cur.execute("""
            INSERT INTO import_receipt_items (receipt_id, product_id, product_name, quantity, import_price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (receipt_id, prod_id, prod_name, qty, import_price, subtotal))

        # Tự động cộng tồn kho
        cur.execute("UPDATE products SET stock = COALESCE(stock, 0) + ? WHERE id = ?", (qty, prod_id))
        conn.commit()
        conn.close()

    return redirect(url_for("admin_imports"))

@app.route("/api/admin/imports/<int:receipt_id>")
@admin_required
def api_admin_import_detail(receipt_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM import_receipts WHERE id = ?", (receipt_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return jsonify({"error": "Receipt not found"}), 404

    cur.execute("SELECT * FROM import_receipt_items WHERE receipt_id = ?", (receipt_id,))
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"receipt": dict(r), "items": items})

# ----------------- 8. QUẢN LÝ PHIẾU XUẤT KHO -----------------
@app.route("/admin/exports")
@admin_required
def admin_exports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM export_receipts ORDER BY id DESC")
    exports = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT id, name, stock FROM products ORDER BY name ASC")
    products = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template("admin/exports.html", active_page="exports", exports=exports, products=products)

@app.route("/admin/exports/create", methods=["POST"])
@admin_required
def admin_create_export():
    reason = request.form.get("reason", "").strip()
    prod_id = request.form.get("product_id")
    qty = int(request.form.get("quantity", 0))
    notes = request.form.get("notes", "").strip()
    created_by = request.form.get("created_by", "").strip() or "Admin"

    if reason and prod_id and qty > 0:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, stock FROM products WHERE id = ?", (prod_id,))
        p_row = cur.fetchone()
        prod_name = p_row["name"] if p_row else "Sản phẩm"
        curr_stock = p_row["stock"] if p_row and p_row["stock"] is not None else 0

        # Giới hạn không xuất quá tồn kho
        actual_qty = min(qty, curr_stock)
        if actual_qty > 0:
            receipt_code = f"PX-{datetime.now().strftime('%y%m%d')}-{random.randint(1000, 9999)}"
            cur.execute("""
                INSERT INTO export_receipts (receipt_code, reason, total_quantity, notes, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (receipt_code, reason, actual_qty, notes, created_by))
            receipt_id = cur.lastrowid

            cur.execute("""
                INSERT INTO export_receipt_items (receipt_id, product_id, product_name, quantity, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (receipt_id, prod_id, prod_name, actual_qty, notes))

            # Tự động trừ tồn kho
            cur.execute("UPDATE products SET stock = MAX(0, COALESCE(stock, 0) - ?) WHERE id = ?", (actual_qty, prod_id))
            conn.commit()
        conn.close()

    return redirect(url_for("admin_exports"))

@app.route("/api/admin/exports/<int:receipt_id>")
@admin_required
def api_admin_export_detail(receipt_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM export_receipts WHERE id = ?", (receipt_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return jsonify({"error": "Receipt not found"}), 404

    cur.execute("SELECT * FROM export_receipt_items WHERE receipt_id = ?", (receipt_id,))
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"receipt": dict(r), "items": items})

@app.route("/admin/db", methods=["GET"])
def view_db_web():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM chat_history ORDER BY id DESC LIMIT 50")
    chats = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, username, email, full_name, phone, created_at FROM users ORDER BY id DESC")
    users = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM user_favorites ORDER BY id DESC")
    favorites = [dict(r) for r in cursor.fetchall()]
    conn.close()

    html = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Evern. — SQLite Database Viewer</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: #FAFAF8; color: #111; padding: 24px 32px; }}
            h1 {{ font-size: 24px; margin-bottom: 8px; }}
            h2 {{ font-size: 18px; margin-top: 32px; margin-bottom: 12px; color: #FF4D30; }}
            table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.04); margin-bottom: 24px; }}
            th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #EAEAEA; font-size: 13px; }}
            th {{ background: #F3F3F1; font-weight: 700; color: #444; }}
            tr:hover {{ background: #FAF9F7; }}
            .pill {{ background: #F0F0EE; padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: 600; }}
            .img-thumb {{ width: 44px; height: 44px; object-fit: cover; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h1>Evern SQLite Database Viewer 🗄️</h1>
                <p style="color:#666; font-size:13px;">Đường dẫn file: <code>{DB_FILE}</code></p>
            </div>
            <a href="/" style="background:#111; color:#fff; padding:8px 16px; border-radius:99px; text-decoration:none; font-size:13px; font-weight:600;">← Quay lại Trang Chủ</a>
        </div>

        <h2>1. Bảng Người Dùng (users) — {len(users)} tài khoản</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Tên Người Dùng (Username)</th>
                    <th>Họ & Tên</th>
                    <th>Email</th>
                    <th>Điện Thoại</th>
                    <th>Ngày Đăng Ký</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''
                <tr>
                    <td>{u['id']}</td>
                    <td><strong>@{u['username']}</strong></td>
                    <td>{u['full_name']}</td>
                    <td>{u['email']}</td>
                    <td>{u['phone'] or '-'}</td>
                    <td style="color:#888; font-size:12px;">{u['created_at']}</td>
                </tr>''' for u in users]) if users else '<tr><td colspan="6" style="text-align:center; color:#999;">Chưa có tài khoản nào được đăng ký.</td></tr>'}
            </tbody>
        </table>

        <h2>2. Bảng Sản Phẩm (products) — {len(products)} mục</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Ảnh</th>
                    <th>Tên Sản Phẩm</th>
                    <th>Danh Mục</th>
                    <th>Màu</th>
                    <th>Giá</th>
                    <th>Kích Cỡ</th>
                    <th>Tags</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''
                <tr>
                    <td>{p['id']}</td>
                    <td><img src="{p['image_url']}" class="img-thumb" alt=""></td>
                    <td><strong>{p['name']}</strong><br><small style="color:#888;">{p['description'] or ''}</small></td>
                    <td><span class="pill">{p['category']}</span></td>
                    <td>{p['color'] or '-'}</td>
                    <td style="font-weight:700; color:#FF4D30;">{p['price']:,}đ</td>
                    <td>{p['sizes']}</td>
                    <td><span class="pill">{p['tags']}</span></td>
                </tr>''' for p in products])}
            </tbody>
        </table>

        <h2>3. Bảng Lịch Sử Chat (chat_history) — {len(chats)} tin nhắn gần nhất</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User ID</th>
                    <th>Tin Nhắn Của User</th>
                    <th>Phản Hồi Của Stylist</th>
                    <th>Intent</th>
                    <th>Thời Gian</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''
                <tr>
                    <td>{c['id']}</td>
                    <td>{c.get('user_id') or '-'}</td>
                    <td style="font-weight:600;">{c['user_message']}</td>
                    <td style="color:#444; max-width:400px;">{c['bot_response']}</td>
                    <td><span class="pill">{c['intent']}</span></td>
                    <td style="color:#888; font-size:12px;">{c['created_at']}</td>
                </tr>''' for c in chats]) if chats else '<tr><td colspan="6" style="text-align:center; color:#999;">Chưa có hội thoại nào được lưu.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "evern-fashion-ai"})

if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", 5000))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    print(f"Evern Fashion AI server running at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
