import os
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER,
            category TEXT,
            sub_category TEXT,
            color TEXT,
            sizes TEXT,
            price INTEGER,
            image_url TEXT,
            images TEXT,
            tags TEXT,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)

    # 2. Create users table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Create user_favorites table for wishlist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)

    # 4. Create chat_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_message TEXT,
            bot_response TEXT,
            intent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 5. Create orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT,
            customer_phone TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            shipping_city TEXT,
            order_notes TEXT,
            payment_method TEXT DEFAULT 'COD',
            total_amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending_confirmation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 6. Create order_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            category_id INTEGER,
            product_name TEXT NOT NULL,
            product_image TEXT,
            size TEXT,
            color TEXT,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    # 7. Create categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. Create import_receipts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_code TEXT UNIQUE NOT NULL,
            supplier_name TEXT NOT NULL,
            total_amount INTEGER NOT NULL DEFAULT 0,
            total_quantity INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            import_price INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,
            FOREIGN KEY (receipt_id) REFERENCES import_receipts(id) ON DELETE CASCADE
        )
    """)

    # 9. Create export_receipts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_code TEXT UNIQUE NOT NULL,
            reason TEXT NOT NULL,
            total_quantity INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (receipt_id) REFERENCES export_receipts(id) ON DELETE CASCADE
        )
    """)

    # Migration: check if user_id column exists in existing chat_history table
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns:
        try:
            cursor.execute("ALTER TABLE chat_history ADD COLUMN user_id INTEGER")
        except Exception as e:
            print(f"[Notice] chat_history column migration: {e}")

    # Migration: check if new columns exist in products table
    cursor.execute("PRAGMA table_info(products)")
    prod_columns = [col[1] for col in cursor.fetchall()]
    new_cols = [
        ("code", "TEXT"),
        ("color_hex", "TEXT"),
        ("collar", "TEXT"),
        ("sleeve", "TEXT"),
        ("material", "TEXT"),
        ("fit", "TEXT"),
        ("old_price", "INTEGER"),
        ("discount_pct", "INTEGER"),
        ("points", "INTEGER"),
        ("online_only", "INTEGER DEFAULT 1"),
        ("stock", "INTEGER DEFAULT 50"),
        ("category_id", "INTEGER REFERENCES categories(id) ON DELETE SET NULL")
    ]
    for col_name, col_type in new_cols:
        if col_name not in prod_columns:
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"[Notice] products column migration {col_name}: {e}")

    # Migration: check if category_id exists in order_items table
    cursor.execute("PRAGMA table_info(order_items)")
    order_item_columns = [col[1] for col in cursor.fetchall()]
    if "category_id" not in order_item_columns:
        try:
            cursor.execute("ALTER TABLE order_items ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL")
        except Exception as e:
            print(f"[Notice] order_items column migration category_id: {e}")

    # Migration: check if new columns exist in users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    user_new_cols = [
        ("address", "TEXT"),
        ("city", "TEXT"),
        ("district", "TEXT"),
        ("ward", "TEXT"),
        ("gender", "TEXT"),
        ("birthday", "TEXT"),
        ("notes", "TEXT"),
        ("role", "TEXT DEFAULT 'customer'"),
        ("status", "TEXT DEFAULT 'active'")
    ]
    for col_name, col_type in user_new_cols:
        if col_name not in user_columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"[Notice] users column migration {col_name}: {e}")

    # Pre-populate default categories
    default_categories = [
        ("Áo thun", "ao-thun", "Các mẫu áo thun T-shirt cotton, oversize, unisex trẻ trung"),
        ("Áo sơ mi", "ao-so-mi", "Áo sơ mi công sở, sơ mi cuban dạo phố thanh lịch"),
        ("Áo polo", "ao-polo", "Áo polo dệt kim, polo trơn phối đồ smart casual"),
        ("Quần jean", "quan-jean", "Quần jean ống suông, ống rộng thời thượng"),
        ("Quần tây", "quan-tay", "Quần âu tây, quần kaki form đứng chuẩn tôn dáng"),
        ("Áo khoác", "ao-khoac", "Áo blazer, bomber, hoodie giữ ấm phong cách"),
        ("Váy & Đầm", "vay-dam", "Đầm dự tiệc, chân váy xòe, đầm chữ A nữ tính"),
        ("Phụ kiện", "phu-kien", "Túi xách, thắt lưng, kính mắt phối đồ thời trang")
    ]
    for cat_name, cat_slug, cat_desc in default_categories:
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)",
                (cat_name, cat_slug, cat_desc)
            )

    # Ensure admin user and set hoangnam to admin
    from werkzeug.security import generate_password_hash
    cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'hoangnam'")

    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, phone, role, status)
            VALUES (?, ?, ?, ?, ?, 'admin', 'active')
        """, (
            "admin",
            "admin@evern.vn",
            generate_password_hash("admin123"),
            "Ban Quản Trị Evern",
            "0988888888"
        ))

    # Seed products from products.json if file exists
    if os.path.exists(PRODUCTS_JSON):
        with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
            products = json.load(f)

        for p in products:
            sizes_str = ",".join(p.get("sizes", [])) if isinstance(p.get("sizes"), list) else p.get("sizes", "")
            tags_str = ",".join(p.get("tags", [])) if isinstance(p.get("tags"), list) else p.get("tags", "")

            cursor.execute("""
                INSERT OR REPLACE INTO products (
                    id, name, code, category, sub_category, color, color_hex, sizes,
                    collar, sleeve, material, fit, price, old_price, discount_pct, points,
                    online_only, image_url, tags, description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p.get("id"),
                p.get("name"),
                p.get("code", f"EV{p.get('id'):04d}"),
                p.get("category"),
                p.get("sub_category"),
                p.get("color"),
                p.get("color_hex", "#111111"),
                sizes_str,
                p.get("collar", "Cổ đức"),
                p.get("sleeve", "Dài tay"),
                p.get("material", "Cotton"),
                p.get("fit", "Regular fit"),
                p.get("price"),
                p.get("old_price", int(p.get("price", 0) * 1.2)),
                p.get("discount_pct", p.get("discount_pct", 15)),
                p.get("points", int(p.get("price", 0) / 1000)),
                1 if p.get("online_only", True) else 0,
                p.get("image_url"),
                tags_str,
                p.get("description")
            ))

    # Sync category_id for products intelligently using Python UTF-8 mapping
    cursor.execute("SELECT id, name FROM categories")
    cat_dict = {r[1]: r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT id, name, category, sub_category FROM products")
    all_products = cursor.fetchall()

    mapping_kw = {
        "áo thun": "Áo thun",
        "áo sơ mi": "Áo sơ mi",
        "áo polo": "Áo polo",
        "quần jeans": "Quần jean",
        "jean": "Quần jean",
        "jeans": "Quần jean",
        "quần âu": "Quần tây",
        "quần khaki": "Quần tây",
        "quần tây": "Quần tây",
        "quần short": "Quần tây",
        "áo khoác": "Áo khoác",
        "blazer": "Áo khoác",
        "áo len": "Áo khoác",
        "đầm dạ hội": "Váy & Đầm",
        "chân váy": "Váy & Đầm",
        "váy": "Váy & Đầm",
        "phụ kiện": "Phụ kiện",
        "giày": "Phụ kiện",
        "thắt lưng": "Phụ kiện",
        "ví da": "Phụ kiện",
        "cà vạt": "Phụ kiện",
        "kính mát": "Phụ kiện"
    }

    for pid, pname, pcat, psub in all_products:
        target_name = None
        if psub and psub.lower().strip() in mapping_kw:
            target_name = mapping_kw[psub.lower().strip()]
        elif pcat and pcat.lower().strip() in mapping_kw:
            target_name = mapping_kw[pcat.lower().strip()]
        elif pcat and pcat.strip() in cat_dict:
            target_name = pcat.strip()

        if target_name and target_name in cat_dict:
            target_id = cat_dict[target_name]
            cursor.execute("UPDATE products SET category_id = ?, category = ? WHERE id = ?", (target_id, target_name, pid))

    # Sync category_id for order_items based on product_id
    cursor.execute("""
        UPDATE order_items
        SET category_id = (
            SELECT category_id FROM products
            WHERE products.id = order_items.product_id
            LIMIT 1
        )
        WHERE (category_id IS NULL OR category_id = 0) AND product_id IS NOT NULL
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized successfully with users, user_favorites, products, chat_history at: {DB_PATH}")

if __name__ == "__main__":
    init_database()
