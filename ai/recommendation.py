import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")

class FashionRecommender:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.create_function("py_lower", 1, lambda s: str(s).lower() if s is not None else "")
        return conn

    def get_all_products(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def recommend(self, entities, limit=4):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM products WHERE 1=1"
        params = []
        gender = entities.get("gender") if entities else None
        if gender and gender.lower() == "nam":
            query += (
                " AND py_lower(category) NOT IN ('váy & đầm', 'đầm', 'chân váy')"
                " AND (py_lower(name) NOT LIKE '% nữ%' AND py_lower(name) NOT LIKE '%nữ %' AND py_lower(name) NOT LIKE '%(nữ)%' OR py_lower(name) LIKE '%nam nữ%' OR py_lower(name) LIKE '%unisex%')"
                " AND py_lower(name) NOT LIKE '%quần tất%'"
                " AND py_lower(name) NOT LIKE '%quần legging%'"
                " AND py_lower(name) NOT LIKE '%kẹp tóc%'"
                " AND py_lower(name) NOT LIKE '%chun buộc tóc%'"
                " AND py_lower(name) NOT LIKE '%siết eo%'"
                " AND py_lower(name) NOT LIKE '%hai dây%'"
                " AND py_lower(name) NOT LIKE '%2 dây%'"
                " AND py_lower(name) NOT LIKE '%camisole%'"
                " AND py_lower(name) NOT LIKE '%croptop%'"
                " AND py_lower(name) NOT LIKE '%crop top%'"
                " AND py_lower(name) NOT LIKE '%trễ vai%'"
                " AND py_lower(name) NOT LIKE '%váy%'"
                " AND py_lower(name) NOT LIKE '%đầm%'"
                " AND py_lower(name) NOT LIKE '%chân váy%'"
                " AND py_lower(name) NOT LIKE '%babette%'"
                " AND py_lower(name) NOT LIKE '%tiểu thư%'"
                " AND py_lower(name) NOT LIKE '%nữ tính%'"
                " AND py_lower(name) NOT LIKE '%hở lưng%'"
                " AND py_lower(name) NOT LIKE '%peplum%'"
                " AND py_lower(name) NOT LIKE '%babydoll%'"
                " AND (py_lower(tags) NOT LIKE '%thời trang nữ%' AND py_lower(tags) NOT LIKE '%dành cho nữ%' OR py_lower(tags) LIKE '%unisex%')"
            )
        elif gender and gender.lower() == "nữ":
            query += (
                " AND (py_lower(name) NOT LIKE '% nam%' AND py_lower(name) NOT LIKE '%nam %' AND py_lower(name) NOT LIKE '%(nam)%' OR py_lower(name) LIKE '%nam nữ%' OR py_lower(name) LIKE '%unisex%')"
                " AND py_lower(name) NOT LIKE '%quý ông%'"
                " AND py_lower(name) NOT LIKE '%cà vạt%'"
                " AND py_lower(name) NOT LIKE '%ví da nam%'"
                " AND (py_lower(tags) NOT LIKE '%thời trang nam%' OR py_lower(tags) LIKE '%unisex%')"
            )

        if entities.get("category"):
            query += " AND category LIKE ?"
            params.append(f"%{entities['category']}%")

        if entities.get("color"):
            query += " AND color LIKE ?"
            params.append(f"%{entities['color']}%")

        if entities.get("max_price"):
            query += " AND price <= ?"
            params.append(entities["max_price"])

        if entities.get("size"):
            query += " AND sizes LIKE ?"
            params.append(f"%{entities['size']}%")

        if entities.get("occasion"):
            query += " AND (tags LIKE ? OR description LIKE ?)"
            params.append(f"%{entities['occasion']}%")
            params.append(f"%{entities['occasion']}%")

        query += f" LIMIT {limit}"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = [dict(row) for row in rows]

        # If strict search returned nothing, relax constraints
        if not results and (entities.get("category") or entities.get("occasion") or entities.get("color")):
            relax_query = "SELECT * FROM products WHERE 1=0"
            relax_params = []

            if entities.get("category"):
                relax_query += " OR category LIKE ?"
                relax_params.append(f"%{entities['category']}%")

            if entities.get("occasion"):
                relax_query += " OR tags LIKE ?"
                relax_params.append(f"%{entities['occasion']}%")

            if entities.get("color"):
                relax_query += " OR color LIKE ?"
                relax_params.append(f"%{entities['color']}%")

            relax_query += f" LIMIT {limit}"
            cursor.execute(relax_query, relax_params)
            results = [dict(row) for row in cursor.fetchall()]

        # If still empty, return top featured products
        if not results:
            cursor.execute(f"SELECT * FROM products ORDER BY price DESC LIMIT {limit}")
            results = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Format lists from comma-separated strings
        for item in results:
            if isinstance(item.get("sizes"), str):
                item["sizes"] = [s.strip() for s in item["sizes"].split(",") if s.strip()]
            if isinstance(item.get("tags"), str):
                item["tags"] = [t.strip() for t in item["tags"].split(",") if t.strip()]

        return results

    def recommend_outfit(self, user_message: str = "", entities: dict = None, limit: int = 4):
        """
        Gợi ý trọn bộ Outfit hài hòa gồm Áo (Top) + Quần (Bottom) + Giày/Khoác/Phụ kiện
        theo giới tính (Nữ / Nam), thời tiết và dịp mặc (date, tết, tiệc, công sở, đi chơi).
        Sử dụng cơ chế lọc linh hoạt và RANDOM để đảm bảo mỗi lần gợi ý đều tươi mới, không trùng lặp.
        """
        import random
        entities = entities or {}
        msg_lower = (user_message or "").lower()
        occasion = entities.get("occasion") or ""
        weather = entities.get("weather") or ""
        gender = entities.get("gender") or ""

        # 1. Nhận diện giới tính
        if not gender:
            if any(w in msg_lower for w in ["nữ", "con gái", "bạn gái", "phái đẹp", "chị em", "nàng", "cho nữ"]):
                gender = "nữ"
            elif any(w in msg_lower for w in ["nam", "con trai", "bạn trai", "phái mạnh", "anh em", "chàng", "cho nam"]):
                gender = "nam"

        # 2. Nhận diện mùa và thời tiết
        season = entities.get("season") or ""
        if not season:
            if any(w in msg_lower for w in ["mùa xuân", "tiết xuân", "ngày xuân", "du xuân", "xuân"]):
                season = "mùa xuân"
            elif any(w in msg_lower for w in ["mùa hè", "mùa hạ", "ngày hè", "hè", "nóng", "oi bức", "nắng"]):
                season = "mùa hè"
            elif any(w in msg_lower for w in ["mùa thu", "ngày thu", "trời thu", "tiết thu", "thu"]):
                season = "mùa thu"
            elif any(w in msg_lower for w in ["mùa đông", "ngày đông", "trời đông", "tiết đông", "đông", "lạnh", "rét"]):
                season = "mùa đông"

        if not weather:
            if season == "mùa đông" or any(w in msg_lower for w in ["lạnh", "rét", "buốt"]):
                weather = "mùa đông"
            elif season == "mùa hè" or any(w in msg_lower for w in ["nóng", "nắng", "oi bức"]):
                weather = "mùa hè"
            elif season in ["mùa thu", "mùa xuân"] or any(w in msg_lower for w in ["mát mẻ", "mát", "se lạnh"]):
                weather = "mát mẻ"

        # 3. Nhận diện và chuẩn hoá dịp sử dụng (Occasion)
        occ_check = f"{occasion} {msg_lower}".lower()
        if any(x in occ_check for x in ["concert", "sơn tùng", "âm nhạc", "music festival", "festival", "quẩy", "show diễn", "liveshow"]):
            occasion = "concert"
        elif any(x in occ_check for x in ["date", "hẹn hò", "crush", "người yêu"]):
            occasion = "hẹn hò"
        elif any(x in occ_check for x in ["tết", "du xuân", "năm mới", "chúc tết", "quần áo tết"]):
            occasion = "tết"
        elif any(x in occ_check for x in ["du lịch", "đài loan", "hàn quốc", "nhật bản", "sapa", "đà lạt", "đi biển", "phượt", "camping"]):
            occasion = "du lịch"
            if not weather:
                weather = "se lạnh"
        elif any(x in occ_check for x in ["sinh nhật", "party"]):
            occasion = "tiệc sinh nhật"
        elif any(x in occ_check for x in ["tiệc", "cưới", "dạ hội", "prom", "gala", "sự kiện"]):
            occasion = "dự tiệc"
        elif any(x in occ_check for x in ["công sở", "đi làm", "văn phòng", "đối tác", "phỏng vấn", "họp"]):
            occasion = "công sở"
        elif any(x in occ_check for x in ["đi chơi", "dạo phố", "cafe", "cà phê", "cuối tuần", "chủ nhật"]):
            occasion = "đi chơi"

        conn = self.get_connection()
        cursor = conn.cursor()
        outfit = []

        # Điều kiện loại trừ các sản phẩm đồ lót, set áo lót nhiều cái, đồ ngủ, legging, jogger, đồ nỉ
        not_suitable = "AND name NOT LIKE '%set %' AND name NOT LIKE '%áo lót%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%body cotton co giãn%' AND name NOT LIKE '%tất%' AND name NOT LIKE '%váy ngủ%' AND name NOT LIKE '%đồ ngủ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%jogger%' AND name NOT LIKE '%nỉ thể thao%' AND name NOT LIKE '%thể thao%'"

        male_excluded = (
            "AND py_lower(category) NOT IN ('váy & đầm', 'đầm', 'chân váy')"
            " AND (py_lower(name) NOT LIKE '% nữ%' AND py_lower(name) NOT LIKE '%nữ %' AND py_lower(name) NOT LIKE '%(nữ)%' OR py_lower(name) LIKE '%nam nữ%' OR py_lower(name) LIKE '%unisex%')"
            " AND py_lower(name) NOT LIKE '%quần tất%'"
            " AND py_lower(name) NOT LIKE '%quần legging%'"
            " AND py_lower(name) NOT LIKE '%hai dây%'"
            " AND py_lower(name) NOT LIKE '%2 dây%'"
            " AND py_lower(name) NOT LIKE '%camisole%'"
            " AND py_lower(name) NOT LIKE '%croptop%'"
            " AND py_lower(name) NOT LIKE '%crop top%'"
            " AND py_lower(name) NOT LIKE '%trễ vai%'"
            " AND py_lower(name) NOT LIKE '%váy%'"
            " AND py_lower(name) NOT LIKE '%đầm%'"
            " AND py_lower(name) NOT LIKE '%chân váy%'"
            " AND py_lower(name) NOT LIKE '%babette%'"
            " AND py_lower(name) NOT LIKE '%tiểu thư%'"
            " AND py_lower(name) NOT LIKE '%nữ tính%'"
            " AND py_lower(name) NOT LIKE '%hở lưng%'"
            " AND py_lower(name) NOT LIKE '%peplum%'"
            " AND py_lower(name) NOT LIKE '%babydoll%'"
            " AND py_lower(name) NOT LIKE '%siết eo%'"
            " AND py_lower(name) NOT LIKE '%kẹp tóc%'"
            " AND py_lower(name) NOT LIKE '%chun buộc tóc%'"
            " AND (py_lower(tags) NOT LIKE '%thời trang nữ%' AND py_lower(tags) NOT LIKE '%dành cho nữ%' OR py_lower(tags) LIKE '%unisex%')"
        )

        is_budget = entities.get("is_budget_friendly") or any(w in msg_lower for w in ["túi tiền", "sinh viên", "tiết kiệm", "giá rẻ", "hạt dẻ", "ít tiền", "không có nhiều tiền", "vừa túi tiền", "hợp túi tiền"])
        order_sql = "ORDER BY price ASC LIMIT 1" if is_budget else "ORDER BY RANDOM() LIMIT 1"

        if gender == "nữ":
            if occasion == "concert":
                # Nữ đi concert: Áo croptop / Áo thun oversize / Áo khoác jeans + Quần loe / Quần jeans / Chân váy xếp ly + Giày sneaker
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        category = 'Áo thun phông' 
                        OR category = 'Áo thun' 
                        OR (category = 'Áo khoác' AND (name LIKE '%jeans%' OR name LIKE '%bomber%'))
                    )
                    AND name NOT LIKE '%váy ngủ%' AND name NOT LIKE '%đồ ngủ%'
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category = 'Quần loe' OR category = 'Quần jean' OR (category = 'Váy & Đầm' AND name LIKE '%chân váy%'))
                      AND name NOT LIKE '%tất%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' 
                      AND (name LIKE '%sneaker%' OR name LIKE '%giày%' OR name LIKE '%kính%')
                      AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            # Dịp: Đi date, Hẹn hò, Tết, Du xuân, Dự tiệc, Sinh nhật, Du lịch
            elif occasion in ["hẹn hò", "tết", "dự tiệc", "tiệc sinh nhật", "du lịch"]:
                # Chọn ĐẦM LIỀN THIẾT KẾ sang trọng hoặc SET CHÂN VÁY / QUẦN LOE + ÁO KIỂU
                use_dress = random.choice([True, False])
                if use_dress:
                    # 1. Đầm thiết kế cao cấp (Đầm Lụa Satin, Đầm Xòe Phối Ren, Đầm Lụa Tơ Tằm)
                    cursor.execute("""
                        SELECT * FROM products 
                        WHERE category = 'Váy & Đầm' 
                          AND name NOT LIKE '%váy ngủ%' AND name NOT LIKE '%đồ ngủ%'
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        outfit.append(dict(row))

                    # 2. Áo khoác ngoài thanh lịch (Blazer / Cardigan)
                    exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE category = 'Áo khoác' 
                          AND (sub_category LIKE '%blazer%' OR name LIKE '%blazer%' OR name LIKE '%cardigan%' OR tags LIKE '%trẻ trung%')
                          AND name NOT LIKE '%suit%' AND name NOT LIKE '%quý ông%' AND tags NOT LIKE '%nam%'
                          AND id NOT IN ({exclude_ids})
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        outfit.append(dict(row))

                    # 3. Phụ kiện: Kẹp tóc Hàn Quốc hoặc Giày hoặc Kính mát
                    exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE category = 'Phụ kiện' 
                          AND (name LIKE '%kẹp tóc%' OR name LIKE '%giày%' OR name LIKE '%kính%' OR name LIKE '%chun buộc tóc%')
                          AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                          AND id NOT IN ({exclude_ids})
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        outfit.append(dict(row))
                else:
                    # Set Áo Sơ mi lụa / Polo + Chân váy xếp ly / Quần ống loe
                    # 1. Áo (Top)
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE (category = 'Áo sơ mi' OR (category = 'Áo thun phông' AND tags LIKE '%trẻ trung%') OR category = 'Áo polo')
                          {not_suitable}
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        outfit.append(dict(row))

                    # 2. Chân váy hoặc Quần ống loe tôn dáng
                    exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE ((category = 'Váy & Đầm' AND name LIKE '%chân váy%') OR category = 'Quần loe' OR (category = 'Quần tây' AND name LIKE '%xếp ly%'))
                          {not_suitable}
                          AND id NOT IN ({exclude_ids})
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        outfit.append(dict(row))

                    # 3. Giày hoặc Phụ kiện kẹp tóc
                    exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE category = 'Phụ kiện' 
                          AND (name LIKE '%giày%' OR name LIKE '%kẹp tóc%' OR name LIKE '%kính%' OR name LIKE '%chun buộc tóc%')
                          AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                          AND id NOT IN ({exclude_ids})
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        outfit.append(dict(row))

            elif occasion == "công sở":
                # Nữ công sở: Áo sơ mi lụa / Sơ mi thanh lịch + Quần tây xếp ly hoặc Chân váy midi
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo sơ mi' {not_suitable}
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE ((category = 'Quần tây' AND name LIKE '%xếp ly%') OR (category = 'Váy & Đầm' AND name LIKE '%chân váy%') OR category = 'Quần loe')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' AND (name LIKE '%blazer%' OR sub_category LIKE '%blazer%')
                      AND name NOT LIKE '%suit%' AND name NOT LIKE '%quý ông%' AND tags NOT LIKE '%nam%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            elif season == "mùa đông":
                # Nữ mùa đông: Áo len cổ lọ / hoodie nỉ + Quần tây xếp ly Babette / Quần jeans + Áo măng tô / chần bông + Sneaker
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Len%' OR name LIKE '%Hoodie%' OR name LIKE '%Nỉ Giữ Nhiệt%')
                      AND category IN ('Áo khoác', 'Áo thun')
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Quần tây', 'Quần jean') AND name NOT LIKE '%short%')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Măng Tô%' OR name LIKE '%Chần Bông%' OR name LIKE '%Jeans%' OR name LIKE '%Biker%')
                      AND category = 'Áo khoác'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' AND (name LIKE '%sneaker%' OR name LIKE '%giày%')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            elif season == "mùa hè":
                # Nữ mùa hè: Áo hai dây lụa / croptop / thun cotton + Quần loe Y2K / Chân váy xếp ly + Kính mát titanium / kẹp tóc
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Hai Dây%' OR name LIKE '%Croptop%' OR (category = 'Áo thun phông' AND tags LIKE '%cotton%'))
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category = 'Quần loe' OR (category = 'Váy & Đầm' AND name LIKE '%chân váy%') OR category = 'Quần jean')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' AND (name LIKE '%kính mát%' OR name LIKE '%kẹp tóc%' OR name LIKE '%sneaker%')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            elif season == "mùa thu":
                # Nữ mùa thu: Sơ mi lụa dài tay / Áo thun dài tay + Quần tây xếp ly Babette / Chân váy midi + Cardigan len mỏng
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Sơ Mi Lụa%' OR name LIKE '%Dài Tay%' OR (category = 'Áo sơ mi' AND name NOT LIKE '%nam%'))
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE ((category = 'Quần tây' AND name LIKE '%xếp ly%') OR (category = 'Váy & Đầm' AND name LIKE '%chân váy%'))
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Cardigan%' OR (category = 'Áo khoác' AND name LIKE '%mỏng%'))
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            elif season == "mùa xuân":
                # Nữ mùa xuân: Đầm ren pastel / Đầm lụa cổ đổ + Cardigan len mỏng + Kẹp tóc pastel
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE category = 'Váy & Đầm' AND (name LIKE '%Đầm Xoè%' OR name LIKE '%Đầm Lụa Tơ Tằm%' OR name LIKE '%chân váy%')
                      AND name NOT LIKE '%váy ngủ%'
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Cardigan%' OR (category = 'Áo khoác' AND sub_category LIKE '%blazer%'))
                      AND name NOT LIKE '%nam%' AND name NOT LIKE '%suit%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' AND (name LIKE '%kẹp tóc%' OR name LIKE '%chun buộc tóc%' OR name LIKE '%sneaker%')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            else:
                # Nữ đi chơi, dạo phố, thường ngày
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Áo thun phông', 'Áo polo') OR (category = 'Áo sơ mi' AND tags LIKE '%trẻ trung%'))
                      {not_suitable}
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Quần loe', 'Quần jean') OR (category = 'Váy & Đầm' AND name LIKE '%chân váy%') OR category = 'Quần tây')
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

                exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' 
                      AND (name LIKE '%giày%' OR name LIKE '%kẹp tóc%' OR name LIKE '%kính%' OR name LIKE '%chun buộc tóc%')
                      AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

        else:
            # 1. CHỌN ÁO (TOP)
            if occasion == "concert":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Áo thun phông' AND name NOT LIKE '%set %' AND name NOT LIKE '%ba lỗ%')
                        OR (category = 'Áo khoác' AND (name LIKE '%jeans%' OR name LIKE '%bomber%' OR name LIKE '%biker%') AND name NOT LIKE '%suit%')
                    )
                    AND name NOT LIKE '%sơ mi%' AND name NOT LIKE '%công sở%'
                    {male_excluded}
                    ORDER BY (CASE WHEN category = 'Áo thun phông' THEN 1 ELSE 2 END) ASC, RANDOM() LIMIT 1
                """)
            elif occasion in ["tết", "dự tiệc", "tiệc sinh nhật"]:
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Áo sơ mi', 'Áo polo') OR (category = 'Áo thun phông' AND tags LIKE '%trẻ trung%'))
                      {not_suitable} {male_excluded}
                    ORDER BY (CASE WHEN category = 'Áo sơ mi' THEN 1 WHEN category = 'Áo polo' THEN 2 ELSE 3 END) ASC, RANDOM() LIMIT 1
                """)
            elif occasion == "hẹn hò":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Áo polo', 'Áo sơ mi') OR (category = 'Áo thun phông' AND tags LIKE '%trẻ trung%'))
                      {not_suitable} {male_excluded}
                    ORDER BY RANDOM() LIMIT 1
                """)
            elif occasion == "công sở":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo sơ mi' {not_suitable} {male_excluded}
                    ORDER BY RANDOM() LIMIT 1
                """)
            elif season == "mùa đông" or weather == "mùa đông":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (name LIKE '%Len%' OR name LIKE '%Hoodie%' OR name LIKE '%Dài Tay%' OR category = 'Áo khoác')
                      {not_suitable} {male_excluded}
                    ORDER BY RANDOM() LIMIT 1
                """)
            elif season == "mùa hè" or weather == "mùa hè":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Áo thun phông' AND tags LIKE '%cotton%')
                        OR (category = 'Áo polo' AND (name LIKE '%Nano%' OR tags LIKE '%nano%'))
                        OR (category = 'Áo sơ mi' AND (name LIKE '%Cuba%' OR name LIKE '%Cộc Tay%' OR name LIKE '%Ngắn Tay%'))
                    )
                    {not_suitable} {male_excluded}
                    ORDER BY RANDOM() LIMIT 1
                """)
            elif season == "mùa thu":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Áo sơ mi' AND (tags LIKE '%bamboo%' OR tags LIKE '%nano%' OR name LIKE '%Dài Tay%' OR name LIKE '%Caro%'))
                        OR (category = 'Áo polo' AND name LIKE '%Dệt Kim%')
                        OR (category = 'Áo thun' AND name LIKE '%Dài Tay%')
                    )
                    {not_suitable} {male_excluded}
                    ORDER BY RANDOM() LIMIT 1
                """)
            elif season == "mùa xuân":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Áo sơ mi' AND (name LIKE '%Cổ Tàu%' OR tags LIKE '%bamboo%'))
                        OR (category = 'Áo polo' AND name LIKE '%Dệt Kim%')
                    )
                    {not_suitable} {male_excluded}
                    ORDER BY RANDOM() LIMIT 1
                """)
            else: # Đi chơi, dạo phố
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Áo polo', 'Áo thun phông') OR (category = 'Áo sơ mi' AND tags LIKE '%trẻ trung%'))
                      {not_suitable} {male_excluded}
                    {order_sql}
                """)
            row = cursor.fetchone()
            if row:
                outfit.append(dict(row))

            # 2. CHỌN QUẦN (BOTTOM)
            exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
            if occasion == "concert":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category IN ('Quần jean', 'Quần loe') OR sub_category LIKE '%jeans%')
                        OR (category = 'Quần tây' AND (name LIKE '%jogger%' OR sub_category LIKE '%jogger%'))
                    )
                    AND name NOT LIKE '%công sở%' AND name NOT LIKE '%quần âu%' AND name NOT LIKE '%quần tây%' AND name NOT LIKE '%tất%'
                    {male_excluded}
                    AND id NOT IN ({exclude_ids})
                    ORDER BY (CASE WHEN category = 'Quần jean' THEN 1 ELSE 2 END) ASC, RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            elif occasion in ["tết", "tiệc sinh nhật", "công sở", "dự tiệc"]:
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Quần tây' 
                      AND (name LIKE '%quần tây%' OR name LIKE '%quần âu%' OR sub_category = 'quần âu' OR name LIKE '%xếp ly%')
                      AND name NOT LIKE '%jogger%' AND name NOT LIKE '%tất%' AND name NOT LIKE '%short%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if not row:
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE category IN ('Quần tây', 'Quần jean')
                          AND name NOT LIKE '%jogger%' AND name NOT LIKE '%tất%' AND name NOT LIKE '%short%'
                          {not_suitable} {male_excluded}
                          AND id NOT IN ({exclude_ids}) 
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
            elif occasion == "hẹn hò":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Quần tây', 'Quần jean') OR sub_category LIKE '%jeans%')
                      AND name NOT LIKE '%jogger%' AND name NOT LIKE '%tất%' AND name NOT LIKE '%short%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            elif season == "mùa hè" or weather == "mùa hè":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Quần tây' AND (sub_category LIKE '%short%' OR name LIKE '%short%'))
                        OR (category = 'Quần tây' AND (name LIKE '%Khaki%' OR name LIKE '%Chino%'))
                        OR (category = 'Quần jean')
                    )
                    AND name NOT LIKE '%nỉ%' AND name NOT LIKE '%tất%'
                    {not_suitable} {male_excluded}
                    AND id NOT IN ({exclude_ids})
                    ORDER BY (CASE WHEN sub_category LIKE '%short%' OR name LIKE '%short%' THEN 1 ELSE 2 END) ASC, RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            elif season == "mùa đông" or weather == "mùa đông":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Quần tây' AND (name LIKE '%Jogger%' OR name LIKE '%Nỉ%' OR sub_category = 'quần jogger'))
                        OR (category = 'Quần jean' AND sub_category LIKE '%jeans%')
                        OR (category = 'Quần tây' AND name LIKE '%quần âu%')
                    )
                    AND name NOT LIKE '%short%' AND name NOT LIKE '%tất%'
                    {not_suitable} {male_excluded}
                    AND id NOT IN ({exclude_ids})
                    ORDER BY (CASE WHEN name LIKE '%Jogger%' OR name LIKE '%Nỉ%' THEN 1 ELSE 2 END) ASC, RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            elif season == "mùa thu":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Quần tây' 
                      AND (name LIKE '%Slim Fit%' OR name LIKE '%Regular%' OR name LIKE '%Chino%')
                      AND name NOT LIKE '%short%' AND name NOT LIKE '%tất%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            elif season == "mùa xuân":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (
                        (category = 'Quần tây' AND (name LIKE '%Chino%' OR name LIKE '%Khaki%' OR name LIKE '%Ghi%'))
                        OR category = 'Quần jean'
                    )
                    AND name NOT LIKE '%short%' AND name NOT LIKE '%tất%'
                    {not_suitable} {male_excluded}
                    AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            else: # Đi chơi, dạo phố, du lịch
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE (category IN ('Quần jean', 'Quần loe') OR sub_category LIKE '%jeans%' OR (category = 'Quần tây' AND (name LIKE '%khaki%' OR name LIKE '%chino%' OR name LIKE '%short%'))) 
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids}) 
                    {order_sql}
                """)
                row = cursor.fetchone()
            if row:
                outfit.append(dict(row))

            # 3. KHOÁC NGOÀI (OUTERWEAR)
            exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
            if occasion == "concert":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (name LIKE '%jeans%' OR name LIKE '%biker%' OR name LIKE '%bomber%' OR sub_category LIKE '%bomber%')
                      AND name NOT LIKE '%suit%' AND tags NOT LIKE '%vest cưới%' AND tags NOT LIKE '%tiểu thư%' AND name NOT LIKE '%măng tô%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY (CASE WHEN name LIKE '%biker%' OR name LIKE '%jeans%' THEN 1 ELSE 2 END) ASC, RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif occasion in ["dự tiệc", "đám cưới", "tiệc cưới"]:
                # Tiệc cưới, sự kiện trang trọng: Cho phép Suit / Blazer sang trọng
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (sub_category LIKE '%blazer%' OR name LIKE '%suit%' OR name LIKE '%blazer%' OR tags LIKE '%lịch sự%' OR tags LIKE '%sang trọng%')
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    {order_sql}
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif occasion == "hẹn hò":
                # Hẹn hò: Cardigan len mỏng, Áo khoác dệt kim, Bomber hoặc Blazer casual trẻ trung (TUYỆT ĐỐI KHÔNG LẤY SUIT CƯỚI / VEST DOANH NHÂN)
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (name LIKE '%cardigan%' OR name LIKE '%dệt kim%' OR name LIKE '%bomber%' OR (sub_category LIKE '%blazer%' AND tags NOT LIKE '%vest cưới%' AND tags NOT LIKE '%doanh nhân%'))
                      AND name NOT LIKE '%suit%' AND tags NOT LIKE '%vest cưới%' AND tags NOT LIKE '%doanh nhân%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    {order_sql}
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif occasion in ["tết", "tiệc sinh nhật", "công sở", "du lịch"]:
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (sub_category LIKE '%blazer%' OR name LIKE '%blazer%' OR name LIKE '%cardigan%' OR name LIKE '%bomber%' OR name LIKE '%gió%' OR tags LIKE '%lịch sự%' OR tags LIKE '%trẻ trung%')
                      AND name NOT LIKE '%suit%' AND tags NOT LIKE '%vest cưới%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    {order_sql}
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif season == "mùa đông" or weather == "mùa đông":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (name LIKE '%Chần Bông%' OR name LIKE '%Jeans%' OR name LIKE '%Biker%' OR name LIKE '%Gió%')
                      AND name NOT LIKE '%suit%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY (CASE WHEN name LIKE '%Chần Bông%' THEN 1 WHEN name LIKE '%Jeans%' THEN 2 ELSE 3 END) ASC, RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif season == "mùa thu":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (name LIKE '%Cardigan%' OR name LIKE '%Gió%' OR name LIKE '%Bomber%')
                      AND name NOT LIKE '%suit%'
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif season == "mùa xuân":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (name LIKE '%Suit%' OR name LIKE '%Cardigan%')
                      {not_suitable} {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))
            elif weather in ["mát mẻ", "se lạnh"] or "mát" in msg_lower or "thu" in msg_lower:
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Áo khoác' 
                      AND (name LIKE '%gió%' OR name LIKE '%khoác%' OR tags LIKE '%gió%')
                      AND name NOT LIKE '%suit%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    outfit.append(dict(row))

            # 4. CHỌN GIÀY / PHỤ KIỆN (FOOTWEAR / ACCESSORIES)
            exclude_ids = ",".join(str(x["id"]) for x in outfit) if outfit else "0"
            if occasion in ["công sở", "dự tiệc"]:
                # Công sở, dự tiệc: Giày tây Oxford hoặc Giày da
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' 
                      AND (name LIKE '%giày tây%' OR name LIKE '%derby%' OR tags LIKE '%oxford%')
                      AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
                if not row:
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE category = 'Phụ kiện' 
                          AND (name LIKE '%thắt lưng%' OR name LIKE '%cà vạt%' OR name LIKE '%ví da%')
                          AND id NOT IN ({exclude_ids})
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
            elif season == "mùa hè":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' 
                      AND (name LIKE '%ZUNO%' OR name LIKE '%lưới%' OR name LIKE '%kính mát%' OR name LIKE '%sneaker%')
                      AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                      {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            elif season == "mùa đông":
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' 
                      AND (name LIKE '%da thật%' OR name LIKE '%sneaker%' OR name LIKE '%ví da%')
                      AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                      {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    ORDER BY RANDOM() LIMIT 1
                """)
                row = cursor.fetchone()
            else: # Đi date / Du lịch / Đi chơi: Ưu tiên Giày Sneaker retro êm chân
                cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE category = 'Phụ kiện' 
                      AND (name LIKE '%sneaker%' OR sub_category LIKE '%sneaker%')
                      AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                      {male_excluded}
                      AND id NOT IN ({exclude_ids})
                    {order_sql}
                """)
                row = cursor.fetchone()
                if not row:
                    cursor.execute(f"""
                        SELECT * FROM products 
                        WHERE category = 'Phụ kiện' 
                          AND (name LIKE '%kính%' OR name LIKE '%thắt lưng%' OR name LIKE '%giày%')
                          AND name NOT LIKE '%tất%' AND name NOT LIKE '%vớ%' AND name NOT LIKE '%legging%' AND name NOT LIKE '%ba lỗ%' AND name NOT LIKE '%dù%'
                          AND id NOT IN ({exclude_ids})
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    row = cursor.fetchone()
            if row:
                outfit.append(dict(row))

        # Format size và tags
        for item in outfit:
            if isinstance(item.get("sizes"), str):
                item["sizes"] = [s.strip() for s in item["sizes"].split(",") if s.strip()]
            if isinstance(item.get("tags"), str):
                item["tags"] = [t.strip() for t in item["tags"].split(",") if t.strip()]

        conn.close()
        return outfit[:limit]
