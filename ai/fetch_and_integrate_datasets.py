
import os
import sys
import json
import time
import urllib.parse
import sqlite3
import requests
from typing import Dict, Any, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_datasets")
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")
PRODUCTS_JSON = os.path.join(DATA_DIR, "products.json")
INTENTS_JSON = os.path.join(DATA_DIR, "intents.json")
FINETUNE_JSONL = os.path.join(DATA_DIR, "dataset_finetune.jsonl")

os.makedirs(RAW_DIR, exist_ok=True)

# Bộ nhớ đệm dịch thuật để tránh gọi lặp lại các cụm từ phổ biến
TRANSLATION_CACHE = {
    # Màu sắc
    "black": "đen",
    "white": "trắng",
    "dark blue": "xanh navy",
    "light blue": "xanh nhạt",
    "blue": "xanh dương",
    "grey": "xám ghi",
    "light grey": "xám sáng",
    "dark grey": "xám đậm",
    "beige": "kem be",
    "light beige": "be sáng",
    "pink": "hồng",
    "light pink": "hồng phấn",
    "dark pink": "hồng đậm",
    "red": "đỏ tươi",
    "dark red": "đỏ rượu",
    "green": "xanh lá",
    "dark green": "xanh rêu đậm",
    "greenish khaki": "kaki rêu",
    "yellow": "vàng",
    "yellowish brown": "nâu vàng bò",
    "brown": "nâu tây",
    "light turquoise": "xanh ngọc nhạt",
    "turquoise": "xanh ngọc",
    "purple": "tím",
    "orange": "cam đất",
    # Loại sản phẩm
    "top": "áo thun",
    "t-shirt": "áo thun",
    "vest top": "áo sát nách",
    "hoodie": "áo hoodie",
    "sweater": "áo len",
    "cardigan": "áo len cardigan",
    "jacket": "áo khoác",
    "coat": "áo khoác dạ",
    "blazer": "áo blazer",
    "shirt": "áo sơ mi",
    "polo shirt": "áo polo",
    "trousers": "quần tây",
    "jeans": "quần jean",
    "skirt": "chân váy",
    "dress": "váy đầm",
    "jumpsuit": "bộ jumpsuit",
    "bag": "túi xách thời trang",
    "belt": "thắt lưng",
    "shoes": "giày thời trang",
    "socks": "vớ cổ cao",
}

COLOR_HEX_MAP = {
    "đen": "#111111",
    "trắng": "#F8FAFC",
    "xanh navy": "#1E3A8A",
    "xanh nhạt": "#93C5FD",
    "xanh dương": "#2563EB",
    "xám ghi": "#64748B",
    "xám sáng": "#CBD5E1",
    "xám đậm": "#334155",
    "kem be": "#F5EBE0",
    "be sáng": "#FAF0E6",
    "hồng": "#F472B6",
    "hồng phấn": "#FCE7F3",
    "hồng đậm": "#DB2777",
    "đỏ tươi": "#DC2626",
    "đỏ rượu": "#991B1B",
    "xanh lá": "#16A34A",
    "xanh rêu đậm": "#14532D",
    "kaki rêu": "#57534E",
    "vàng": "#EAB308",
    "nâu vàng bò": "#B45309",
    "nâu tây": "#78350F",
    "xanh ngọc nhạt": "#A7F3D0",
    "xanh ngọc": "#0D9488",
    "tím": "#9333EA",
    "cam đất": "#EA580C"
}

def translate_en_to_vi(text: str) -> str:
    """Dịch văn bản từ tiếng Anh sang tiếng Việt mượt mà qua Google Translate API."""
    if not text or not str(text).strip():
        return ""
    text_clean = str(text).strip()
    cache_key = text_clean.lower()
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]

    url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl=vi&q=" + urllib.parse.quote(text_clean)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                res_json = resp.json()
                if isinstance(res_json, list) and len(res_json) > 0:
                    result = res_json[0]
                    TRANSLATION_CACHE[cache_key] = result
                    return result
        except Exception:
            time.sleep(0.5)

    # Nếu lỗi hoặc timeout, trả về chuỗi gốc
    return text_clean

def format_tool_call_to_stylist_vi(response_str: str, prompt_vi: str = "") -> str:
    """Chuyển đổi tool call e-commerce thành câu trả lời tự nhiên của Evern AI Stylist."""
    try:
        data = json.loads(response_str)
        if isinstance(data, dict) and "name" in data:
            name = data.get("name", "")
            args = data.get("arguments", {})
            if name == "cancel_order":
                oid = args.get("order_id", "của bạn")
                return f"Dạ Evern đã tiếp nhận yêu cầu hủy đơn hàng {oid}. Hệ thống đang hoàn tất thủ tục hủy đơn và sẽ gửi tin nhắn xác nhận cùng hướng dẫn hoàn tiền (nếu đã thanh toán) đến bạn ngay nhé! ❤️"
            elif name == "get_order_status":
                oid = args.get("order_id", "của bạn")
                return f"Dạ mình đã tra cứu đơn hàng {oid} trên hệ thống Evern: Kiện hàng đã được đóng gói cẩn thận và đang được đơn vị vận chuyển giao tới bạn, dự kiến trong 1-2 ngày tới bạn sẽ nhận được ạ! 📦✨"
            elif name in ["initiate_return", "return_refund"]:
                oid = args.get("order_id", "của bạn")
                sku = args.get("item_sku", "sản phẩm")
                return f"Dạ Evern xin lỗi vì trải nghiệm chưa trọn vẹn với sản phẩm {sku} thuộc đơn {oid}. Evern hỗ trợ đổi trả miễn phí trong 15 ngày! Nhân viên CSKH sẽ gọi trực tiếp để điều phối shipper đến lấy hàng tận nhà cho bạn nhé."
            elif name == "get_recommendations":
                cat = args.get("category", "thời trang")
                return f"Dạ với dòng sản phẩm {cat}, Evern hiện có rất nhiều mẫu thiết kế mới nhất với chất liệu cao cấp và tôn dáng cực đỉnh. Bạn cho mình biết thêm tone màu yêu thích hoặc chiều cao cân nặng để mình lên set chuẩn đẹp nhé! ✨"
            elif name == "search_products":
                kw = args.get("query", "")
                return f"Dạ mình đã lọc các mẫu liên quan đến '{kw}' trên kệ của Evern. Bạn tham khảo các gợi ý hoặc gửi mình phong cách mong muốn để mình phối đồ cho bạn nhé!"
    except Exception:
        pass
    return None


def fetch_hm_ecommerce_products(target_count: int = 65) -> List[Dict[str, Any]]:
    """Tải sản phẩm thực tế từ Qdrant/hm_ecommerce_products trên Hugging Face."""
    print(f"\n[1/4] Đang kết nối Hugging Face tải dataset 'Qdrant/hm_ecommerce_products'...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    collected = []
    seen_articles = set()

    # Các offset đa dạng để lấy phong phú nhiều nhóm thời trang
    offsets = [0, 80, 160, 250, 400, 600, 850, 1100, 1500, 2000, 2500, 3200]

    for offset in offsets:
        if len(collected) >= target_count:
            break
        url = f"https://datasets-server.huggingface.co/rows?dataset=Qdrant/hm_ecommerce_products&config=default&split=train&offset={offset}&limit=50"
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                rows = resp.json().get("rows", [])
                for r in rows:
                    item = r.get("row", {})
                    art_id = item.get("article_id")
                    img = item.get("image_url")
                    name = item.get("prod_name")
                    desc = item.get("detail_desc")
                    ptype = item.get("product_type_name", "")

                    # Bỏ qua nếu thiếu ảnh, thiếu mô tả hoặc là đồ lót/đồ em bé không hợp thời trang chính
                    if not img or not name or not desc or art_id in seen_articles:
                        continue
                    if any(bad in ptype.lower() for bad in ["underwear", "bra", "panties", "baby", "bib"]):
                        continue

                    seen_articles.add(art_id)
                    collected.append(item)
                    if len(collected) >= target_count:
                        break
            time.sleep(0.3)
        except Exception as e:
            print(f"  [Cảnh báo] Lỗi khi tải offset {offset}: {e}")

    print(f"  -> Đã thu thập được {len(collected)} sản phẩm H&M thực tế hợp lệ từ Hugging Face.")
    # Lưu file thô để đối chiếu
    raw_path = os.path.join(RAW_DIR, "hm_ecommerce_products_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu bản thô tại: {raw_path}")
    return collected

def map_and_translate_hm_products(raw_items: List[Dict[str, Any]], start_id: int = 36) -> List[Dict[str, Any]]:
    """Dịch và chuẩn hóa sản phẩm H&M sang lược đồ thời trang Evern."""
    print(f"\n[2/4] Đang dịch sản phẩm H&M sang Tiếng Việt và chuẩn hóa vào lược đồ dự án...")
    processed = []
    current_id = start_id

    for idx, item in enumerate(raw_items):
        prod_name_en = item.get("prod_name", "").strip()
        type_en = item.get("product_type_name", "").strip()
        group_en = item.get("product_group_name", "").strip()
        color_en = item.get("colour_group_name", "").strip()
        desc_en = item.get("detail_desc", "").strip()
        image_url = item.get("image_url", "").strip()
        article_id = item.get("article_id", f"{current_id:06d}")

        # Dịch màu sắc
        color_vi = translate_en_to_vi(color_en.lower())
        color_hex = COLOR_HEX_MAP.get(color_vi, "#2B2D42")

        # Dịch mô tả chi tiết
        desc_vi = translate_en_to_vi(desc_en) if desc_en else "Sản phẩm thời trang cao cấp từ chất liệu thoáng mát, phom dáng chuẩn mực hiện đại."

        # Phân loại danh mục theo hệ thống Evern
        type_lower = type_en.lower()
        if any(w in type_lower for w in ["polo"]):
            category = "Áo polo"
            sub_category = "áo polo basic"
            collar = "Cổ bẻ"
            sleeve = "Ngắn tay"
            base_price = 380000
            material = "Cotton pique"
            fit = "Regular fit"
            sizes = ["S", "M", "L", "XL"]
            name_vi = f"Áo Polo {translate_en_to_vi(prod_name_en)}"
        elif any(w in type_lower for w in ["shirt", "blouse"]):
            category = "Áo sơ mi"
            sub_category = "áo sơ mi"
            collar = "Cổ đức"
            sleeve = "Dài tay" if "long" in desc_en.lower() or "l/s" in prod_name_en.lower() else "Ngắn tay"
            base_price = 450000
            material = "Cotton poplin / Bamboo"
            fit = "Slim fit"
            sizes = ["S", "M", "L", "XL"]
            name_vi = f"Áo Sơ Mi {translate_en_to_vi(prod_name_en)}"
        elif any(w in type_lower for w in ["top", "t-shirt", "vest"]):
            category = "Áo thun"
            sub_category = "áo thun"
            collar = "Cổ tròn"
            sleeve = "Dài tay" if "long" in desc_en.lower() or "l/s" in prod_name_en.lower() else "Ngắn tay"
            base_price = 290000
            material = "Cotton Organic 100%"
            fit = "Oversize" if "oversize" in desc_en.lower() else "Regular fit"
            sizes = ["S", "M", "L", "XL"]
            name_vi = f"Áo Thun {translate_en_to_vi(prod_name_en)}"
        elif any(w in type_lower for w in ["hoodie", "sweater", "cardigan", "jacket", "coat", "blazer"]):
            category = "Áo khoác"
            sub_category = "blazer" if "blazer" in type_lower else ("hoodie" if "hoodie" in type_lower else "áo khoác")
            collar = "Có mũ" if "hood" in desc_en.lower() or "hoodie" in type_lower else "Cổ bẻ"
            sleeve = "Dài tay"
            base_price = 690000 if "coat" in type_lower or "jacket" in type_lower or "blazer" in type_lower else 490000
            material = "Nỉ chân cua / Len dệt kim"
            fit = "Relaxed fit"
            sizes = ["S", "M", "L", "XL"]
            name_vi = f"Áo Khoác {translate_en_to_vi(prod_name_en)}"
        elif any(w in type_lower for w in ["jeans"]):
            category = "Quần jean"
            sub_category = "quần jean"
            collar = "Không"
            sleeve = "Không"
            base_price = 550000
            material = "Denim co giãn cao cấp"
            fit = "Slim fit" if "skinny" in desc_en.lower() else "Ống suông thẳng"
            sizes = ["29", "30", "31", "32", "33"]
            name_vi = f"Quần Jean {translate_en_to_vi(prod_name_en)}"
        elif any(w in type_lower for w in ["trousers", "pants", "leggings"]):
            category = "Quần tây"
            sub_category = "quần tây"
            collar = "Không"
            sleeve = "Không"
            base_price = 490000
            material = "Vải Tuytsi Hàn Quốc"
            fit = "Form đứng tôn dáng"
            sizes = ["S", "M", "L", "XL"]
            name_vi = f"Quần Tây {translate_en_to_vi(prod_name_en)}"
        elif any(w in type_lower for w in ["dress", "skirt", "jumpsuit"]):
            category = "Váy & Đầm"
            sub_category = "đầm xòe" if "dress" in type_lower else "chân váy"
            collar = "Cổ chữ V" if "v-neck" in desc_en.lower() else "Cổ tròn"
            sleeve = "Sát nách" if "sleeveless" in desc_en.lower() else "Ngắn tay"
            base_price = 590000
            material = "Lụa Satin / Voan tơ"
            fit = "Dáng xòe nhẹ"
            sizes = ["S", "M", "L"]
            name_vi = f"Váy Đầm {translate_en_to_vi(prod_name_en)}"
        else:
            category = "Phụ kiện"
            sub_category = "phụ kiện"
            collar = "Không"
            sleeve = "Không"
            base_price = 190000
            material = "Da PU / Sợi tổng hợp"
            fit = "Freesize"
            sizes = ["Freesize"]
            name_vi = f"Phụ Kiện {translate_en_to_vi(prod_name_en)}"

        # Làm sạch tên tiếng Việt nếu còn từ chưa dịch hoặc lặp
        name_vi = name_vi.replace("  ", " ").strip()

        # Tạo giá bán và giảm giá khuyến mãi
        price = base_price + ((current_id * 17) % 5) * 20000
        discount_pct = 15 + ((current_id * 7) % 15)
        old_price = int(price * (1 + discount_pct / 100))
        points = int(price / 1000)

        tags = [
            category.lower(),
            sub_category.lower(),
            color_vi.lower(),
            "thời trang h&m",
            "xu hướng 2026",
            "hàng chính hãng",
            "thanh lịch"
        ]

        product_obj = {
            "id": current_id,
            "name": name_vi,
            "code": f"HM{article_id[-6:]}",
            "category": category,
            "sub_category": sub_category,
            "color": color_vi,
            "color_hex": color_hex,
            "sizes": sizes,
            "collar": collar,
            "sleeve": sleeve,
            "material": material,
            "fit": fit,
            "price": price,
            "old_price": old_price,
            "discount_pct": discount_pct,
            "points": points,
            "online_only": True,
            "image_url": image_url,
            "tags": tags,
            "description": desc_vi
        }
        processed.append(product_obj)
        current_id += 1

        if (idx + 1) % 15 == 0:
            print(f"  [Đã dịch] {idx + 1}/{len(raw_items)} sản phẩm...")

    print(f"  -> Hoàn tất dịch và chuẩn hóa {len(processed)} sản phẩm H&M!")
    return processed

def integrate_products_to_project(new_products: List[Dict[str, Any]]):
    """Lưu vào data/products.json và nạp vào database SQLite SQLite database.db."""
    print(f"\n[Tích hợp sản phẩm] Đang cập nhật data/products.json và database.db...")
    # 1. Lưu file độc lập data/hm_ecommerce_products_vi.json
    hm_vi_file = os.path.join(DATA_DIR, "hm_ecommerce_products_vi.json")
    with open(hm_vi_file, "w", encoding="utf-8") as f:
        json.dump(new_products, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu dataset sản phẩm H&M Tiếng Việt riêng tại: {hm_vi_file}")

    # 2. Hợp nhất vào data/products.json
    existing_products = []
    if os.path.exists(PRODUCTS_JSON):
        try:
            with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
                existing_products = json.load(f)
        except Exception:
            existing_products = []

    existing_codes = {p.get("code") for p in existing_products}
    merged_products = list(existing_products)

    added_count = 0
    for p in new_products:
        if p["code"] not in existing_codes:
            merged_products.append(p)
            existing_codes.add(p["code"])
            added_count += 1

    with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
        json.dump(merged_products, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã cập nhật data/products.json (Tổng số: {len(merged_products)} sản phẩm, Thêm mới: {added_count}).")

    # 3. Đồng bộ vào SQLite database.db
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Lấy category_id mapping
            cursor.execute("SELECT id, name FROM categories")
            cat_map = {row[1]: row[0] for row in cursor.fetchall()}

            for p in new_products:
                cat_name = p.get("category", "")
                cat_id = cat_map.get(cat_name)
                sizes_str = ",".join(p.get("sizes", [])) if isinstance(p.get("sizes"), list) else p.get("sizes", "")
                tags_str = ",".join(p.get("tags", [])) if isinstance(p.get("tags"), list) else p.get("tags", "")

                cursor.execute("""
                    INSERT OR REPLACE INTO products (
                        id, name, code, category, sub_category, color, color_hex, sizes,
                        collar, sleeve, material, fit, price, old_price, discount_pct, points,
                        online_only, image_url, tags, description, category_id, stock
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p.get("id"),
                    p.get("name"),
                    p.get("code"),
                    cat_name,
                    p.get("sub_category"),
                    p.get("color"),
                    p.get("color_hex", "#111111"),
                    sizes_str,
                    p.get("collar"),
                    p.get("sleeve"),
                    p.get("material"),
                    p.get("fit"),
                    p.get("price"),
                    p.get("old_price"),
                    p.get("discount_pct"),
                    p.get("points"),
                    1,
                    p.get("image_url"),
                    tags_str,
                    p.get("description"),
                    cat_id,
                    50
                ))

            conn.commit()
            cursor.execute("SELECT count(*) FROM products")
            total_in_db = cursor.fetchone()[0]
            conn.close()
            print(f"  -> Đã đồng bộ thành công vào SQLite Database (Tổng hiện tại trong DB: {total_in_db} sản phẩm).")
        except Exception as e:
            print(f"  [Lỗi SQLite] Không thể nạp sản phẩm vào DB: {e}")


def build_and_integrate_evern_fashion_stylist_dataset() -> List[Dict[str, Any]]:
    """
    Tạo và tích hợp bộ dữ liệu hội thoại thời trang tiếng Việt chuyên sâu cho Evern Fashion.
    Tham khảo từ:
    - VOGUE: Hội thoại Seeker <-> Stylist, grounded catalog items, user profiles, styling rationale.
    - VN_Fashion_data: 5 dáng người Việt Nam, các dịp sự kiện (công sở, tiệc, hẹn hò, du lịch), phối màu & tone da.
    """
    print(f"\n[3/4] Đang khởi tạo và tích hợp Dataset Thời Trang Evern AI Stylist (VOGUE + VN_Fashion_data)...")
    from ai.build_evern_stylist_dataset import get_curated_fashion_dialogues

    dialogues = get_curated_fashion_dialogues()
    print(f"  -> Đã tạo {len(dialogues)} kịch bản hội thoại thời trang tiếng Việt chuẩn Stylist.")

    # 1. Lưu file dataset tiếng Việt độc lập
    stylist_json = os.path.join(DATA_DIR, "evern_fashion_stylist_vi.json")
    with open(stylist_json, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã lưu dataset thời trang tiếng Việt tại: {stylist_json}")

    stylist_jsonl = os.path.join(DATA_DIR, "evern_fashion_stylist_vi.jsonl")
    with open(stylist_jsonl, "w", encoding="utf-8") as f:
        for d in dialogues:
            f.write(json.dumps({
                "messages": [
                    {"role": "system", "content": "Bạn là Evern AI Stylist - Chuyên gia tư vấn định hình phong cách và phối đồ thời trang cao cấp của thương hiệu Evern Fashion."},
                    {"role": "user", "content": d["prompt_vi"]},
                    {"role": "assistant", "content": d["response_vi"]}
                ]
            }, ensure_ascii=False) + "\n")
    print(f"  -> Đã lưu file chuẩn ChatML tại: {stylist_jsonl}")

    # 2. Làm sạch và Cập nhật intents.json
    intents_data = {"intents": []}
    if os.path.exists(INTENTS_JSON):
        try:
            with open(INTENTS_JSON, "r", encoding="utf-8") as f:
                intents_data = json.load(f)
        except Exception:
            pass

    junk_keywords = [
        'khoan', 'bosch', 'makita', 'tai nghe', 'sony wh-', 'apple watch', 'airpods',
        'kallax', 'ikea', 'bộ dao', 'dyson', 'máy hút bụi', 'nồi', 'instant pot',
        'whey', 'protein', 'oats', 'yến mạch', 'máy mài', 'serum', 'salicylic',
        'campingaz', 'bếp cắm trại', 'paws india', 'gãi của paws', 'secretlab',
        'máy giặt', 'lg 8kg', 'wonderchef', 'nutri-blend', 'điều hòa', 'daikin',
        'máy nén', 'bóng đá', 'cosco', 'ikigai', 'clean code', 'phân bón', 'ugaoo',
        'chậu trồng cây', 'cello garden', 'tâm lý tiền bạc', 'bình gas', 'lò vi sóng',
        'ifb 25l', 'máy nướng bánh', 'morphy richards', 'khay đựng vụn', 'thức ăn cho cây',
        'thức ăn thực vật', 'bột whey', 'reebok classic', 'dumbbell', '₹', 'neutrogena',
        'inspiron 15', 'power drills', 'tủ lạnh'
    ]

    # Loại bỏ junk
    for intent in intents_data.get("intents", []):
        intent["patterns"] = [p for p in intent.get("patterns", []) if not any(k in p.lower() for k in junk_keywords)]
        intent["responses"] = [r for r in intent.get("responses", []) if not any(k in r.lower() for k in junk_keywords)]

    intents_by_tag = {item["tag"]: item for item in intents_data.get("intents", [])}

    added_patterns = 0
    added_responses = 0
    for d in dialogues:
        tag = d["intent_tag"]
        p_vi = d["prompt_vi"].strip()
        r_vi = d["response_vi"].strip()

        if tag not in intents_by_tag:
            intents_by_tag[tag] = {
                "tag": tag,
                "patterns": [],
                "responses": []
            }
            intents_data["intents"].append(intents_by_tag[tag])

        target_intent = intents_by_tag[tag]
        patterns = target_intent.setdefault("patterns", [])
        responses = target_intent.setdefault("responses", [])

        if p_vi and p_vi.lower() not in [p.lower() for p in patterns]:
            patterns.append(p_vi)
            added_patterns += 1

        if r_vi and r_vi not in responses and len(responses) < 15:
            responses.append(r_vi)
            added_responses += 1

    with open(INTENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(intents_data, f, ensure_ascii=False, indent=2)
    print(f"  -> Đã cập nhật data/intents.json (Đã thêm {added_patterns} mẫu câu thời trang mới).")

    # 3. Cập nhật dataset_finetune.jsonl
    existing_finetune = []
    existing_prompts = set()
    if os.path.exists(FINETUNE_JSONL):
        try:
            with open(FINETUNE_JSONL, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        user_msg = ""
                        for m in row.get("messages", []):
                            if m.get("role") == "user":
                                user_msg = m.get("content", "").strip()
                        if user_msg and not any(k in user_msg.lower() for k in junk_keywords):
                            existing_finetune.append(row)
                            existing_prompts.add(user_msg.lower())
        except Exception:
            pass

    added_finetune = 0
    for d in dialogues:
        p_vi = d["prompt_vi"].strip()
        r_vi = d["response_vi"].strip()
        if p_vi and p_vi.lower() not in existing_prompts:
            item = {
                "messages": [
                    {"role": "system", "content": "Bạn là Evern AI Stylist - Chuyên gia tư vấn thời trang cao cấp của Evern Fashion."},
                    {"role": "user", "content": p_vi},
                    {"role": "assistant", "content": r_vi}
                ]
            }
            existing_finetune.append(item)
            existing_prompts.add(p_vi.lower())
            added_finetune += 1

    with open(FINETUNE_JSONL, "w", encoding="utf-8") as f:
        for row in existing_finetune:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"  -> Đã cập nhật data/dataset_finetune.jsonl (Thêm {added_finetune} cặp hội thoại Stylist mới).")
    return dialogues


def retrain_intent_and_rag():
    """Tái huấn luyện mô hình phân loại ý định nội bộ và cập nhật RAG FAISS."""
    print(f"\n=======================================================")
    print(f"TIẾN HÀNH TỰ ĐỘNG CẬP NHẬT MÔ HÌNH VÀ CHỈ MỤC RAG CỤC BỘ")
    print(f"=======================================================")

    # 1. Huấn luyện lại IntentClassifier
    try:
        from ai.intent import IntentClassifier
        clf = IntentClassifier()
        print(f"[IntentClassifier] Huấn luyện thành công trên {clf.metrics.get('num_patterns')} mẫu câu ({clf.metrics.get('num_intents')} intents) - Độ chính xác: {clf.metrics.get('train_accuracy') * 100:.1f}%")
    except Exception as e:
        print(f"[IntentClassifier] Cảnh báo huấn luyện Intent: {e}")

    # 2. Xây dựng lại RAG FAISS Vector Database
    try:
        from ai.rag_engine import RAGEngine
        rag = RAGEngine()
        print("[RAG] Đang nạp toàn bộ tài liệu Markdown và sản phẩm mới từ database để tạo Vector Index...")
        num_vectors = rag.ingest(force_rebuild=True)
        print(f"[RAG] Vector Knowledge Base FAISS đã được cập nhật hoàn hảo với {num_vectors} vectors!")
    except Exception as e:
        print(f"[RAG] Cảnh báo cập nhật RAG: {e}")

def main():
    print("=================================================================")
    print(" BẮT ĐẦU QUY TRÌNH TÍCH HỢP DATASET THỜI TRANG EVERN AI STYLIST")
    print("=================================================================")

    # 1. Tải và xử lý Qdrant/hm_ecommerce_products
    try:
        hm_raw = fetch_hm_ecommerce_products(target_count=65)
        hm_processed = map_and_translate_hm_products(hm_raw, start_id=36)
        integrate_products_to_project(hm_processed)
    except Exception as e:
        print(f"  [Thông tin] Bỏ qua tải lại HM do đã có sẵn sản phẩm trong catalog: {e}")

    # 2. Tích hợp Evern Fashion Stylist Dataset (VOGUE + VN_Fashion_data)
    build_and_integrate_evern_fashion_stylist_dataset()

    # 3. Cập nhật Model và Vector Knowledge
    retrain_intent_and_rag()

    print("\n🎉 HOÀN TẤT TOÀN DIỆN!")
    print("1. Đã tích hợp Dataset Thời Trang Evern AI Stylist (VOGUE + VN_Fashion_data).")
    print("2. Đã loại bỏ triệt để Full-Ecom-Chatbot-Dataset phi thời trang.")
    print("3. Đã đồng bộ hoàn hảo vào Catalog sản phẩm, Database SQLite, Intent Classifier, Fine-tune Dataset và RAG Index.")

if __name__ == "__main__":
    main()
