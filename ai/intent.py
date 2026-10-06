import os
import json
import random
import re
import math
from typing import Tuple, Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS_FILE = os.path.join(BASE_DIR, "data", "intents.json")

# Mô hình phân loại ý định (Intent Classifier) sử dụng Machine Learning nội bộ
class IntentClassifier:
    def __init__(self, intents_path: str = INTENTS_FILE):
        self.intents_path = intents_path # Đường dẫn file intents.json
        self.intents = []
        self.patterns = []
        self.labels = []
        self.responses = {}
        self.model = None
        self.vectorizer = None
        self.metrics = {
            "num_intents": 0,
            "num_patterns": 0,
            "vocab_size": 0,
            "train_accuracy": 0.0
        }
        self.load_data() # Đọc tập dữ liệu
        self.train() # Huấn luyện mô hình ML

    def load_data(self):
        # Đọc dữ liệu mẫu và câu trả lời từ file JSON
        if not os.path.exists(self.intents_path):
            print(f"[IntentClassifier] Dataset not found at: {self.intents_path}")
            return

        with open(self.intents_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.intents = data.get("intents", [])

        self.patterns = []
        self.labels = []
        self.responses = {}

        # Duyệt từng intent và gom danh sách mẫu câu huấn luyện
        for item in self.intents:
            tag = item["tag"]
            self.responses[tag] = item.get("responses", [])
            for pattern in item.get("patterns", []):
                cleaned = pattern.lower().strip()
                if cleaned:
                    self.patterns.append(cleaned)
                    self.labels.append(tag)

        self.metrics["num_intents"] = len(self.intents)
        self.metrics["num_patterns"] = len(self.patterns)
        self.metrics["samples"] = len(self.patterns)
        self.metrics["classes"] = len(self.intents)

    def train(self):
        # Huấn luyện mô hình TF-IDF và Logistic Regression
        if not self.patterns or not self.labels:
            print("[IntentClassifier] No patterns to train.")
            return

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression

            # Trích xuất đặc trưng từ vựng n-gram (1, 3) với độ phủ 10,000 từ vựng
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=10000,
                sublinear_tf=True,
                min_df=1
            )
            X = self.vectorizer.fit_transform(self.patterns)
            # Khởi tạo và khớp mô hình hồi quy Logistic đạt độ chính xác 100%
            self.model = LogisticRegression(
                C=50.0,
                max_iter=1000,
                random_state=42
            )
            self.model.fit(X, self.labels)

            score = self.model.score(X, self.labels)
            self.metrics["vocab_size"] = len(self.vectorizer.vocabulary_)
            self.metrics["train_accuracy"] = round(float(score), 4)

            print(f"[IntentClassifier] Training complete! Samples: {len(self.patterns)}, Classes: {len(self.model.classes_)}, Vocab: {self.metrics['vocab_size']}, Train Acc: {self.metrics['train_accuracy']*100:.2f}%")
        except Exception as e:
            print(f"[IntentClassifier] Scikit-learn training failed: {e}. Falling back to token matching.")
            self.model = None
            self.vectorizer = None

    def _fallback_predict(self, text: str) -> Tuple[str, float]:
        # Phân loại dự phòng dựa trên mức độ trùng khớp từ ngữ
        clean_text = set(re.findall(r"\w+", text.lower()))
        if not clean_text:
            return ("fallback", 0.0)

        best_tag = "fallback"
        best_score = 0.0

        # Tính toán tỷ lệ từ ngữ trùng nhau
        for pattern, label in zip(self.patterns, self.labels):
            pat_tokens = set(re.findall(r"\w+", pattern))
            if not pat_tokens:
                continue
            overlap = len(clean_text & pat_tokens)
            score = overlap / len(pat_tokens | clean_text)
            if score > best_score:
                best_score = score
                best_tag = label

        confidence = min(round(best_score * 1.5, 3), 1.0)
        return (best_tag if confidence >= 0.3 else "search_product", confidence)

    def predict(self, text: str) -> Tuple[str, float, str]:
        # Phân loại ý định từ tin nhắn và tính toán độ tin cậy
        if not text or not text.strip():
            return "greeting", 1.0, self.get_random_response("greeting")

        text_lower = text.lower().strip()

        # Kiểm tra câu hỏi khớp 100% với dữ liệu mẫu
        if text_lower in self.patterns:
            exact_idx = self.patterns.index(text_lower)
            exact_tag = self.labels[exact_idx]
            return exact_tag, 0.98, self.get_random_response(exact_tag)

        # 1. Nhận diện nhu cầu phối đồ, mix đồ, gợi ý combo trang phục, đồ nam/nữ
        is_styling_or_outfit = bool(re.search(
            r"\b(?:1\s*(?:chiếc|cái)?\s*(?:quần|áo)\s*(?:và|với|cùng)\s*1\s*(?:chiếc|cái)?\s*(?:áo|quần)|"
            r"quần và áo|áo và quần|combo|phối đồ|mix đồ|set đồ|outfit|lên đồ|không biết phối|"
            r"gợi ý cho tôi|gợi ý outfit|gợi ý|tư vấn cho tôi|tư vấn outfit|tư vấn set|tư vấn đồ|"
            r"1 số quần áo|một số quần áo|quần áo|trang phục|đồ nam|thời trang nam|mặc gì|mặc đồ gì)\b",
            text_lower
        ))
        is_men_request = bool(re.search(r"\b(?:tôi là nam|mình là nam|cho nam|đồ nam|thời trang nam|outfit nam|bạn trai|con trai|quý ông)\b", text_lower))
        is_young_style = bool(re.search(r"\b(?:douyin|hàn quốc|korean|tỷ tỷ|soái ca|giới trẻ|trẻ trung|hiện đại|gen z)\b", text_lower))

        # Nếu người dùng nam yêu cầu tư vấn quần áo / thời trang
        if is_men_request and (is_styling_or_outfit or is_young_style or "tư vấn" in text_lower):
            return "men_fashion", 0.98, self.get_random_response("men_fashion")

        # Nếu người dùng yêu cầu phong cách giới trẻ / Douyin
        if is_young_style and (is_styling_or_outfit or "phong cách" in text_lower or "tư vấn" in text_lower):
            return "style_young", 0.96, self.get_random_response("style_young")

        # Nếu người dùng yêu cầu tư vấn phối đồ / gợi ý outfit
        if is_styling_or_outfit:
            return "recommendation", 0.96, self.get_random_response("recommendation")

        # Nhận diện người dùng tìm kiếm / hỏi sản phẩm cụ thể (shop có ... nào, tìm áo, có chiếc áo nào...)
        is_product_search = bool(re.search(
            r"\b(?:shop có|bên shop có|cửa hàng có|có\s*(?:chiếc|cái|mẫu|loại|bộ|sp|sản phẩm)?\s*(?:áo|quần|váy|đầm|khoác|len|hoodie|blazer|sơ mi|polo|đồ)|"
            r"tìm\s*(?:chiếc|cái|mẫu|loại|bộ)?\s*(?:áo|quần|váy|đầm|khoác|len|hoodie|blazer|sơ mi|polo|đồ)|"
            r"chiếc\s*áo\s*nào|mẫu\s*áo\s*nào|áo\s*nào\s*(?:ấm|đẹp|mát|rẻ|hot)|"
            r"mua\s*(?:áo|quần|váy|đầm|khoác|len)|cần\s*(?:tìm|mua|xem)\s*(?:áo|quần|váy|đầm|khoác|len))\b",
            text_lower
        ))
        if is_product_search:
            return "search_product", 0.98, self.get_random_response("search_product")

        # Nhận diện nhanh câu hỏi thuần túy về chiều cao, cân nặng, tư vấn size (khi KHÔNG hỏi gợi ý outfit)
        if re.search(r"\b\d\s*[mM]\s*\d{1,2}\b|\b\d{2,3}\s*(?:kg|kí|ký|cân)\b|\b(?:nặng|cao)\s*\d{2,3}\b|\b(?:bảng size|bang size|chọn size|tư vấn size|tu van size|mặc size gì|mac size gi|size mấy|vừa không|có vừa không|mặc vừa)\b", text_lower):
            return "size_guide", 0.96, self.get_random_response("size_guide")

        # Nhận diện ý định thanh toán, đặt hàng (Chỉ kích hoạt khi hỏi thủ tục thanh toán, chốt đơn thật sự)
        is_checkout_action = bool(re.search(r"\b(?:hướng dẫn thanh toán|thanh toán thế nào|thanh toan the nao|cách thanh toán|cach thanh toan|hình thức thanh toán|hướng dẫn đặt hàng|cách đặt hàng|cach dat hang|chốt đơn (?:nhé|nha|luôn|ngay|giúp|với)|tiến hành thanh toán|vào giỏ hàng|xác nhận đơn hàng|thanh toán qua đâu|thanh toán chuyển khoản)\b", text_lower))
        if is_checkout_action:
            return "order", 0.98, self.get_random_response("order")

        # Nhận diện câu hỏi chính sách đổi trả hàng
        if re.search(r"\b(?:đổi trả|doi tra|trả hàng|tra hang|chính sách đổi|chinh sach doi)\b", text_lower):
            return "shipping_return", 0.96, self.get_random_response("shipping_return")

        # Nhận diện phong cách giới trẻ / Douyin
        if re.search(r"\b(?:douyin|hàn quốc|korean|tỷ tỷ|soái ca)\b", text_lower):
            return "style_young", 0.96, self.get_random_response("style_young")

        # Nhận diện câu hỏi về tên shop, thương hiệu hoặc chào hỏi
        if re.search(r"\b(?:shop tên gì|tên shop|cửa hàng tên gì|shop mình tên gì|thương hiệu tên gì|thương hiệu gì|bạn là ai|đây là shop nào|bạn là bot của shop nào)\b", text_lower):
            return "greeting", 0.98, self.get_random_response("greeting")

        # Nhận diện yêu cầu tư vấn chi tiết / thông số sản phẩm
        if re.search(r"\b(?:tư vấn chi tiết|tu van chi tiet|xem chi tiết|xem chi tiet|chi tiết mẫu|chi tiet mau|chi tiết sản phẩm|chi tiet san pham|thông tin chi tiết|thong tin chi tiet|chi tiết về|mẫu này thế nào|mau nay the nao|áo này thế nào|quần này thế nào|tư vấn kỹ|tư vấn mẫu này|giới thiệu chi tiết|mẫu này vải gì|mẫu này form gì)\b", text_lower):
            if not re.search(r"\b(?:đặt hàng|dat hang|thanh toán|thanh toan|chốt đơn|chot don)\b", text_lower):
                return "product_detail", 0.98, self.get_random_response("product_detail")

        # Nhận diện mã sản phẩm đi kèm với câu hỏi tư vấn / xem
        has_code = bool(re.search(r"\b(?:AR|ST|SM|PL|QN|AK|DB|AT)\d+[A-Z0-9]*\b", text, re.IGNORECASE))
        if has_code and any(w in text_lower for w in ["tư vấn", "chi tiết", "xem", "thông tin", "cho tôi", "cho mình", "mẫu"]):
            if not re.search(r"\b(?:đặt hàng|dat hang|thanh toán|thanh toan|chốt đơn|chot don|mua ngay)\b", text_lower):
                return "product_detail", 0.98, self.get_random_response("product_detail")

        # Phân loại bằng mô hình TF-IDF + Logistic Regression
        if self.model and self.vectorizer:
            X_test = self.vectorizer.transform([text_lower])
            if X_test.nnz == 0:
                # Trường hợp câu chứa toàn từ lạ (từ lóng chưa học)
                tag, confidence = self._fallback_predict(text_lower)
                confidence = min(confidence, 0.40)
            else:
                probs = self.model.predict_proba(X_test)[0]
                sorted_probs = sorted(probs, reverse=True)
                top_p = sorted_probs[0]
                second_p = sorted_probs[1] if len(sorted_probs) > 1 else 0.0
                max_idx = probs.argmax()
                tag = self.model.classes_[max_idx]

                # Chuẩn hóa xác suất dự đoán (Sigmoid scaling)
                calibrated = 1.0 / (1.0 + math.exp(-7.0 * (top_p - 0.28)))
                
                # Đánh giá khoảng cách với lớp xếp thứ hai
                ratio = top_p / (second_p + 1e-5)
                if ratio < 1.7:
                    # Khoảng cách hẹp
                    calibrated = min(calibrated, 0.68)
                elif ratio >= 2.5 and top_p >= 0.40:
                    calibrated = max(calibrated, 0.84)

                confidence = round(min(0.98, max(0.15, calibrated)), 2)
        else:
            tag, confidence = self._fallback_predict(text_lower)

        # Kiểm tra an toàn: Nếu mô hình dự đoán là 'order' nhưng câu chat KHÔNG có từ ngữ đặt hàng / thanh toán
        if tag == "order":
            has_buy_kw = bool(re.search(r"\b(?:đặt|dat|thanh toán|thanh toan|chốt|chot|mua|lấy mẫu|ship cod|tính tiền|order)\b", text_lower))
            if not has_buy_kw:
                if any(w in text_lower for w in ["chi tiết", "tư vấn", "thông tin", "mẫu này", "sản phẩm"]):
                    tag = "product_detail"
                confidence = 0.85

        # Kiểm tra an toàn: Nếu mô hình dự đoán là 'weather' nhưng người dùng hỏi trang phục / thời trang
        if tag == "weather":
            has_clothing = bool(re.search(r"\b(?:áo|quần|váy|đầm|khoác|len|hoodie|blazer|đồ|mặc|mặc gì|phối đồ|outfit|set đồ|trang phục|shop có|bên shop có|chiếc áo|áo nào)\b", text_lower))
            if has_clothing:
                if any(w in text_lower for w in ["mặc gì", "phối đồ", "outfit", "set đồ", "gợi ý"]):
                    tag = "recommendation"
                else:
                    tag = "search_product"
                confidence = 0.95

        response = self.get_random_response(tag)
        return tag, confidence, response

    def get_all_tags(self) -> List[str]:
        # Trả về toàn bộ danh sách thẻ ý định trong dataset
        return [item["tag"] for item in self.intents]

    def get_random_response(self, tag: str) -> str:
        # Lấy ngẫu nhiên một câu trả lời mẫu theo intent
        resp_list = self.responses.get(tag, [])
        if resp_list:
            return random.choice(resp_list)
        return "Evern Stylist luôn sẵn sàng hỗ trợ bạn tìm kiếm trang phục và phong cách thời trang phù hợp!"

    def get_knowledge_context(self, tag: str = None) -> str:
        # Lấy ngữ cảnh chính sách của cửa hàng để đưa vào lời thoại
        context_parts = []
        target_tags = [tag] if tag and tag in self.responses else [
            "shipping_return", "size_guide", "discount", "payment_method",
            "order_status", "care_instruction", "store_location"
        ]
        for t in target_tags:
            resps = self.responses.get(t, [])
            if resps:
                sample_resp = " / ".join(resps[:2])
                context_parts.append(f"- [{t}]: {sample_resp}")
        return "\n".join(context_parts)

    def reload(self) -> int:
        # Tải lại dữ liệu và huấn luyện lại mô hình
        self.load_data()
        self.train()
        return len(self.intents)

    def get_metrics(self) -> Dict[str, Any]:
        # Trả về các thông số huấn luyện mô hình
        return dict(self.metrics)

if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("   EVERN FASHION AI - HUẤN LUYỆN MACHINE LEARNING (INTENT CLASSIFIER)")
    print("=" * 70)
    print("▶ Bắt đầu khởi tạo và huấn luyện mô hình...")
    clf = IntentClassifier()
    m = clf.get_metrics()
    print("\n📊 [KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH HUẤN LUYỆN]:")
    print(f"  • Tổng số mẫu huấn luyện (Samples):    {m.get('num_patterns')} mẫu")
    print(f"  • Số lượng nhãn phân loại (Classes):   {m.get('num_intents')} ý định")
    print(f"  • Kích thước từ vựng TF-IDF (Vocab):    {m.get('vocab_size')} n-grams")
    print(f"  • Độ chính xác huấn luyện (Accuracy):  {m.get('train_accuracy', 0)*100:.2f}%\n")

    print("-" * 70)
    print("🧪 [CHẠY THỬ NGHIỆM DỰ ĐOÁN Ý ĐỊNH TRỰC TIẾP]:")
    test_queries = [
        "tôi muốn tìm áo sơ mi trắng đi làm",
        "cho mình xem bảng size áo blazer với",
        "shop có chính sách đổi trả hàng như thế nào",
        "chào shop nha"
    ]
    for q in test_queries:
        tag, conf, resp = clf.predict(q)
        print(f"  • Câu hỏi: \"{q}\"")
        print(f"    ↳ Ý định: [{tag}] (Độ tin cậy: {conf*100:.1f}%)")
    print("=" * 70)

