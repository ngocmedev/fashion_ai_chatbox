# -*- coding: utf-8 -*-
"""
Script chuẩn hóa tên gọi thời trang và sửa toàn bộ link ảnh bị hỏng (404 Amazon S3)
của 65 sản phẩm H&M / Evern (mã HM...) thành ảnh Unsplash CDN thời trang cao cấp.
"""
import sqlite3
import json
import os
import sys

# Đảm bảo in UTF-8
sys.stdout.reconfigure(encoding='utf-8')

PRODUCTS_FIX = {
    # Mã HM: (Tên mới thời trang, Link ảnh Unsplash chất lượng cao)
    "HM775015": (
        "Áo Hai Dây Lụa Satin Cao Cấp (Đen)",
        "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600&auto=format&fit=crop&q=80"
    ),
    "HM775044": (
        "Áo Hai Dây Camisole Thanh Lịch (Trắng)",
        "https://images.unsplash.com/photo-1508427953056-b00b8d78ebf5?w=600&auto=format&fit=crop&q=80"
    ),
    "HM775051": (
        "Áo Croptop Hai Dây Ôm Body (Trắng Kem)",
        "https://images.unsplash.com/photo-1525171254930-643fc658b64e?w=600&auto=format&fit=crop&q=80"
    ),
    "HM565003": (
        "Quần Tất Siêu Mỏng 20D Tự Nhiên Màu Da",
        "https://images.unsplash.com/photo-1516762689617-e1cffcef479d?w=600&auto=format&fit=crop&q=80"
    ),
    "HM586001": (
        "Quần Tất Định Hình Nâng Mông Shape Up 30D (Đen)",
        "https://images.unsplash.com/photo-1506630448388-4e683c67ddb0?w=600&auto=format&fit=crop&q=80"
    ),
    "HM679048": (
        "Áo Khoác Gió Thể Thao Phom Rộng Windbreaker (Xám Ghi)",
        "https://images.unsplash.com/photo-1544441893-675973e31985?w=600&auto=format&fit=crop&q=80"
    ),
    "HM679052": (
        "Áo Khoác Gió Phối Màu Pastel Windbreaker (Xanh Nhạt)",
        "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600&auto=format&fit=crop&q=80"
    ),
    "HM379047": (
        "Áo Thun Tay Dài Cotton Frugan Basic (Xanh Navy)",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458003": (
        "Quần Jogger Nỉ Thể Thao Jerry (Xám Đậm)",
        "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458004": (
        "Quần Jogger Nỉ Thể Thao Jerry (Xám Ghi)",
        "https://images.unsplash.com/photo-1509551388413-e18d0ac5d495?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458028": (
        "Quần Jogger Nỉ Bo Gấu Jerry (Đen)",
        "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458029": (
        "Quần Jogger Dáng Rộng Jerry Basic (Xám Chì)",
        "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458034": (
        "Quần Jogger Nữ Năng Động Jerry (Hồng Pastel)",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458038": (
        "Quần Jogger Nỉ Cạp Thun Jerry (Đen Tuyền)",
        "https://images.unsplash.com/photo-1539185441755-769473a23570?w=600&auto=format&fit=crop&q=80"
    ),
    "HM458039": (
        "Quần Jogger Thể Thao Jerry (Xanh Navy)",
        "https://images.unsplash.com/photo-1479064555552-3ef4979f8908?w=600&auto=format&fit=crop&q=80"
    ),
    "HM129001": (
        "Quần Tây Ống Suông Công Sở Babette (Đen)",
        "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=600&auto=format&fit=crop&q=80"
    ),
    "HM129014": (
        "Quần Tây Xếp Ly Dáng Rộng Babette (Đen Tuyền)",
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&auto=format&fit=crop&q=80"
    ),
    "HM129018": (
        "Quần Tây Công Sở Thời Thượng Babette (Đỏ Rượu Burgundy)",
        "https://images.unsplash.com/photo-1551803091-e20673f15770?w=600&auto=format&fit=crop&q=80"
    ),
    "HM129025": (
        "Quần Âu Ống Đứng Lưng Cao Babette (Xám Đậm)",
        "https://images.unsplash.com/photo-1475178626620-a4d074967452?w=600&auto=format&fit=crop&q=80"
    ),
    "HM173001": (
        "Quần Tất Gen Bụng Thon Gọn Control Top 50D (Đen)",
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&auto=format&fit=crop&q=80"
    ),
    "HM589006": (
        "Set 2 Kẹp Tóc Càng Cua Hàn Quốc (Đen Nhám)",
        "https://images.unsplash.com/photo-1535295972055-1c762f4483e5?w=600&auto=format&fit=crop&q=80"
    ),
    "HM589007": (
        "Set 2 Kẹp Tóc Càng Cua Thời Trang (Màu Be Xám)",
        "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=600&auto=format&fit=crop&q=80"
    ),
    "HM589010": (
        "Set 2 Kẹp Tóc Càng Cua Pastel (Cam Nhạt)",
        "https://images.unsplash.com/photo-1611042553365-9b101441c135?w=600&auto=format&fit=crop&q=80"
    ),
    "HM589011": (
        "Set 2 Kẹp Tóc Kim Loại Sang Chảnh (Bạc Ánh Kim)",
        "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600&auto=format&fit=crop&q=80"
    ),
    "HM589012": (
        "Set 2 Kẹp Tóc Kim Loại Cao Cấp (Vàng Gold)",
        "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=600&auto=format&fit=crop&q=80"
    ),
    "HM085001": (
        "Quần Legging Lửng Nâng Mông Co Giãn (Đen)",
        "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=600&auto=format&fit=crop&q=80"
    ),
    "HM085026": (
        "Quần Legging Thể Thao Lửng (Trắng Kem)",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&auto=format&fit=crop&q=80"
    ),
    "HM085027": (
        "Quần Legging Lửng Năng Động (Xám Ghi)",
        "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&auto=format&fit=crop&q=80"
    ),
    "HM035001": (
        "Dù Cầm Tay Tự Động Chống Nắng UV Cao Cấp (Đen)",
        "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=600&auto=format&fit=crop&q=80"
    ),
    "HM661022": (
        "Váy Ngủ Lụa Satin Sang Trọng Phối Ren (Trắng Ngọc)",
        "https://images.unsplash.com/photo-1518049362265-d5b2a6467637?w=600&auto=format&fit=crop&q=80"
    ),
    "HM661025": (
        "Váy Ngủ Lụa Satin Tiểu Thư (Hồng Phấn)",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600&auto=format&fit=crop&q=80"
    ),
    "HM872001": (
        "Áo Khoác Dệt Kim Khóa Kéo Dorian (Đen)",
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&auto=format&fit=crop&q=80"
    ),
    "HM872037": (
        "Áo Khoác Hoodie Nỉ Dorian Có Mũ (Xám Đậm)",
        "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600&auto=format&fit=crop&q=80"
    ),
    "HM872043": (
        "Áo Khoác Cardigan Len Mỏng Dorian (Trắng Kem)",
        "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&auto=format&fit=crop&q=80"
    ),
    "HM872051": (
        "Áo Thun Dài Tay Cổ Tròn Dorian (Đen)",
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&auto=format&fit=crop&q=80"
    ),
    "HM872052": (
        "Áo Khoác Bomber Thể Thao Dorian (Xanh Navy)",
        "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=600&auto=format&fit=crop&q=80"
    ),
    "HM872053": (
        "Áo Khoác Chần Bông Siêu Nhẹ Dorian (Xám Ghi)",
        "https://images.unsplash.com/photo-1544441893-675973e31985?w=600&auto=format&fit=crop&q=80"
    ),
    "HM706001": (
        "Set 3 Áo Ba Lỗ Cotton Cao Cấp Evern (Trắng)",
        "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600&auto=format&fit=crop&q=80"
    ),
    "HM706004": (
        "Set 3 Áo Tank Top Thể Thao Năng Động (Trắng)",
        "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80"
    ),
    "HM706005": (
        "Set 3 Áo Ba Lỗ Dệt Kim Thoáng Khí (Xám Nhạt)",
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&auto=format&fit=crop&q=80"
    ),
    "HM721001": (
        "Set Chun Buộc Tóc Đính Charm Kim Loại (Vàng Gold)",
        "https://images.unsplash.com/photo-1599643477877-530eb83abc8e?w=600&auto=format&fit=crop&q=80"
    ),
    "HM721002": (
        "Set Chun Buộc Tóc Đính Charm Kim Loại (Bạc Silver)",
        "https://images.unsplash.com/photo-1600003014755-ba31aa59c4b6?w=600&auto=format&fit=crop&q=80"
    ),
    "HM730001": (
        "Quần Tất Lót Nỉ Giữ Nhiệt 200D Mùa Đông (Đen)",
        "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&auto=format&fit=crop&q=80"
    ),
    "HM339034": (
        "Set 6 Áo Thun Body Cotton Co Giãn 4 Chiều (Trắng)",
        "https://images.unsplash.com/photo-1525171254930-643fc658b64e?w=600&auto=format&fit=crop&q=80"
    ),
    "HM033001": (
        "Quần Tất Đùi Viền Ren Chống Tụt Nouvelle (Đen)",
        "https://images.unsplash.com/photo-1518049362265-d5b2a6467637?w=600&auto=format&fit=crop&q=80"
    ),
    "HM033006": (
        "Quần Tất Đùi Viền Silicon Giữ Dáng Nouvelle (Màu Da)",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=600&auto=format&fit=crop&q=80"
    ),
    "HM959011": (
        "Quần Thể Thao Dệt Kim Dáng Suông Thompson (Đen)",
        "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=600&auto=format&fit=crop&q=80"
    ),
    "HM959013": (
        "Quần Thể Thao Dệt Kim Dáng Suông Thompson (Xám Đậm)",
        "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=600&auto=format&fit=crop&q=80"
    ),
    "HM224001": (
        "Hộp 4 Đôi Tất Cổ Trung Cotton Kháng Khuẩn (Be Kem)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM224002": (
        "Hộp 4 Đôi Tất Cổ Trung Cotton Kháng Khuẩn (Đen)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM231002": (
        "Hộp 4 Đôi Quần Tất Da Chân Siêu Dai Tự Nhiên (Màu Da)",
        "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=600&auto=format&fit=crop&q=80"
    ),
    "HM289011": (
        "Quần Kaki Ống Đứng Dáng Slim Fit Cheapo (Xanh Denim)",
        "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&auto=format&fit=crop&q=80"
    ),
    "HM610001": (
        "Quần Tây Âu Nam Dáng Suông Công Sở (Đen)",
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&auto=format&fit=crop&q=80"
    ),
    "HM610007": (
        "Quần Tây Âu Nam Slim Fit Co Giãn (Đen Tuyền)",
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&auto=format&fit=crop&q=80"
    ),
    "HM610010": (
        "Quần Tây Công Sở Dáng Lửng Mắt Cá (Đen)",
        "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=600&auto=format&fit=crop&q=80"
    ),
    "HM340001": (
        "Quần Tất Cạp Cao Nâng Mông Highwaist 30D (Đen)",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80"
    ),
    "HM442007": (
        "Set 3 Đôi Tất Sneaker Cổ Ngắn Chống Tụt (Đen)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM442010": (
        "Set 3 Đôi Tất Sneaker Cổ Ngắn Chống Tụt (Trắng)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM442042": (
        "Set 3 Đôi Tất Sneaker Cotton Thoáng Khí (Xám Nhạt)",
        "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600&auto=format&fit=crop&q=80"
    ),
    "HM442043": (
        "Set 3 Đôi Tất Sneaker Cổ Lửng Năng Động (Xám Sáng)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM074062": (
        "Hộp 5 Đôi Tất Sneaker Nữ Sigge Pastel (Hồng Dễ Thương)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM074069": (
        "Hộp 5 Đôi Tất Sneaker Sigge Khử Mùi (Xám Ghi)",
        "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600&auto=format&fit=crop&q=80"
    ),
    "HM074071": (
        "Hộp 5 Đôi Tất Sneaker Nam Nữ Sigge Cotton (Đen)",
        "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=600&auto=format&fit=crop&q=80"
    ),
    "HM734002": (
        "Set 2 Áo Thun Tay Dài Cotton Kompis (Đen Cơ Bản)",
        "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600&auto=format&fit=crop&q=80"
    ),
    "HM734054": (
        "Set 2 Áo Thun Tay Dài Cotton Kompis (Xanh Pastel)",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600&auto=format&fit=crop&q=80"
    )
}

def update_database():
    db_path = 'database/database.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} không tồn tại!")
        return 0

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    updated_count = 0
    for code, (new_name, new_img) in PRODUCTS_FIX.items():
        c.execute("""
            UPDATE products 
            SET name = ?, image_url = ?
            WHERE code = ?
        """, (new_name, new_img, code))
        if c.rowcount > 0:
            updated_count += c.rowcount
            
    conn.commit()
    conn.close()
    print(f"✅ Đã cập nhật thành công {updated_count} sản phẩm trong database SQLite!")
    return updated_count

def update_json_file(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} không tồn tại, bỏ qua.")
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated_count = 0
    if isinstance(data, list):
        for p in data:
            code = p.get('code')
            if code in PRODUCTS_FIX:
                new_name, new_img = PRODUCTS_FIX[code]
                p['name'] = new_name
                p['image_url'] = new_img
                # Nếu có trường images (list)
                if 'images' in p and isinstance(p['images'], list) and len(p['images']) > 0:
                    p['images'][0] = new_img
                updated_count += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã cập nhật {updated_count} sản phẩm trong {file_path}")
    return updated_count

if __name__ == '__main__':
    print("🚀 Bắt đầu sửa đổi hình ảnh và tên gọi sản phẩm...")
    update_database()
    update_json_file('data/products.json')
    update_json_file('data/hm_ecommerce_products_vi.json')
    print("🎉 Hoàn tất cập nhật dữ liệu sản phẩm!")
