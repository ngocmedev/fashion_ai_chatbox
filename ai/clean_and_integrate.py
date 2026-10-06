"""
EVERN FASHION AI - BỘ DỌN DẸP FULL-ECOM VÀ TÍCH HỢP DATASET EVERN STYLIST
==========================================================================
1. Xóa hoàn toàn các file dataset Full-Ecom rác khỏi dự án:
   - data/full_ecom_chatbot_vi.json
   - data/full_ecom_chatbot_vi.jsonl
   - data/raw_datasets/full_ecom_chatbot_raw.json
2. Làm sạch data/intents.json:
   - Loại bỏ các câu hỏi về máy khoan, điều hòa, tủ lạnh, lò vi sóng, sách self-help, whey protein...
   - Tích hợp 65 mẫu kịch bản thời trang tiếng Việt từ evern_fashion_stylist_vi.json
3. Cập nhật data/dataset_finetune.jsonl:
   - Bổ sung toàn bộ các đoạn hội thoại ChatML mới từ evern_fashion_stylist_vi.jsonl
"""

import os
import sys
import json

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INTENTS_JSON = os.path.join(DATA_DIR, "intents.json")
FINETUNE_JSONL = os.path.join(DATA_DIR, "dataset_finetune.jsonl")
EVERN_STYLIST_JSON = os.path.join(DATA_DIR, "evern_fashion_stylist_vi.json")
EVERN_STYLIST_JSONL = os.path.join(DATA_DIR, "evern_fashion_stylist_vi.jsonl")

JUNK_KEYWORDS = [
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


def remove_full_ecom_files():
    """Xóa bỏ triệt để các file Full-Ecom ra khỏi thư mục dự án."""
    print("\n--- BƯỚC 1: XÓA CÁC FILE DATASET FULL-ECOM RÁC KHỎI DỰ ÁN ---")
    files_to_remove = [
        os.path.join(DATA_DIR, "full_ecom_chatbot_vi.json"),
        os.path.join(DATA_DIR, "full_ecom_chatbot_vi.jsonl"),
        os.path.join(DATA_DIR, "raw_datasets", "full_ecom_chatbot_raw.json")
    ]
    for path in files_to_remove:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"  [Đã xóa vĩnh viễn] {os.path.relpath(path, BASE_DIR)}")
            except Exception as e:
                print(f"  [Lỗi khi xóa] {path}: {e}")
        else:
            print(f"  [Đã không còn tồn tại] {os.path.relpath(path, BASE_DIR)}")


def clean_and_integrate_intents():
    """Làm sạch intents.json và nạp dataset thời trang mới."""
    print("\n--- BƯỚC 2: LÀM SẠCH VÀ TÍCH HỢP INTENTS.JSON ---")
    if not os.path.exists(INTENTS_JSON):
        print(f"  [Lỗi] Không tìm thấy file {INTENTS_JSON}")
        return

    with open(INTENTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Dọn dẹp junk
    removed_patterns = 0
    removed_responses = 0
    for item in data.get("intents", []):
        cleaned_patterns = []
        for p in item.get("patterns", []):
            if any(k in p.lower() for k in JUNK_KEYWORDS):
                removed_patterns += 1
            else:
                cleaned_patterns.append(p)
        item["patterns"] = cleaned_patterns

        cleaned_responses = []
        for r in item.get("responses", []):
            if any(k in r.lower() for k in JUNK_KEYWORDS):
                removed_responses += 1
            else:
                cleaned_responses.append(r)
        item["responses"] = cleaned_responses

    print(f"  -> Đã loại bỏ {removed_patterns} mẫu câu và {removed_responses} phản hồi phi thời trang khỏi intents.json.")

    # 2. Tích hợp từ evern_fashion_stylist_vi.json
    if not os.path.exists(EVERN_STYLIST_JSON):
        print(f"  [Lỗi] Chưa có file {EVERN_STYLIST_JSON}")
        return

    with open(EVERN_STYLIST_JSON, "r", encoding="utf-8") as f:
        stylist_items = json.load(f)

    intents_by_tag = {i["tag"]: i for i in data.get("intents", [])}
    added_patterns = 0
    added_responses = 0

    for item in stylist_items:
        tag = item.get("intent_tag", "recommendation")
        p_vi = item.get("prompt_vi", "").strip()
        r_vi = item.get("response_vi", "").strip()

        if tag not in intents_by_tag:
            new_intent = {"tag": tag, "patterns": [], "responses": []}
            data["intents"].append(new_intent)
            intents_by_tag[tag] = new_intent

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
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  -> Đã tích hợp thành công {added_patterns} mẫu câu và {added_responses} phản hồi thời trang Evern Stylist vào data/intents.json!")


def clean_and_integrate_finetune():
    """Tích hợp các mẫu hội thoại ChatML mới vào dataset_finetune.jsonl."""
    print("\n--- BƯỚC 3: CẬP NHẬT DATASET_FINETUNE.JSONL ---")
    existing_items = []
    existing_prompts = set()

    if os.path.exists(FINETUNE_JSONL):
        with open(FINETUNE_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        user_msg = ""
                        for m in row.get("messages", []):
                            if m.get("role") == "user":
                                user_msg = m.get("content", "").strip()
                        # Kiểm tra xem có chứa từ khóa rác không
                        if not any(k in user_msg.lower() for k in JUNK_KEYWORDS):
                            existing_items.append(row)
                            if user_msg:
                                existing_prompts.add(user_msg.lower())
                    except Exception:
                        pass

    added_finetune = 0
    if os.path.exists(EVERN_STYLIST_JSONL):
        with open(EVERN_STYLIST_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        user_msg = ""
                        for m in row.get("messages", []):
                            if m.get("role") == "user":
                                user_msg = m.get("content", "").strip()
                        if user_msg and user_msg.lower() not in existing_prompts:
                            existing_items.append(row)
                            existing_prompts.add(user_msg.lower())
                            added_finetune += 1
                    except Exception:
                        pass

    with open(FINETUNE_JSONL, "w", encoding="utf-8") as f:
        for row in existing_items:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"  -> Đã cập nhật data/dataset_finetune.jsonl: Tổng cộng {len(existing_items)} mẫu hội thoại ChatML (Đã thêm {added_finetune} mẫu Evern Stylist mới).")


def main():
    print("=" * 70)
    print(" QUY TRÌNH LOẠI BỎ FULL-ECOM & TÍCH HỢP DATASET EVERN STYLIST")
    print("=" * 70)

    remove_full_ecom_files()
    clean_and_integrate_intents()
    clean_and_integrate_finetune()

    print("\n🎉 HOÀN TẤT DỌN DẸP VÀ TÍCH HỢP DATASET THỜI TRANG TIẾNG VIỆT!")


if __name__ == "__main__":
    main()
