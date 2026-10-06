import os
import sys
import sqlite3

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")

def view_database():
    if not os.path.exists(DB_PATH):
        print(f"[!] Không tìm thấy file database tại: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("                DANH SÁCH BẢNG TRONG DATABASE")
    print("="*70)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for t in tables:
        print(f"  • Bảng: {t[0]}")

    # 1. Bảng users
    print("\n" + "="*70)
    print("                1. DANH SÁCH TÀI KHOẢN (BẢNG: users)")
    print("="*70)
    cursor.execute("SELECT id, username, email, full_name, created_at FROM users")
    users = cursor.fetchall()
    if users:
        print(f"{'ID':<4} | {'USERNAME':<16} | {'EMAIL':<24} | {'HỌ VÀ TÊN':<20} | {'NGÀY TẠO'}")
        print("-" * 85)
        for u in users:
            print(f"{u[0]:<4} | {u[1]:<16} | {u[2]:<24} | {(u[3] or '-'):<20} | {u[4]}")
    else:
        print("  (Chưa có tài khoản nào đăng ký)")

    # 2. Bảng products
    print("\n" + "="*70)
    print("                2. DỮ LIỆU SẢN PHẨM (BẢNG: products)")
    print("="*70)
    cursor.execute("SELECT id, name, category, color, price, sizes FROM products")
    products = cursor.fetchall()
    print(f"{'ID':<4} | {'TÊN SẢN PHẨM':<32} | {'LOẠI':<8} | {'MÀU':<8} | {'GIÁ (VNĐ)':<12} | {'SIZE'}")
    print("-" * 85)
    for p in products:
        price_str = f"{p[4]:,}đ"
        print(f"{p[0]:<4} | {p[1]:<32} | {p[2]:<8} | {p[3] or '-':<8} | {price_str:<12} | {p[5]}")

    # 3. Bảng chat_history
    print("\n" + "="*70)
    print("           3. LỊCH SỬ HỘI THOẠI GẦN ĐÂY (BẢNG: chat_history)")
    print("="*70)
    cursor.execute("SELECT id, user_message, intent, created_at FROM chat_history ORDER BY id DESC LIMIT 10")
    chats = cursor.fetchall()
    if chats:
        print(f"{'ID':<4} | {'USER MESSAGE':<35} | {'INTENT':<16} | {'THỜI GIAN'}")
        print("-" * 80)
        for c in chats:
            msg = (c[1][:32] + '...') if len(c[1]) > 32 else c[1]
            print(f"{c[0]:<4} | {msg:<35} | {c[2]:<16} | {c[3]}")
    else:
        print("  (Chưa có tin nhắn nào được lưu)")

    conn.close()
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    view_database()
