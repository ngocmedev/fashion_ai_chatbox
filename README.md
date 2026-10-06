# Evern Fashion AI Chatbot (LLM + RAG Architecture) 👗✨

Hệ thống Chatbot AI tư vấn và định hình phong cách thời trang thông minh thế hệ mới, hoạt động theo kiến trúc **RAG (Retrieval-Augmented Generation)** kết hợp **Local LLM**.

---

## 🌟 Điểm Cải Tiến Đột Phá

1. **100% Miễn Phí - 0đ API Key**:
   - Sử dụng **Local Embeddings** (`sentence-transformers/all-MiniLM-L6-v2`) chạy hoàn toàn cục bộ trên máy, không cần mạng hay bất kỳ API Key nào (không còn phụ thuộc Google Gemini hay OpenAI trả phí).
2. **Không Dùng Intent Cứng Nhắc**:
   - Loại bỏ hoàn toàn việc gõ tay các mẫu câu `intents.json`.
   - LLM tự hiểu câu hỏi tự nhiên của khách (từ tiếng lóng, câu phức đến ngữ cảnh phối đồ, hỏi size, hỏi chính sách).
3. **Cơ Chế "Tự Train Dữ Liệu" Siêu Đơn Giản**:
   - Chỉ cần thả file Markdown (`.md`) hoặc Text (`.txt`) chứa thông tin bảng size, cẩm nang phối đồ, chính sách shop vào thư mục `data/knowledge/`.
   - Chạy 1 câu lệnh nạp: Hệ thống tự động phân tách văn bản (*chunking*), tạo vector số học và lưu vào **FAISS Vector Store** cục bộ.
4. **Hỗ Trợ Local LLM (Ollama) Siêu Mượt**:
   - Tối ưu cho GPU rời (NVIDIA RTX 3050 Ti): Có thể kết nối trực tiếp với **Ollama** chạy mô hình **Qwen 2.5 (1.5B hoặc 3B)** để sinh phản hồi tiếng Việt siêu tốc.
   - Khi chưa khởi động Ollama, hệ thống tự động kích hoạt **Bộ Tổng Hợp Tri Thức Nội Bộ (Smart Synthesizer)**, cam kết 100% chatbot hoạt động trơn tru không lỗi.

---

## 📁 Cấu Trúc Thư Mục Tri Thức RAG

```text
fashion-ai-chatbot/
│
├── data/
│   ├── knowledge/              # 📂 Nơi "tự train" bằng cách thả tài liệu vào
│   │   ├── bang_size.md        # Hướng dẫn chọn size theo chiều cao, cân nặng
│   │   ├── chinh_sach_cua_hang.md # Chính sách đổi trả, ship hàng, freeship, bảo hành
│   │   ├── cam_nang_phoi_do.md # Cẩm nang phối đồ công sở, dự tiệc, Douyin/GenZ
│   │   └── chat_lieu_va_bao_quan.md # Hướng dẫn chất liệu & mẹo bảo quản đồ
│   └── products.json          # Danh mục sản phẩm thời trang mẫu
│
├── database/
│   ├── database.db            # SQLite lưu trữ sản phẩm, tài khoản, đơn hàng
│   └── faiss_index/           # 🗄️ FAISS Vector Store lưu trữ tri thức đã nhúng
│
├── ai/
│   ├── rag_engine.py          # 🚀 Động cơ RAG chính (Loader, Chunking, FAISS, Query)
│   ├── local_llm.py           # Kết nối Local LLM (Ollama & Smart Synthesizer)
│   └── chatbot.py             # Điều phối hội thoại RAG & trích xuất card sản phẩm
│
├── app.py                     # Flask Web Server & API /api/chat
└── requirements.txt           # Thư viện phụ thuộc
```

---

## 🚀 Hướng Dẫn Sử Dụng & Tự Nạp Dữ Liệu

### 1. Cài đặt môi trường
Mở terminal trong thư mục dự án và cài đặt:
```bash
pip install -r requirements.txt
```

### 2. "Tự Train" / Huấn Luyện AI Bằng Dataset Riêng
Bạn có thể tự huấn luyện AI bằng bộ dataset hội thoại của riêng bạn (`.json`, `.jsonl`, `.csv`, `.txt`):
```bash
# Huấn luyện mô hình Local LLM riêng trên Ollama từ dataset
python train_ai.py --dataset path/to/your_dataset.json

# Hoặc nếu muốn nạp tri thức vào Vector DB (FAISS):
python -m ai.rag_engine --ingest
```
*Lệnh này sẽ tự động tạo mô hình `evern-ai-stylist` trong Ollama và xuất file `dataset_finetune.jsonl`.*

### 3. Chạy Local LLM với Ollama (100% 0đ API Key & Bảo Mật)
1. Tải và cài đặt Ollama miễn phí từ: **[https://ollama.com](https://ollama.com)**
2. Khởi động Ollama (đã cài model `qwen2.5:1.5b` hoặc `evern-ai-stylist`).
3. Chatbot sẽ tự động phát hiện cổng `127.0.0.1:11434` của Ollama và chuyển sang chế độ Local AI tạo sinh đầy đủ!

### 4. Khởi chạy Web Server
```bash
python app.py
```
Mở trình duyệt truy cập: **[http://127.0.0.1:5000](http://127.0.0.1:5000)** và trải nghiệm thử hỏi bất kỳ câu nào về kích cỡ, sản phẩm, phối đồ hoặc chính sách!
