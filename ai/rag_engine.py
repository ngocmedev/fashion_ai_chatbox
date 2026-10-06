import os
import sys
import glob
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

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

from ai.local_llm import LocalLLMService

KNOWLEDGE_DIR = os.path.join(BASE_DIR, "data", "knowledge")
PRODUCTS_FILE = os.path.join(BASE_DIR, "data", "products.json")
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")
FAISS_DIR = os.path.join(BASE_DIR, "database", "faiss_index")

class Document:
    """Đại diện cho một đoạn tài liệu tri thức."""
    def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Document(source={self.metadata.get('source', 'unknown')}, len={len(self.page_content)})"

class RAGEngine:
    """
    Hệ thống RAG (Retrieval-Augmented Generation) thông minh cho Fashion AI Chatbot.
    Theo kiến trúc video Việt Nguyễn AI:
    1. Document Ingestion: Đọc toàn bộ tài liệu Markdown/Text trong data/knowledge/ + Sản phẩm từ database
    2. Text Splitting: Chia đoạn chunk_size=600, overlap=100
    3. Embeddings: Local Sentence Transformers (chạy 100% offline không cần API key)
    4. Vector Store: FAISS vector database lưu cục bộ tại database/faiss_index
    5. Retriever: Truy xuất ngữ cảnh liên quan nhất
    6. LLM Generator: Gọi Local LLM (Ollama hoặc smart synthesizer) trả lời tự nhiên
    """
    def __init__(self):
        self.llm_service = LocalLLMService()
        self.vector_store = None
        self.embeddings = None
        self._init_components()

    def _init_components(self):
        """Khởi tạo Embedding và nạp FAISS vector store nếu đã index sẵn."""
        try:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings

            # Dùng model gọn nhẹ, chất lượng cao, chạy mượt trên CPU lẫn GPU
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        except Exception as e:
            print(f"[RAG] Đang chuẩn bị module embedding: {e}")

        # Thử load FAISS index nếu đã tồn tại
        if os.path.exists(os.path.join(FAISS_DIR, "index.faiss")):
            try:
                from langchain_community.vectorstores import FAISS
                if self.embeddings:
                    self.vector_store = FAISS.load_local(
                        folder_path=FAISS_DIR,
                        embeddings=self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    print("[RAG] Đã tải thành công FAISS Vector Store từ đĩa!")
            except Exception as e:
                print(f"[RAG] Chưa thể nạp FAISS index: {e}")

    def load_all_raw_documents(self) -> List[Document]:
        """
        Nạp toàn bộ tài liệu từ:
        1. Thư mục data/knowledge/*.md, *.txt
        2. Dữ liệu sản phẩm từ data/products.json hoặc SQLite
        """
        docs: List[Document] = []

        # 1. Đọc các file văn bản tri thức
        if os.path.exists(KNOWLEDGE_DIR):
            for ext in ("*.md", "*.txt"):
                for file_path in glob.glob(os.path.join(KNOWLEDGE_DIR, ext)):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read()
                        doc_name = os.path.basename(file_path)
                        docs.append(Document(
                            page_content=text,
                            metadata={"source": doc_name, "type": "knowledge_file"}
                        ))
                    except Exception as e:
                        print(f"[RAG] Lỗi đọc file {file_path}: {e}")

        # 2. Đọc sản phẩm từ database/products.json và biến thành tài liệu có cấu trúc
        products_data = []
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products")
                rows = cursor.fetchall()
                products_data = [dict(r) for r in rows]
                conn.close()
            except Exception as e:
                print(f"[RAG] Lỗi đọc products từ SQLite: {e}")

        if not products_data and os.path.exists(PRODUCTS_FILE):
            try:
                with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                    products_data = json.load(f)
            except Exception as e:
                print(f"[RAG] Lỗi đọc products.json: {e}")

        # Chuyển đổi từng sản phẩm thành một văn bản mô tả ngữ nghĩa chi tiết
        for p in products_data:
            p_id = p.get("id")
            p_code = p.get("code") or f"SP-{p_id}"
            p_name = p.get("name", "")
            p_cat = p.get("category", "")
            p_price = p.get("price", 0)
            p_colors = p.get("colors") or []
            if isinstance(p_colors, str):
                p_colors = [c.strip() for c in p_colors.split(",")]
            p_sizes = p.get("sizes") or []
            if isinstance(p_sizes, str):
                p_sizes = [s.strip() for s in p_sizes.split(",")]
            p_desc = p.get("description", "")
            p_style = p.get("style", "")
            p_gender = p.get("gender", "unisex")

            price_formatted = f"{p_price:,.0f} VNĐ" if p_price else "Liên hệ"
            colors_str = ", ".join(p_colors) if p_colors else "Đa dạng"
            sizes_str = ", ".join(p_sizes) if p_sizes else "Freesize"

            content = (
                f"SẢN PHẨM: {p_name} (Mã: {p_code})\n"
                f"- Danh mục: {p_cat}\n"
                f"- Giá bán: {price_formatted}\n"
                f"- Màu sắc: {colors_str}\n"
                f"- Kích cỡ sẵn có: {sizes_str}\n"
                f"- Dành cho: {p_gender}\n"
                f"- Phong cách / Vibe: {p_style}\n"
                f"- Mô tả sản phẩm: {p_desc}\n"
            )
            docs.append(Document(
                page_content=content,
                metadata={
                    "source": "product_catalog",
                    "type": "product",
                    "product_id": p_id,
                    "product_code": p_code,
                    "product_name": p_name,
                    "category": p_cat,
                    "price": p_price,
                    "colors": colors_str,
                    "sizes": sizes_str,
                    "image": p.get("image", "")
                }
            ))

        print(f"[RAG] Đã thu thập {len(docs)} tài liệu nguồn (văn bản & sản phẩm).")
        return docs

    def split_documents(self, docs: List[Document]) -> List[Document]:
        """Chia nhỏ tài liệu thành các chunks bằng TextSplitter."""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            try:
                # Tương thích ngược với các phiên bản LangChain cũ (< 0.2) qua dynamic import để tránh IDE linter báo lỗi
                import importlib
                _mod = importlib.import_module("langchain.text_splitter")
                RecursiveCharacterTextSplitter = getattr(_mod, "RecursiveCharacterTextSplitter")
            except Exception:
                # Phân đoạn đơn giản nếu chưa có thư viện
                return docs

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=550,
            chunk_overlap=90,
            separators=["\n## ", "\n### ", "\n---\n", "\n\n", "\n", ". ", " ", ""]
        )

        all_chunks: List[Document] = []
        for doc in docs:
            # Nếu là sản phẩm lẻ thì giữ nguyên vẹn để không bị đứt đoạn thông số
            if doc.metadata.get("type") == "product":
                all_chunks.append(doc)
            else:
                chunks = splitter.split_text(doc.page_content)
                for chunk in chunks:
                    all_chunks.append(Document(page_content=chunk, metadata=doc.metadata))

        print(f"[RAG] Đã chia thành {len(all_chunks)} chunks dữ liệu chuẩn.")
        return all_chunks

    def ingest(self, force_rebuild: bool = True) -> int:
        """
        Huấn luyện / Nạp toàn bộ dữ liệu vào FAISS Vector Store.
        Đây chính là quá trình 'tự train dữ liệu' mà bạn mong muốn!
        """
        print("[RAG] Bắt đầu quá trình nạp và embedding dữ liệu tri thức...")
        raw_docs = self.load_all_raw_documents()
        if not raw_docs:
            print("[RAG] Không tìm thấy tài liệu nào để nạp!")
            return 0

        chunks = self.split_documents(raw_docs)

        # Chuyển đổi sang định dạng LangChain Document
        from langchain_core.documents import Document as LCDocument
        lc_docs = [
            LCDocument(page_content=c.page_content, metadata=c.metadata)
            for c in chunks
        ]

        if not self.embeddings:
            self._init_components()

        if not self.embeddings:
            print("[RAG] Lỗi: Chưa nạp được embedding model!")
            return 0

        from langchain_community.vectorstores import FAISS

        # Xây dựng Vector Index
        self.vector_store = FAISS.from_documents(lc_docs, self.embeddings)

        # Lưu index xuống ổ đĩa để tái sử dụng ngay lập tức mà không cần nhúng lại
        os.makedirs(FAISS_DIR, exist_ok=True)
        self.vector_store.save_local(FAISS_DIR)
        print(f"[RAG] 'Train' thành công! FAISS index đã được lưu tại {FAISS_DIR} với {len(lc_docs)} vector.")
        return len(lc_docs)

    def retrieve(self, query: str, top_k: int = 4) -> List[Tuple[Any, float]]:
        """Truy xuất các đoạn văn bản tương đồng nhất với câu hỏi từ FAISS."""
        if not self.vector_store:
            # Thử nạp lại
            self._init_components()

        if not self.vector_store:
            print("[RAG] Vector store chưa sẵn sàng, đang tự động nạp dữ liệu lần đầu...")
            self.ingest()

        if self.vector_store:
            try:
                # Tìm kiếm kèm theo điểm tương đồng
                results = self.vector_store.similarity_search_with_score(query, k=top_k)
                return results
            except Exception as e:
                print(f"[RAG] Lỗi khi truy vấn FAISS: {e}")

        return []

    def extract_related_products(self, retrieved_docs: List[Any], query: str) -> List[Dict[str, Any]]:
       
        found_product_ids = set()
        matched_products: List[Dict[str, Any]] = []

        # 1. Trích xuất từ metadata của các chunks tìm được
        for doc_tuple in retrieved_docs:
            doc = doc_tuple[0] if isinstance(doc_tuple, tuple) else doc_tuple
            meta = getattr(doc, "metadata", {})
            if meta.get("type") == "product" and meta.get("product_id"):
                p_id = meta.get("product_id")
                if p_id not in found_product_ids:
                    found_product_ids.add(p_id)

        # 2. Truy vấn chi tiết sản phẩm từ SQLite
        if found_product_ids and os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in found_product_ids)
                cursor.execute(f"SELECT * FROM products WHERE id IN ({placeholders}) LIMIT 6", list(found_product_ids))
                matched_products = [dict(r) for r in cursor.fetchall()]
                conn.close()
            except Exception as e:
                print(f"[RAG] Lỗi lấy sản phẩm từ DB: {e}")

        # 3. Nếu chưa đủ hoặc RAG tìm ra cẩm nang phối đồ chung, tìm thêm 2-4 sản phẩm bổ trợ theo từ khoá
        if len(matched_products) < 2 and os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                keywords = ["blazer", "sơ mi", "áo thun", "quần", "váy", "đầm", "jean"]
                detected_cat = ""
                for kw in keywords:
                    if kw in query.lower():
                        detected_cat = kw
                        break
                if detected_cat:
                    cursor.execute("""
                        SELECT * FROM products 
                        WHERE LOWER(category) LIKE ? OR LOWER(name) LIKE ?
                        LIMIT 4
                    """, (f"%{detected_cat}%", f"%{detected_cat}%"))
                    extra = [dict(r) for r in cursor.fetchall() if r["id"] not in found_product_ids]
                    matched_products.extend(extra)
                conn.close()
            except Exception:
                pass

        return matched_products

    def query(self, user_message: str) -> Dict[str, Any]:
        
        # 1. Truy xuất tài liệu
        retrieved_results = self.retrieve(user_message, top_k=4)
        
        # Tạo chuỗi ngữ cảnh (Context)
        context_chunks = []
        sources = []
        for item in retrieved_results:
            doc = item[0] if isinstance(item, tuple) else item
            text = getattr(doc, "page_content", str(doc))
            meta = getattr(doc, "metadata", {})
            src = meta.get("source", "Tài liệu cửa hàng")
            if src not in sources:
                sources.append(src)
            context_chunks.append(f"[{src}]\n{text}")

        context_text = "\n\n".join(context_chunks)

        # 2. Xây dựng Prompt chuẩn RAG tách biệt System và Context
        rag_system = (
            "Bạn là Evern AI Stylist. Hãy xưng hô 'mình' và gọi khách là 'bạn'. "
            "Dựa sát vào ngữ cảnh cửa hàng được cung cấp để trả lời thân thiện, chu đáo, súc tích bằng tiếng Việt. "
            "Tuyệt đối không bịa đặt thông tin và không in ra các câu chỉ dẫn hệ thống hay tên file kỹ thuật."
        )
        rag_prompt = (
            f"NGỮ CẢNH CỬA HÀNG:\n{context_text}\n\n"
            f"CÂU HỎI CỦA KHÁCH HÀNG: {user_message}\n\n"
            "Hãy viết câu trả lời tự nhiên gửi đến khách hàng:"
        )

        # 3. Tạo câu trả lời từ Local LLM
        reply = self.llm_service.generate(prompt=rag_prompt, system_prompt=rag_system)
        reply = self.llm_service.clean_llm_response(reply)

        # 4. Trích xuất sản phẩm liên quan để hiển thị dạng thẻ card trên website
        products = self.extract_related_products(retrieved_results, user_message)

        return {
            "reply": reply,
            "products": products,
            "rag_sources": sources,
            "ai_pipeline": "rag_local_llm",
            "ollama_status": self.llm_service.check_ollama_status()
        }

if __name__ == "__main__":
    import sys
    engine = RAGEngine()
    if "--ingest" in sys.argv or "-i" in sys.argv:
        print("[RAG] Tiến hành train / nạp dữ liệu thủ công...")
        engine.ingest(force_rebuild=True)
    else:
        test_q = "Mình cao 1m68 nặng 60kg thì mặc size gì?"
        print(f"\n--- Thử nghiệm câu hỏi: '{test_q}' ---")
        res = engine.query(test_q)
        print("Câu trả lời:\n", res["reply"])
        print("\nSản phẩm tìm thấy:", len(res["products"]))
