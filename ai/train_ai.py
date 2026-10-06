"""
EVERN FASHION AI - CÔNG CỤ HUẤN LUYỆN AI BẰNG LOCAL LLM & DATASET RIÊNG
======================================================================
Hỗ trợ nạp dataset riêng (JSON, JSONL, CSV, TXT, MD) để:
1. Tạo Custom Model trực tiếp trên Ollama (evern-ai-stylist) với Modelfile
2. Huấn luyện lại Vector Knowledge Base (RAG FAISS)
3. Xuất dataset chuẩn ChatML / ShareGPT để Fine-tune LoRA/QLoRA bằng GPU

Cách sử dụng:
  python train_ai.py                        # Huấn luyện tự động từ data/intents.json
  python train_ai.py --dataset my_data.json # Huấn luyện từ file dataset riêng của bạn
  python train_ai.py --export-finetune      # Xuất file data/dataset_finetune.jsonl để train LoRA
"""

import os
import sys
import json
import csv
import re
import subprocess
from typing import Dict, Any, List

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư mục gốc dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATASET = os.path.join(BASE_DIR, "data", "intents.json")
MODELFILE_PATH = os.path.join(BASE_DIR, "ai", "Modelfile")
FINETUNE_OUTPUT = os.path.join(BASE_DIR, "data", "dataset_finetune.jsonl")

def load_user_dataset(file_path: str) -> List[Dict[str, str]]:
    """
    Đọc dataset từ nhiều định dạng:
    - intents.json: {"intents": [{"tag": ..., "patterns": [...], "responses": [...]}]}
    - JSON list: [{"question": "...", "answer": "..."}, ...] hoặc [{"instruction": ..., "output": ...}]
    - JSONL: Mỗi dòng 1 JSON object
    - CSV: Cột câu hỏi, câu trả lời
    - TXT / MD: Dạng Q&A hoặc tài liệu
    """
    if not os.path.exists(file_path):
        print(f"[Lỗi] Không tìm thấy file dataset: {file_path}")
        return []

    ext = os.path.splitext(file_path)[1].lower()
    pairs = []

    try:
        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "intents" in data:
                # Định dạng intents.json
                for item in data["intents"]:
                    tag = item.get("tag", "general")
                    patterns = item.get("patterns", [])
                    responses = item.get("responses", [])
                    if patterns and responses:
                        for p in patterns[:5]:  # Lấy tối đa 5 mẫu mỗi intent
                            resp = responses[0] if responses else ""
                            pairs.append({"user": p.strip(), "assistant": resp.strip(), "tag": tag})
            elif isinstance(data, list):
                # Định dạng danh sách câu hỏi - trả lời
                for item in data:
                    q = item.get("question") or item.get("instruction") or item.get("user") or item.get("input") or ""
                    a = item.get("answer") or item.get("output") or item.get("assistant") or item.get("response") or ""
                    if q and a:
                        pairs.append({"user": str(q).strip(), "assistant": str(a).strip()})

        elif ext == ".jsonl":
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    q = item.get("question") or item.get("instruction") or item.get("user") or item.get("prompt") or ""
                    a = item.get("answer") or item.get("output") or item.get("assistant") or item.get("response") or item.get("completion") or ""
                    if (not q or not a) and "messages" in item:
                        for m in item["messages"]:
                            if m.get("role") == "user":
                                q = m.get("content", "")
                            elif m.get("role") == "assistant":
                                a = m.get("content", "")
                    if q and a:
                        pairs.append({"user": str(q).strip(), "assistant": str(a).strip()})

        elif ext in [".csv", ".tsv"]:
            delimiter = "," if ext == ".csv" else "\t"
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader, [])]
                q_idx = 0
                a_idx = 1
                for i, h in enumerate(headers):
                    if any(w in h for w in ["hỏi", "question", "user", "input", "cau_hoi"]):
                        q_idx = i
                    elif any(w in h for w in ["trả lời", "answer", "assistant", "output", "cau_tra_loi", "phan_hoi"]):
                        a_idx = i
                for row in reader:
                    if len(row) > max(q_idx, a_idx):
                        q = row[q_idx].strip()
                        a = row[a_idx].strip()
                        if q and a:
                            pairs.append({"user": q, "assistant": a})

        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            # Tách theo cặp HỎI / ĐÁP nếu có
            matches = re.findall(r"(?:Hỏi|Q|User|Khách):\s*(.+?)\n(?:Đáp|A|Bot|Stylist):\s*(.+?)(?=\n(?:Hỏi|Q|User|Khách):|\Z)", text, re.DOTALL | re.IGNORECASE)
            for q, a in matches:
                pairs.append({"user": q.strip(), "assistant": a.strip()})

    except Exception as e:
        print(f"[Lỗi] Khi đọc file dataset: {e}")

    print(f"[Dataset] Đã nạp thành công {len(pairs)} cặp câu hỏi - trả lời từ: {file_path}")
    return pairs

def build_ollama_modelfile(pairs: List[Dict[str, str]], base_model: str = "qwen2.5:1.5b") -> str:
    """Tạo Modelfile cho Ollama để huấn luyện Custom Model với phong cách và tri thức riêng."""
    few_shot_lines = []
    seen_tags = set()
    count = 0
    for p in pairs:
        tag = p.get("tag")
        if tag and tag in seen_tags:
            continue
        if tag:
            seen_tags.add(tag)
        
        u = p["user"].replace('"', '\\"')
        a = p["assistant"].replace('"', '\\"')
        few_shot_lines.append(f'MESSAGE user "{u}"')
        few_shot_lines.append(f'MESSAGE assistant "{a}"')
        count += 1
        if count >= 20:
            break

    messages_block = "\n".join(few_shot_lines)

    modelfile_content = f"""# ==========================================================
# EVERN AI STYLIST - CUSTOM LOCAL MODELFILE
# Đã huấn luyện từ dataset riêng của thương hiệu Evern
# ==========================================================
FROM {base_model}

# Tối ưu siêu tham số cho tư vấn thời trang
PARAMETER temperature 0.35
PARAMETER top_p 0.85
PARAMETER top_k 40
PARAMETER repeat_penalty 1.15
PARAMETER num_ctx 4096
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"

# Định hình tính cách chuyên gia Stylist
SYSTEM \"\"\"Bạn là Evern AI Stylist - Chuyên viên tư vấn và định hình phong cách thời trang thông minh, thanh lịch, tận tâm của thương hiệu Evern.

QUY TẮC BẮT BUỘC:
1. Xưng 'mình' hoặc 'Evern' và gọi khách hàng là 'bạn'. Giọng điệu ấm áp, trẻ trung, chuyên nghiệp và lịch thiệp.
2. Dựa sát vào danh sách sản phẩm thật từ Database SQLite (tên, mã, giá, màu sắc, size) được cung cấp trong ngữ cảnh. Tuyệt đối không được tự ý bịa đặt thông tin sản phẩm hay giá cả sai lệch.
3. Luôn in đậm tên sản phẩm, giá bán (VNĐ) và size số sẵn có.
4. Nhiệt tình gợi ý mẹo phối đồ tôn dáng và mời khách chia sẻ thêm chiều cao, cân nặng để tư vấn chọn size chuẩn xác nhất.
5. Tuyệt đối KHÔNG in ra các ký hiệu kỹ thuật như [bang_size.md] hay markdown thô.
6. BẮT BUỘC trả lời 100% bằng Tiếng Việt tự nhiên, chuẩn mực, lưu loát. Tuyệt đối KHÔNG dùng hoặc chêm chữ tiếng Trung (như 裤子, 衣服) hay từ ngữ ngoại lai lạ.\"\"\"

# Dữ liệu huấn luyện mẫu (Few-shot learning từ Dataset riêng):
{messages_block}
"""
    os.makedirs(os.path.dirname(MODELFILE_PATH), exist_ok=True)
    with open(MODELFILE_PATH, "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"[Modelfile] Đã lưu file cấu hình mô hình tại: {MODELFILE_PATH}")
    return MODELFILE_PATH

def train_ollama_model(model_name: str = "evern-ai-stylist"):
    """Thực thi lệnh 'ollama create' để xây dựng mô hình AI cục bộ."""
    print(f"\n[Bắt đầu] Đang biên dịch và huấn luyện mô hình '{model_name}' trên Ollama...")
    try:
        cmd = ["ollama", "create", model_name, "-f", MODELFILE_PATH]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        raw_log = (result.stdout or "") + "\n" + (result.stderr or "")
        for line in raw_log.splitlines():
            cleaned_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line).strip()
            if cleaned_line and not any(w in cleaned_line for w in ["?25", "?2026"]):
                print(f"  ⚡ {cleaned_line}")
        print(f"\n🎉 [THÀNH CÔNG] Mô hình AI riêng '{model_name}' đã được huấn luyện và sẵn sàng!")
        print(f"👉 Chatbot sẽ tự động nhận diện và ưu tiên sử dụng model '{model_name}' ngay lập tức.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Lỗi] Khi gọi Ollama create: {e.stderr or e}")
        print("Vui lòng đảm bảo ứng dụng Ollama đang bật trên máy tính của bạn.")
        return False
    except FileNotFoundError:
        print("[Lỗi] Không tìm thấy lệnh 'ollama'. Vui lòng cài đặt Ollama từ https://ollama.com")
        return False

def export_finetune_dataset(pairs: List[Dict[str, str]], output_path: str = FINETUNE_OUTPUT):
    """Xuất dataset sang định dạng JSONL (ShareGPT / ChatML) để Fine-tune LoRA/QLoRA bằng GPU."""
    system_prompt = "Bạn là Evern AI Stylist - Chuyên gia tư vấn thời trang cao cấp của Evern Fashion."
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for p in pairs:
            item = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": p["user"]},
                    {"role": "assistant", "content": p["assistant"]}
                ]
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n[Xuất dữ liệu] Đã xuất {len(pairs)} mẫu hội thoại sang file: {output_path}")
    print(f"👉 File này sẵn sàng để nạp vào Unsloth, HuggingFace TRL hoặc Google Colab để fine-tune LoRA!")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Công cụ huấn luyện AI bằng LLM & Dataset riêng")
    parser.add_argument("--dataset", "-d", type=str, default=DEFAULT_DATASET, help="Đường dẫn file dataset của bạn (.json, .jsonl, .csv, .txt)")
    parser.add_argument("--base-model", "-b", type=str, default="qwen2.5:1.5b", help="Mô hình nền tảng (qwen2.5:1.5b, qwen2.5:3b, llama3.2:3b)")
    parser.add_argument("--model-name", "-m", type=str, default="evern-ai-stylist", help="Tên mô hình sau khi train trên Ollama")
    parser.add_argument("--export-finetune", action="store_true", help="Xuất file JSONL phục vụ Fine-tune LoRA nâng cao")
    args = parser.parse_args()

    print("=" * 70)
    print("      EVERN FASHION AI - TỰ HUẤN LUYỆN LOCAL LLM BẰNG DATASET RIÊNG")
    print("=" * 70)

    dataset_path = args.dataset
    if not os.path.isabs(dataset_path):
        dataset_path = os.path.join(BASE_DIR, dataset_path)

    pairs = load_user_dataset(dataset_path)
    if not pairs:
        print("[Thông báo] Sử dụng dataset mặc định data/intents.json...")
        pairs = load_user_dataset(DEFAULT_DATASET)

    if not pairs:
        print("[Thất bại] Không có dữ liệu để huấn luyện.")
        return

    if args.export_finetune:
        export_finetune_dataset(pairs)
        return

    # 1. Tạo Modelfile từ dataset trong thư mục ai/
    build_ollama_modelfile(pairs, base_model=args.base_model)

    # 2. Huấn luyện model trên Ollama
    train_ollama_model(model_name=args.model_name)

    # 3. Đồng thời xuất file fine-tune LoRA trong thư mục data/
    export_finetune_dataset(pairs)

    print("\n" + "=" * 70)
    print("HƯỚNG DẪN KIỂM TRA MÔ HÌNH VỪA TRAIN:")
    print(f"  1. Chạy thử trên terminal:  ollama run {args.model_name}")
    print(f"  2. Khởi động lại Web Chatbot: python app.py")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
