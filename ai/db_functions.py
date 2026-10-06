import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")

# Quản lý truy vấn cơ sở dữ liệu SQLite cho hệ thống
class FashionDBService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path # Đường dẫn file SQLite

    def _get_db(self):
        # Kết nối tới database và trả về hàng theo dạng dictionary
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.create_function("py_lower", 1, lambda s: str(s).lower() if s is not None else "")
        return conn

    def _format_product(self, row: sqlite3.Row) -> Dict[str, Any]:
        p = dict(row) # Ép kiểu hàng dữ liệu sang dictionary
        # Xử lý danh sách kích thước (size)
        if isinstance(p.get("sizes"), str):
            p["sizes"] = [s.strip() for s in p["sizes"].split(",") if s.strip()]
        elif not p.get("sizes"):
            p["sizes"] = ["S", "M", "L", "XL"]

        # Xử lý danh sách thẻ tìm kiếm (tags)
        if isinstance(p.get("tags"), str):
            p["tags"] = [t.strip() for t in p["tags"].split(",") if t.strip()]
        elif not p.get("tags"):
            p["tags"] = []

        # Đặt ảnh mặc định nếu sản phẩm chưa có ảnh
        if not p.get("image_url"):
            p["image_url"] = "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80"

        return p

    def search_products(
        self,
        query: str = "",
        category: str = "",
        sub_category: str = "",
        min_price: int = 0,
        max_price: int = 0,
        color: str = "",
        size: str = "",
        gender: str = "",
        style: str = "",
        material: str = "",
        limit: int = 6
    ) -> Tuple[List[Dict[str, Any]], str]:
        conn = self._get_db() # Mở kết nối CSDL
        cursor = conn.cursor()
        sql = "SELECT * FROM products WHERE 1=1" # Câu lệnh SQL cơ sở
        params = [] # Danh sách tham số an toàn

        # Lọc theo giới tính (nam / nữ)
        if gender and str(gender).strip().lower() == "nam":
            sql += (" AND py_lower(category) NOT IN ('váy & đầm', 'đầm', 'chân váy')"
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
                    " AND (py_lower(tags) NOT LIKE '%thời trang nữ%' AND py_lower(tags) NOT LIKE '%dành cho nữ%' OR py_lower(tags) LIKE '%unisex%')")
        elif gender and str(gender).strip().lower() == "nữ":
            sql += (" AND (py_lower(name) NOT LIKE '% nam%' AND py_lower(name) NOT LIKE '%nam %' AND py_lower(name) NOT LIKE '%(nam)%' OR py_lower(name) LIKE '%nam nữ%' OR py_lower(name) LIKE '%unisex%')"
                    " AND py_lower(name) NOT LIKE '%quý ông%'"
                    " AND py_lower(name) NOT LIKE '%cà vạt%'"
                    " AND py_lower(name) NOT LIKE '%ví da nam%'"
                    " AND (py_lower(tags) NOT LIKE '%thời trang nam%' OR py_lower(tags) LIKE '%unisex%')")

        # Lọc theo phong cách thời trang (style: douyin, korean, streetwear, y2k, vintage...)
        if style and str(style).strip():
            st_clean = str(style).strip().lower()
            if st_clean == "douyin":
                sql += " AND (py_lower(tags) LIKE '%douyin%' OR py_lower(tags) LIKE '%douying%' OR py_lower(name) LIKE '%douyin%' OR py_lower(description) LIKE '%douyin%' OR py_lower(tags) LIKE '%hot trend%' OR py_lower(tags) LIKE '%y2k%' OR py_lower(tags) LIKE '%trẻ trung%')"
            elif st_clean == "korean":
                sql += " AND (py_lower(tags) LIKE '%hàn quốc%' OR py_lower(tags) LIKE '%korean%' OR py_lower(name) LIKE '%hàn quốc%' OR py_lower(tags) LIKE '%trẻ trung%')"
            elif st_clean == "streetwear":
                sql += " AND (py_lower(tags) LIKE '%streetwear%' OR py_lower(tags) LIKE '%đường phố%' OR py_lower(tags) LIKE '%cool ngầu%' OR py_lower(tags) LIKE '%cá tính%')"
            else:
                sql += " AND (py_lower(tags) LIKE ? OR py_lower(name) LIKE ? OR py_lower(description) LIKE ?)"
                params.extend([f"%{st_clean}%", f"%{st_clean}%", f"%{st_clean}%"])

        # Lọc theo tiểu danh mục cụ thể (sub_category: quần loe, quần âu, quần short, quần khaki, blazer, áo sơ mi...)
        if sub_category and str(sub_category).strip():
            sc_clean = str(sub_category).strip().lower()
            if "loe" in sc_clean:
                sql += " AND (py_lower(sub_category) LIKE '%loe%' OR py_lower(name) LIKE '%loe%' OR py_lower(tags) LIKE '%loe%' OR py_lower(category) LIKE '%loe%')"
            elif "âu" in sc_clean or "tây" in sc_clean:
                sql += " AND (py_lower(sub_category) LIKE '%quần âu%' OR py_lower(name) LIKE '%quần âu%' OR py_lower(name) LIKE '%quần tây%') AND py_lower(sub_category) NOT LIKE '%short%'"
            elif "short" in sc_clean:
                sql += " AND (py_lower(sub_category) LIKE '%short%' OR py_lower(name) LIKE '%short%')"
            elif "kaki" in sc_clean or "khaki" in sc_clean:
                sql += " AND (py_lower(sub_category) LIKE '%khaki%' OR py_lower(name) LIKE '%khaki%' OR py_lower(tags) LIKE '%khaki%')"
            elif "suông" in sc_clean or "suong" in sc_clean:
                sql += " AND (py_lower(sub_category) LIKE '%suông%' OR py_lower(name) LIKE '%suông%' OR py_lower(tags) LIKE '%suông%')"
            elif "rộng" in sc_clean or "rong" in sc_clean:
                sql += " AND (py_lower(sub_category) LIKE '%rộng%' OR py_lower(name) LIKE '%rộng%' OR py_lower(tags) LIKE '%rộng%')"
            elif "jeans" in sc_clean or "jean" in sc_clean:
                if "khoác" in sc_clean:
                    sql += " AND (py_lower(name) LIKE '%khoác%' OR py_lower(category) LIKE '%khoác%') AND (py_lower(name) LIKE '%jean%' OR py_lower(tags) LIKE '%jean%')"
                else:
                    sql += " AND (py_lower(sub_category) LIKE '%jean%' OR py_lower(name) LIKE '%jean%' OR py_lower(tags) LIKE '%jean%')"
            elif "hoodie" in sc_clean:
                sql += " AND (py_lower(name) LIKE '%hoodie%' OR py_lower(tags) LIKE '%hoodie%')"
            elif "bomber" in sc_clean:
                sql += " AND (py_lower(name) LIKE '%bomber%' OR py_lower(tags) LIKE '%bomber%')"
            elif "gió" in sc_clean or "windbreaker" in sc_clean:
                sql += " AND (py_lower(name) LIKE '%gió%' OR py_lower(tags) LIKE '%gió%')"
            elif "da" in sc_clean and ("khoác" in sc_clean or "biker" in sc_clean):
                sql += " AND (py_lower(name) LIKE '%da%' OR py_lower(tags) LIKE '%da%') AND (py_lower(name) LIKE '%khoác%' OR py_lower(category) LIKE '%khoác%')"
            else:
                q_sub = f"%{sc_clean}%"
                sql += " AND (py_lower(sub_category) LIKE ? OR py_lower(name) LIKE ? OR py_lower(tags) LIKE ?)"
                params.extend([q_sub, q_sub, q_sub])

        # Lọc theo từ khóa tìm kiếm (tên, mô tả, tag, danh mục, mã, chất liệu)
        if query and str(query).strip():
            q = f"%{str(query).strip().lower()}%"
            sql += " AND (py_lower(name) LIKE ? OR py_lower(description) LIKE ? OR py_lower(tags) LIKE ? OR py_lower(sub_category) LIKE ? OR py_lower(code) LIKE ? OR py_lower(material) LIKE ?)"
            params.extend([q, q, q, q, q, q])

        # Lọc theo chất liệu vải
        if material and str(material).strip():
            m_clean = str(material).strip().lower()
            sql += " AND (py_lower(material) LIKE ? OR py_lower(description) LIKE ? OR py_lower(tags) LIKE ? OR py_lower(name) LIKE ?)"
            params.extend([f"%{m_clean}%", f"%{m_clean}%", f"%{m_clean}%", f"%{m_clean}%"])


        # Lọc theo danh mục sản phẩm (sử dụng py_lower để hỗ trợ tiếng Việt có dấu)
        if category and str(category).strip():
            cat_clean = str(category).strip().lower()
            if "loe" in cat_clean:
                sql += " AND (py_lower(category) LIKE '%loe%' OR py_lower(sub_category) LIKE '%loe%' OR py_lower(name) LIKE '%loe%' OR py_lower(tags) LIKE '%loe%')"
            else:
                cat = f"%{cat_clean}%"
                sql += " AND (py_lower(category) LIKE ? OR py_lower(sub_category) LIKE ? OR py_lower(name) LIKE ?)"
                params.extend([cat, cat, cat])

        # Lọc giá tối thiểu
        if min_price and int(min_price) > 0:
            sql += " AND price >= ?"
            params.append(int(min_price))

        # Lọc giá tối đa
        if max_price and int(max_price) > 0:
            sql += " AND price <= ?"
            params.append(int(max_price))

        # Lọc theo màu sắc
        if color and str(color).strip():
            sql += " AND py_lower(color) LIKE ?"
            params.append(f"%{str(color).strip().lower()}%")

        # Lọc theo kích cỡ (size)
        if size and str(size).strip():
            sql += " AND py_lower(sizes) LIKE ?"
            params.append(f"%{str(size).strip().lower()}%")

        # Loại bỏ phụ kiện nhỏ khi tìm kiếm chung
        if not query and not category and not min_price and not max_price and not color:
            sql += " AND category != 'Phụ kiện'"

        # Sắp xếp: Ưu tiên các trang phục thời trang chính, đưa đồ lót / set đồ lót xuống sau
        sql += f" ORDER BY (CASE WHEN py_lower(name) LIKE '%set %' OR py_lower(name) LIKE '%ba lỗ%' THEN 1 ELSE 0 END) ASC, price ASC LIMIT {max(1, min(int(limit) if limit else 6, 12))}"
        cursor.execute(sql, params) # Thực thi truy vấn SQL
        rows = cursor.fetchall() # Lấy danh sách kết quả

        # Nếu có các tiêu chí cụ thể (từ khóa, chất liệu, màu sắc, giá, size...) mà không tìm thấy,
        # TUYỆT ĐỐI KHÔNG nới lỏng để tránh trả về sản phẩm sai tiêu chí khi trong kho không có
        has_strict_filter = bool(query or material or color or min_price or max_price or size)

        # Nếu không có hàng khớp chính xác nhưng có sub_category, ưu tiên tìm theo sub_category trước (khi không có tiêu chí nghiêm ngặt)
        if not rows and sub_category and not has_strict_filter:
            sc_c = sub_category.lower()
            if "âu" in sc_c or "tây" in sc_c:
                cursor.execute(
                    "SELECT * FROM products WHERE (py_lower(sub_category) LIKE '%quần âu%' OR py_lower(name) LIKE '%quần âu%') ORDER BY price ASC LIMIT 4"
                )
            else:
                cursor.execute(
                    "SELECT * FROM products WHERE (py_lower(sub_category) LIKE ? OR py_lower(name) LIKE ? OR py_lower(tags) LIKE ?) ORDER BY price ASC LIMIT 4",
                    (f"%{sc_c}%", f"%{sc_c}%", f"%{sc_c}%")
                )
            relaxed_rows = cursor.fetchall()
            if relaxed_rows:
                alt_products = [self._format_product(r) for r in relaxed_rows]
                conn.close()
                return (alt_products, f"Gợi ý {len(alt_products)} mẫu '{sub_category}' nổi bật tại cửa hàng:")

        # Nếu không có hàng khớp chính xác nhưng có category, tìm sản phẩm cùng category ở mức giá/màu khác (khi không có tiêu chí nghiêm ngặt)
        if not rows and category and not has_strict_filter:
            cursor.execute(
                "SELECT * FROM products WHERE (py_lower(category) LIKE ? OR py_lower(sub_category) LIKE ? OR py_lower(name) LIKE ?) ORDER BY price ASC LIMIT 4",
                (f"%{category.lower()}%", f"%{category.lower()}%", f"%{category.lower()}%")
            )
            relaxed_rows = cursor.fetchall()
            if relaxed_rows:
                alt_products = [self._format_product(r) for r in relaxed_rows]
                conn.close()
                return (alt_products, f"Gợi ý {len(alt_products)} mẫu '{category}' nổi bật tại cửa hàng:")

        conn.close() # Đóng kết nối CSDL
        products = [self._format_product(r) for r in rows] # Chuẩn hóa từng sản phẩm

        # Trả về thông báo nếu không có sản phẩm nào
        if not products:
            return ([], "Không tìm thấy sản phẩm nào trong database phù hợp với tiêu chí tìm kiếm.")

        summary = f"Tìm thấy {len(products)} sản phẩm trong database."
        return (products, summary)

    def get_product(self, product_id_or_name: str) -> Tuple[Optional[Dict[str, Any]], str]:
        conn = self._get_db() # Mở kết nối CSDL
        cursor = conn.cursor()
        query_val = str(product_id_or_name).strip()

        row = None
        # Tìm theo ID sản phẩm nếu đầu vào là số
        if query_val.isdigit():
            cursor.execute("SELECT * FROM products WHERE id = ?", (int(query_val),))
            row = cursor.fetchone()

        # Tìm theo mã sản phẩm (code)
        if not row:
            cursor.execute("SELECT * FROM products WHERE code = ?", (query_val,))
            row = cursor.fetchone()

        # Tìm gần đúng theo tên sản phẩm
        if not row:
            cursor.execute("SELECT * FROM products WHERE name LIKE ? LIMIT 1", (f"%{query_val}%",))
            row = cursor.fetchone()

        conn.close() # Đóng kết nối CSDL

        # Trả về thông báo nếu không tìm thấy
        if not row:
            return (None, f"Không tìm thấy sản phẩm '{product_id_or_name}' trong database.")

        product = self._format_product(row) # Định dạng thông tin sản phẩm
        return (product, f"Đã tìm thấy sản phẩm: {product['name']}")

    def check_stock(self, product_id_or_name: str, size: str = "", color: str = "") -> Tuple[Optional[Dict[str, Any]], str]:
        # Lấy thông tin sản phẩm từ CSDL
        product, msg = self.get_product(product_id_or_name)
        if not product:
            return (None, msg)

        # Lấy số lượng hàng còn trong kho, size và màu
        stock = product.get("stock", 50)
        sizes_available = product.get("sizes", [])
        prod_color = product.get("color", "")

        # Kiểm tra xem size khách yêu cầu có còn không
        is_size_match = True
        if size and size.strip():
            is_size_match = any(size.strip().upper() == s.upper() for s in sizes_available)

        # Kiểm tra xem màu khách yêu cầu có sẵn không
        is_color_match = True
        if color and color.strip():
            is_color_match = color.strip().lower() in prod_color.lower()

        # Soạn thông báo tình trạng hàng tồn kho
        if stock <= 0:
            status_text = f"Sản phẩm '{product['name']}' hiện đang TẠM HẾT HÀNG trong kho."
        else:
            status_text = f"Sản phẩm '{product['name']}' hiện CÒN HÀNG ({stock} cái)."
            if size:
                if is_size_match:
                    status_text += f" Size '{size}' đang có sẵn."
                else:
                    status_text += f" Size '{size}' hiện hết, còn size: {', '.join(sizes_available)}."
            if color:
                if is_color_match:
                    status_text += f" Màu '{color}' có sẵn."
                else:
                    status_text += f" Hiện chỉ có màu: {prod_color}."

        return (product, status_text)

    def get_product_price(self, product_id_or_name: str) -> Tuple[Optional[Dict[str, Any]], str]:
        # Lấy dữ liệu sản phẩm từ CSDL
        product, msg = self.get_product(product_id_or_name)
        if not product:
            return (None, msg)

        # Lấy giá bán hiện tại, giá gốc và điểm tích lũy
        price = product["price"]
        old_price = product.get("old_price", price)
        discount = product.get("discount_pct", 0)
        points = product.get("points", int(price / 1000))

        # Soạn chi tiết bảng giá
        info = (
            f"Sản phẩm '{product['name']}':\n"
            f"- Giá bán: {price:,}đ\n"
            f"- Giá niêm yết: {old_price:,}đ (Giảm {discount}%)\n"
            f"- Tích lũy: {points:,} điểm"
        )
        return (product, info)

    def search_by_price(self, max_price: int, min_price: int = 0, category: str = "", limit: int = 6) -> Tuple[List[Dict[str, Any]], str]:
        # Lọc sản phẩm theo khoảng giá người dùng yêu cầu
        return self.search_products(
            query="",
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )

    def search_by_category(self, category: str, limit: int = 6) -> Tuple[List[Dict[str, Any]], str]:
        # Lọc sản phẩm theo danh mục hoặc loại trang phục
        return self.search_products(
            query="",
            category=category,
            limit=limit
        )

    def get_curated_outfit(self, style: str = "douyin", gender: str = "nam") -> Tuple[List[Dict[str, Any]], str]:
        conn = self._get_db() # Kết nối CSDL
        cursor = conn.cursor()
        style_lower = (style or "douyin").lower()

        # Gợi ý set đồ phong cách Douyin / Đường phố
        if "douyin" in style_lower or "trung quốc" in style_lower or "streetwear" in style_lower:
            target_ids = [3, 4, 5, 30] # Áo thun + Quần jeans + Sneaker + Kính
            summary = "Set đồ phong cách Douyin giới trẻ: Áo thun oversize + Quần jeans ống suông vintage + Sneaker retro + Kính mát Titanium"
        # Gợi ý set đồ phong cách Hàn Quốc
        elif "hàn quốc" in style_lower or "korean" in style_lower:
            target_ids = [28, 19, 5] if gender == "nam" else [28, 7, 5]
            summary = "Set đồ phong cách Hàn Quốc: Áo len mỏng cổ lọ + Quần âu slim fit / Chân váy midi + Sneaker retro"
        # Gợi ý set đồ phong cách công sở
        elif "công sở" in style_lower or "office" in style_lower:
            target_ids = [11, 19, 29, 25] # Sơ mi + Quần âu + Giày tây + Thắt lưng
            summary = "Set đồ công sở lịch lãm: Áo sơ mi nano chống nhăn + Quần âu slim fit + Giày tây derby Oxford + Thắt lưng da bò"
        # Gợi ý set đồ phong cách trẻ trung năng động
        else:
            target_ids = [15, 21, 5] # Polo + Quần Khaki + Sneaker
            summary = "Set đồ trẻ trung năng động: Áo polo dệt kim + Quần khaki chino + Giày sneaker retro"

        # Lấy thông tin các sản phẩm trong set đồ từ CSDL
        placeholders = ",".join("?" * len(target_ids))
        cursor.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", target_ids)
        rows = cursor.fetchall()
        conn.close() # Đóng kết nối CSDL

        # Sắp xếp đúng theo thứ tự phối đồ
        prod_map = {r["id"]: self._format_product(r) for r in rows}
        ordered_products = [prod_map[tid] for tid in target_ids if tid in prod_map]
        return (ordered_products, summary)
