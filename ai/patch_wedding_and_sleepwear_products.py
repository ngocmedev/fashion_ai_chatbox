# -*- coding: utf-8 -*-
"""
Script cập nhật danh mục sản phẩm váy ngủ và bổ sung đầm dạ hội / tiệc cưới sang trọng
cho Evern Fashion nhằm phục vụ chuẩn xác dress code sự kiện (đám cưới 5 sao, dạ tiệc).
"""
import sqlite3
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'database/database.db'
PRODUCTS_JSON = 'data/products.json'

NEW_WEDDING_DRESSES = [
    {
        "id": 102,
        "code": "DM260101",
        "name": "Đầm Xoè Midi Phối Ren Dự Tiệc Cao Cấp (Hồng Pastel)",
        "category": "Váy & Đầm",
        "sub_category": "đầm dạ hội / đầm tiệc cưới",
        "color": "hồng pastel",
        "color_hex": "#F4C2C2",
        "sizes": ["S", "M", "L"],
        "price": 890000,
        "old_price": 1150000,
        "discount_pct": 23,
        "points": 890,
        "stock": 35,
        "collar": "Cổ vuông thanh lịch",
        "sleeve": "Tay con bồng nhẹ",
        "material": "Ren thêu hoa cao cấp phối lụa tơ tằm",
        "fit": "Dáng xoè chữ A thon gọn eo",
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600&auto=format&fit=crop&q=80",
        "tags": "đầm đi tiệc, đầm đám cưới, đầm dự tiệc, váy đi tiệc, đầm sang trọng, khách sạn 5 sao, váy dạ hội, tôn dáng, thanh lịch",
        "description": "Đầm midi dáng chữ A thanh lịch với chất liệu ren thêu hoa phối lụa mềm mại, cổ vuông kín đáo trang nhã, tone màu hồng pastel dịu dàng chuẩn dress code đám cưới sang trọng tại khách sạn 5 sao mà không lấn át cô dâu.",
        "category_id": 5,
        "online_only": 0,
        "images": ["https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600&auto=format&fit=crop&q=80"]
    },
    {
        "id": 103,
        "code": "DM260102",
        "name": "Đầm Lụa Tơ Tằm Cổ Đổ Quý Phái (Xanh Mint Pastel)",
        "category": "Váy & Đầm",
        "sub_category": "đầm dạ hội / đầm tiệc cưới",
        "color": "xanh pastel",
        "color_hex": "#A2D2BF",
        "sizes": ["S", "M", "L"],
        "price": 950000,
        "old_price": 1280000,
        "discount_pct": 26,
        "points": 950,
        "stock": 28,
        "collar": "Cổ đổ quyến rũ",
        "sleeve": "Sát nách tinh tế",
        "material": "Lụa tơ tằm óng ả mềm rủ",
        "fit": "Phom suông chiết eo nhẹ tôn dáng",
        "image_url": "https://images.unsplash.com/photo-1518049362265-d5b2a6467637?w=600&auto=format&fit=crop&q=80",
        "tags": "đầm đám cưới, đầm đi tiệc, đầm lụa, đầm dạ hội, váy dự tiệc sang trọng, khách sạn 5 sao, quiet luxury, thanh lịch",
        "description": "Đầm lụa tơ tằm mềm rủ cao cấp, phom suông chiết eo nhẹ nhàng, tone màu xanh pastel dịu mắt quý phái chuẩn phong cách Quiet Luxury dành riêng cho các sự kiện tiệc tối và đám cưới sang trọng.",
        "category_id": 5,
        "online_only": 0,
        "images": ["https://images.unsplash.com/photo-1518049362265-d5b2a6467637?w=600&auto=format&fit=crop&q=80"]
    }
]

def update_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Cập nhật sub_category cho 2 mẫu váy ngủ để phân biệt rạch ròi với đầm đi tiệc
    c.execute("""
        UPDATE products 
        SET sub_category = 'váy ngủ / đồ mặc nhà',
            tags = 'váy ngủ, đồ ngủ lụa, đồ mặc nhà, pijama lụa, lụa satin cao cấp, quyến rũ, thoải mái'
        WHERE code IN ('HM661022', 'HM661025')
    """)
    print(f"Cập nhật sub_category cho váy ngủ: {c.rowcount} dòng")

    # 2. Cập nhật sản phẩm Đầm Lụa Cổ Đổ tiệc cưới hiện có
    c.execute("""
        UPDATE products
        SET sub_category = 'đầm dạ hội / đầm tiệc cưới',
            tags = 'đầm dạ hội, đầm dự tiệc, đầm đi tiệc, đầm đám cưới, đầm lụa cổ đổ, sang trọng, quyến rũ, khách sạn 5 sao'
        WHERE code = 'DM258810'
    """)

    # 3. Thêm 2 mẫu đầm dạ hội tiệc cưới mới nếu chưa có
    for p in NEW_WEDDING_DRESSES:
        c.execute("SELECT id FROM products WHERE code = ?", (p["code"],))
        if not c.fetchone():
            c.execute("""
                INSERT INTO products (
                    id, code, name, category, sub_category, color, color_hex,
                    sizes, price, old_price, discount_pct, points, stock,
                    collar, sleeve, material, fit, image_url, tags, description,
                    category_id, online_only, images
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, (
                p["id"], p["code"], p["name"], p["category"], p["sub_category"], p["color"], p["color_hex"],
                ",".join(p["sizes"]), p["price"], p["old_price"], p["discount_pct"], p["points"], p["stock"],
                p["collar"], p["sleeve"], p["material"], p["fit"], p["image_url"], p["tags"], p["description"],
                p["category_id"], p["online_only"], json.dumps(p["images"])
            ))
            print(f"Đã thêm mới đầm tiệc cưới: {p['name']} ({p['code']})")

    conn.commit()
    conn.close()

def update_json():
    if os.path.exists(PRODUCTS_JSON):
        with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
            prods = json.load(f)

        existing_codes = {p.get("code") for p in prods}
        for p in prods:
            if p.get("code") in ["HM661022", "HM661025"]:
                p["sub_category"] = "váy ngủ / đồ mặc nhà"
                p["tags"] = ["váy ngủ", "đồ ngủ lụa", "đồ mặc nhà", "pijama lụa", "lụa satin cao cấp", "quyến rũ", "thoải mái"]
            elif p.get("code") == "DM258810":
                p["sub_category"] = "đầm dạ hội / đầm tiệc cưới"

        for new_p in NEW_WEDDING_DRESSES:
            if new_p["code"] not in existing_codes:
                prods.append(new_p)
                print(f"Đã thêm vào products.json: {new_p['code']}")

        with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
            json.dump(prods, f, ensure_ascii=False, indent=2)
        print("Đã cập nhật products.json thành công!")

if __name__ == "__main__":
    update_db()
    update_json()
    print("Hoàn tất phân tách váy ngủ và đầm tiệc cưới!")
