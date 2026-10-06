import os
import sys
import re
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from ai.db_functions import FashionDBService
from ai.entity import EntityExtractor
from ai.intent import IntentClassifier
from ai.local_llm import LocalLLMService
from ai.response_generator import ResponseGenerator
from ai.recommendation import FashionRecommender
from ai.rag_engine import RAGEngine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")

class FashionChatbot:
    """
    Hệ thống Chatbot AI Stylist cho Evern Fashion (100% Local & Privacy - 0đ API Key):
    - Truy cập trực tiếp CSDL SQLite (bảng products) để tìm kiếm và trả về sản phẩm thật (kèm thẻ Card hình ảnh, giá, size).
    - Sử dụng Local LLM (Ollama - Qwen 2.5 hoặc model tự train) để sinh lời tư vấn chuyên sâu, tự nhiên bám sát sản phẩm từ Database.
    - Dự phòng tự động bằng Bộ sinh lời ResponseGenerator cục bộ, cam kết 100% không bao giờ gặp lỗi gián đoạn.
    - RAG Engine truy xuất thông tin chính sách, cẩm nang phối đồ và bảng size (tự động làm sạch tên file .md).
    - Hoàn toàn KHÔNG phụ thuộc vào Google Gemini hay bất kỳ API Key trả phí bên ngoài nào.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db_service = FashionDBService(db_path)
        self.recommender = FashionRecommender(db_path)
        self.intent_classifier = IntentClassifier()
        self.llm_service = LocalLLMService()
        self.rag_engine = RAGEngine()
        # Bộ nhớ ngữ cảnh hội thoại đa lượt (Multi-turn Context Memory)
        self.session_contexts: Dict[str, Dict[str, Any]] = {}

    def reload_intents(self) -> int:
        """Nạp lại tập mẫu intent và index RAG."""
        self.intent_classifier.load_data()
        self.intent_classifier.train()
        count = self.rag_engine.ingest(force_rebuild=True)
        print(f"[Chatbot] Đã cập nhật thành công Intent Classifier và {count} vector tri thức.")
        return count

    def reindex_rag(self) -> int:
        """Nạp và 'train' lại tri thức RAG."""
        return self.reload_intents()

    def get_model_metrics(self) -> Dict[str, Any]:
        """Trả về thông số trạng thái hệ thống AI Local."""
        status = self.llm_service.check_ollama_status()
        return {
            "primary_ai": "SQLite Database Product Search + Local LLM (Ollama)",
            "local_model": status.get("selected_model", "qwen2.5:1.5b"),
            "ollama_running": status.get("running", False),
            "available_models": status.get("models", []),
            "fallback_ai": "ResponseGenerator Local Rules (0.001s)",
            "api_key_required": False,
            "cost": "0 VNĐ (100% Local & Privacy)",
            "db_path": self.db_path
        }

    def log_chat(self, user_message: str, bot_response: str, intent: str = "search_product", user_id: Optional[int] = None):
        """Lưu lịch sử hội thoại vào CSDL SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (user_id, user_message, bot_response, intent)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_message, bot_response, intent))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Chatbot] Error logging conversation: {e}")

    def _get_session_key(self, user_id: Optional[int], session_id: Optional[str]) -> str:
        if user_id:
            return f"user_{user_id}"
        if session_id:
            return f"session_{session_id}"
        return "default_guest"

    def _get_context(self, session_key: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Lấy ngữ cảnh hội thoại đa lượt của người dùng (từ RAM hoặc CSDL SQLite)."""
        if session_key not in self.session_contexts:
            self.session_contexts[session_key] = {
                "turns": [],
                "last_products": [],
                "active_product": None,
                "last_intent": None,
                "last_entities": {}
            }
            if user_id:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT user_message, bot_response, intent 
                        FROM chat_history 
                        WHERE user_id = ? 
                        ORDER BY id DESC LIMIT 3
                    """, (user_id,))
                    rows = cursor.fetchall()
                    conn.close()
                    for u_msg, b_resp, it in reversed(rows):
                        self.session_contexts[session_key]["turns"].append({"role": "user", "text": u_msg})
                        self.session_contexts[session_key]["turns"].append({"role": "bot", "text": b_resp})
                except Exception as e:
                    print(f"[Chatbot] Error loading user chat history into context: {e}")

        return self.session_contexts[session_key]

    def _update_context(
        self,
        session_key: str,
        user_message: str,
        bot_response: str,
        intent: str,
        products: List[Dict[str, Any]],
        entities: Dict[str, Any]
    ):
        """Cập nhật bộ nhớ ngữ cảnh sau mỗi lượt chat."""
        ctx = self._get_context(session_key)
        ctx["turns"].append({"role": "user", "text": user_message})
        ctx["turns"].append({"role": "bot", "text": bot_response})
        if len(ctx["turns"]) > 6:
            ctx["turns"] = ctx["turns"][-6:]

        if products:
            ctx["last_products"] = products
            ctx["active_product"] = products[0]
        elif intent in ["out_of_scope", "greeting", "goodbye", "store_location", "payment_method", "shipping_return", "care_instruction"]:
            # Khi người dùng chuyển sang câu hỏi ngoài lề hoặc chính sách chung: giải phóng sản phẩm đang ghim
            ctx["last_products"] = []
            ctx["active_product"] = None
        elif not any(w in user_message.lower() for w in ["mẫu này", "áo này", "quần này", "váy này", "đầm này", "nó", "cái này"]):
            # Người dùng chuyển sang câu hỏi khác không dùng đại từ: xóa sản phẩm ghim cũ để không bị dính sang lượt sau
            ctx["last_products"] = []
            ctx["active_product"] = None

        ctx["last_intent"] = intent
        ctx["last_entities"] = {k: v for k, v in entities.items() if v}

    def clear_context(self, user_id: Optional[int] = None, session_id: Optional[str] = None):
        """Xóa sạch bộ nhớ ngữ cảnh tạm."""
        key = self._get_session_key(user_id, session_id)
        if key in self.session_contexts:
            del self.session_contexts[key]

    def _check_out_of_scope(self, user_message: str) -> Tuple[bool, str]:
        """
        Phát hiện các câu hỏi hoàn toàn nằm ngoài phạm vi thời trang của Evern Fashion:
        1. Thiết bị cơ khí / máy móc: máy khoan, máy mài, máy cắt, máy hàn, cờ lê, tua vít, bosch, makita...
        2. Đồ công nghệ / điện máy / gia dụng: điện thoại, laptop, tivi, tủ lạnh, máy giặt, xe máy...
        3. Sách / văn học / so sánh sách: sách ikigai, clean code, đắc nhân tâm, truyện tranh...
        4. Lập trình / IT / toán học: viết code python, giải toán, bài tập...
        5. Đồ ăn thức uống / dược phẩm: hỏi mua trà sữa, bánh mì, thuốc...
        """
        msg_l = user_message.lower().strip()

        # 1. Cơ khí, dụng cụ máy móc
        mech_patterns = [
            r"\b(?:máy khoan|may khoan|máy mài|may mai|máy cắt|may cat|máy hàn|may han|máy cưa|may cua)\b",
            r"\b(?:mũi khoan|mui khoan|búa|cờ lê|co le|tua vít|tuavit|tô vít|kìm|mỏ lết|máy bắn vít)\b",
            r"\b(?:bosch|makita|dewalt|stanley|milwaukee|ingco|total)\b"
        ]
        for pat in mech_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion là thương hiệu thời trang thiết kế chuyên về các dòng trang phục (áo sơ mi, áo polo, áo thun, áo khoác, quần tây, quần jean, đầm váy và phụ kiện thời trang) ạ. ✨\n\n"
                    "Hiện tại showroom bên mình **không kinh doanh máy móc hay dụng cụ cơ khí** này nha! 😊 "
                    "Nếu bạn đang có nhu cầu tìm kiếm trang phục thời trang để đi làm, dạo phố hay dự tiệc thì cứ chia sẻ với mình nhé! ❤️"
                )

        # 2. Sách và tác phẩm văn học / giáo dục (như Ikigai, Clean Code, v.v.)
        book_patterns = [
            r"\b(?:sách|cuốn sách|quyển sách|tiểu thuyết|truyện tranh|manga|giáo trình)\b",
            r"\b(?:ikigai|clean code|đắc nhân tâm|dac nhan tam|nhà giả kim|nha gia kim|hạt giống tâm hồn)\b"
        ]
        has_book_kw = any(re.search(pat, msg_l) for pat in book_patterns)
        if has_book_kw and any(w in msg_l for w in ["so sánh", "so sanh", "tóm tắt", "tom tat", "review", "nội dung", "đọc", "tác giả", "bán sách", "mua sách"]):
            return True, (
                "Dạ mình là Evern Stylist - trợ lý AI chuyên về tư vấn thời trang và định hình phong cách cho Evern Fashion thôi ạ! ✨\n\n"
                "Nội dung về các đầu sách nằm ngoài dữ liệu thời trang của mình nên mình chưa thể hỗ trợ so sánh hay review được. "
                "Nếu bạn cần gợi ý outfit thoải mái để đọc sách, cafe cuối tuần hay đi làm, đi chơi thì mình luôn sẵn sàng đồng hành cùng bạn nha! 😊"
            )

        # 3. Đồ công nghệ, điện tử, gia dụng, phương tiện
        tech_patterns = [
            r"\b(?:điện thoại|iphone|ipad|samsung galaxy|xiaomi|oppo|macbook|laptop|máy tính bàn|pc gaming|card màn hình|vga|rtx|cpu|ram)\b",
            r"\b(?:chuột máy tính|bàn phím cơ|bàn phím gaming|razer|logitech|airpods|tai nghe bluetooth)\b",
            r"\b(?:tủ lạnh|máy giặt|điều hòa|máy lạnh|nồi cơm điện|lò vi sóng|bếp từ|máy hút bụi|máy lọc nước)\b",
            r"\b(?:xe máy|ô tô|xe đạp|honda sh|vespa|vinfast)\b"
        ]
        for pat in tech_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion là cửa hàng chuyên về thời trang nam nữ cao cấp ạ. ✨\n\n"
                    "Hiện tại shop không kinh doanh các thiết bị điện tử, công nghệ hay phương tiện này. "
                    "Bạn có muốn mình tư vấn các mẫu quần áo thời trang, set đồ mới về cực hot của Evern không nhé! ❤️"
                )

        # 4. Lập trình, IT, toán học, khoa học
        it_math_patterns = [
            r"\b(?:viết code|viet code|lập trình|lap trinh|code python|code javascript|code java|code c\+\+|html|reactjs|database|sql query)\b",
            r"\b(?:giải toán|giai toan|phương trình|tích phân|đạo hàm|bài tập toán)\b",
            r"^\s*\d+\s*[\+\-\*\/]\s*\d+\s*(?:bằng mấy|\=|\?)*\s*$"
        ]
        for pat in it_math_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist là trợ lý ảo chuyên trách tư vấn thời trang và thẩm mỹ trang phục của Evern Fashion ạ! ✨\n\n"
                    "Các câu hỏi về lập trình, toán học hay kỹ thuật nằm ngoài phạm vi chuyên môn của mình. "
                    "Hãy chia sẻ với mình về phong cách ăn mặc hoặc sự kiện bạn sắp tham gia để mình lên đồ chuẩn đẹp nhất cho bạn nhé! 😊"
                )

        # 5. Đồ ăn thức uống (khi hỏi mua tại shop)
        food_patterns = [
            r"\b(?:bán|mua|ship|giao)\s+(?:trà sữa|cà phê|cafe|bánh mì|cơm|bún|phở|gà rán|pizza|đồ ăn|thức uống)\b",
            r"\b(?:trà sữa|bánh mì|cơm tấm|bún bò|phở bò)\s+(?:không|ko|bao nhiêu)\b"
        ]
        for pat in food_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion là shop thời trang quần áo chứ không kinh doanh đồ ăn, nước uống ạ! 😄\n\n"
                    "Nếu bạn chuẩn bị đi cafe hay hẹn hò ăn uống cuối tuần mà chưa biết mặc gì cho xinh thì cứ nhắn mình tư vấn outfit liền nha! ✨"
                )

        # 6. Dược phẩm, y tế
        med_patterns = [
            r"\b(?:thuốc tây|thuốc kháng sinh|panadol|paracetamol|thuốc cảm|khám bệnh|chữa bệnh)\b"
        ]
        for pat in med_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion là thương hiệu thời trang và không bán các sản phẩm y tế hay thuốc men ạ! "
                    "Bạn cần tư vấn trang phục giữ ấm thời trang hay set đồ nào khác thì cứ nhắn mình hỗ trợ nhé! ❤️"
                )

        # 7. Đồ lót / Nội y (Evern Fashion hiện tại không kinh doanh)
        is_fleece_lining = any(w in msg_l for w in ["lót lông", "lot long", "lót nỉ", "lot ni", "lót bông", "lot bong"])
        underwear_patterns = [
            r"\b(?:quần sịp|quan sip|sịp|sip|quần lót|quan lot|đồ lót|do lot|quần xì|quan xi|boxer|sịp đùi|sịp chéo|quần lọt khe|thong)\b",
            r"\b(?:áo lót|ao lot|áo ngực|ao nguc|bra|bralette|nội y|noi y)\b"
        ]
        if not is_fleece_lining:
            for pat in underwear_patterns:
                if re.search(pat, msg_l):
                    return True, (
                        "Dạ hiện tại Evern Fashion **chưa kinh doanh dòng sản phẩm đồ lót / nội y** (quần sịp, boxer, quần lót, áo lót) ạ! 😊\n\n"
                        "Showroom bên mình chuyên sâu về các dòng **trang phục thời trang thiết kế cao cấp** gồm:\n"
                        "• **Áo:** Áo sơ mi công sở/casual, áo polo dệt kim & cotton, áo thun phông trẻ trung, áo khoác (blazer, jeans, bomber, măng tô).\n"
                        "• **Quần:** Quần tây/âu thanh lịch, quần jeans tôn dáng (ống suông, ống loe, baggy), quần kaki/chinos, quần short.\n"
                        "• **Váy & Đầm:** Đầm tiệc/dạ hội sang trọng, đầm hoa dạo phố, chân váy và đầm ngủ lụa satin cao cấp.\n"
                        "• **Phụ kiện:** Giày sneaker retro, giày loafer da thật, thắt lưng da, ví da...\n\n"
                        "Nếu bạn đang muốn tìm các mẫu quần áo thời trang đi làm, đi chơi hay đi tiệc thì cứ nhắn mình tư vấn liền nha! ❤️"
                    )

        # 8. Đồ bơi / bikini
        swimwear_patterns = [
            r"\b(?:đồ bơi|do boi|bikini|áo tắm|ao tam|quần bơi|quan boi|monokini)\b"
        ]
        for pat in swimwear_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ hiện tại Evern Fashion **chưa kinh doanh dòng sản phẩm đồ bơi / bikini** ạ! 😊\n\n"
                    "Nếu bạn đang chuẩn bị đi biển hay du lịch nghỉ dưỡng, mình có rất nhiều mẫu **áo sơ mi linen mỏng nhẹ, áo thun phông, quần short đi biển hoặc đầm maxi** cực kỳ thoáng mát và lên hình siêu đẹp luôn nè! ✨ "
                    "Bạn có muốn mình gợi ý vài set đồ đi biển không nhé? ❤️"
                )

        # 9. Mỹ phẩm, đồ trang điểm, nước hoa
        cosmetic_patterns = [
            r"\b(?:son môi|son moi|nước hoa|nuoc hoa|perfume|kem chống nắng|kem dưỡng|kem duong|mỹ phẩm|my pham|mascara|phấn phủ|toner)\b"
        ]
        for pat in cosmetic_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion là thương hiệu chuyên về trang phục thời trang và giày/phụ kiện chứ **không kinh doanh mỹ phẩm hay nước hoa** ạ! ✨\n\n"
                    "Showroom có sẵn rất nhiều mẫu áo quần, đầm váy và set đồ chuẩn đẹp để bạn phối đồ thật xinh. Bạn cần tư vấn trang phục cho dịp nào thì cứ chia sẻ với mình nhé! ❤️"
                )
        # Nếu câu hỏi thể hiện rõ nhu cầu tư vấn thời trang, trang phục, phối đồ
        # (dù có chứa từ ngữ bối cảnh như sinh viên, đi học, du lịch, phỏng vấn, ngân hàng, gym...)
        # thì BỎ QUA các bộ lọc ngữ cảnh bên dưới để hệ thống vào luồng tư vấn Outfit/Sản phẩm chuẩn xác:
        has_fashion_intent = any(kw in msg_l for kw in [
            "quần áo", "quan ao", "trang phục", "trang phuc", "outfit", "set đồ", "set do", 
            "lên đồ", "len do", "phối đồ", "phoi do", "mặc gì", "mac gi", "mặc đồ", "mac do",
            "tư vấn", "tu van", "gợi ý đồ", "chọn đồ", "thời trang", "thoi trang", "hợp túi tiền",
            "túi tiền", "giá sinh viên", "áo", "quần", "váy", "đầm", "chân váy", "khoác", "blazer", "polo", "sơ mi"
        ])
        if has_fashion_intent:
            return False, ""

        finance_patterns = [
            r"\b(?:ngân hàng|bank|vietcombank|techcombank|mb bank|bidv|agribank|acb|vpbank|tpbank)\b",
            r"\b(?:chuyển khoản|chuyen khoan|tài khoản ngân hàng|stk|số tài khoản|sao kê)\b",
            r"\b(?:thẻ tín dụng|the tin dung|credit card|debit card|atm|rút tiền|nạp tiền)\b",
            r"\b(?:vay tiền|vay vốn|lãi suất|khoản vay|trả góp)\b",
            r"\b(?:chứng khoán|cổ phiếu|cổ phiếu|stock|forex|đầu tư)\b",
            r"\b(?:bitcoin|btc|ethereum|eth|crypto|tiền điện tử|coin|usdt)\b",
            r"\b(?:ví momo|momo|zalopay|shopeepay|paypal)\b",
        ]

        for pat in finance_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion là cửa hàng chuyên về thời trang nên mình không hỗ trợ "
                    "các vấn đề về ngân hàng, đầu tư, chứng khoán hay tiền điện tử ạ! 💳\n\n"
                    "Nếu bạn muốn tìm sản phẩm thời trang theo ngân sách cụ thể thì mình có thể "
                    "giúp bạn lọc mẫu phù hợp nha! ✨"
                )


        real_estate_patterns = [
            r"\b(?:bất động sản|bat dong san|nhà đất|mua đất|bán đất|đất nền)\b",
            r"\b(?:căn hộ|chung cư|apartment|condo|penthouse|villa|biệt thự)\b",
            r"\b(?:thuê nhà|mua nhà|bán nhà|cho thuê nhà|phòng trọ)\b",
            r"\b(?:giá đất|giá nhà|giá chung cư|diện tích đất|sổ đỏ|sổ hồng)\b",
        ]

        for pat in real_estate_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion chuyên về thời trang nên không kinh doanh "
                    "nhà đất, căn hộ hay bất động sản ạ! 🏠\n\n"
                    "Nếu bạn đang tìm outfit để đi xem nhà, gặp khách hàng hoặc đi làm "
                    "thì mình có thể tư vấn cho bạn nhé! ✨"
                )


        travel_patterns = [
            r"\b(?:đặt vé máy bay|vé máy bay|flight|chuyến bay|bay từ|bay đến)\b",
            r"\b(?:đặt phòng|khách sạn|hotel|resort|homestay|airbnb)\b",
            r"\b(?:tour du lịch|tour|lịch trình du lịch|itinerary)\b",
            r"\b(?:visa|hộ chiếu|passport|thị thực)\b",
            r"\b(?:booking|đặt xe|thuê xe|vé tàu|vé xe khách)\b",
            r"\b(?:địa điểm du lịch|đi đâu chơi|ăn gì ở|check in ở đâu)\b",
        ]

        for pat in travel_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không cung cấp dịch vụ đặt vé, khách sạn hay tour du lịch ạ! ✈️\n\n"
                    "Tuy nhiên nếu bạn đang chuẩn bị đi du lịch thì mình có thể tư vấn "
                    "outfit phù hợp với thời tiết, địa điểm và phong cách bạn muốn nha! 👕✨"
                )




        sports_patterns = [
            r"\b(?:bóng đá|football|soccer|fifa|world cup|champions league)\b",
            r"\b(?:bóng rổ|basketball|nba)\b",
            r"\b(?:tennis|cầu lông|badminton|bơi lội|bơi)\b",
            r"\b(?:gym|tập gym|fitness|workout|cardio)\b",
            r"\b(?:yoga|pilates|chạy bộ|marathon)\b",
            r"\b(?:cầu thủ|huấn luyện viên|trận đấu|tỷ số|bảng xếp hạng)\b",
        ]

        for pat in sports_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không cung cấp thông tin chuyên môn về thể thao "
                    "hay kết quả thi đấu ạ! ⚽\n\n"
                    "Nếu bạn đang cần đồ mặc khi tập gym, chạy bộ, đi chơi thể thao "
                    "thì mình có thể gợi ý trang phục phù hợp nha! 👟"
                )


        game_patterns = [
            r"\b(?:game|gaming|esports|e sport)\b",
            r"\b(?:liên quân|lien quan|valorant|lol|league of legends|pubg|free fire)\b",
            r"\b(?:minecraft|roblox|genshin|genshin impact|pokemon)\b",
            r"\b(?:steam|playstation|xbox|nintendo)\b",
            r"\b(?:tướng|hero|skin|rank|leo rank|đội hình|build đồ)\b",
        ]

        for pat in game_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist không phải trợ lý chuyên về game hay esports ạ! 🎮\n\n"
                    "Nếu bạn muốn tìm outfit theo vibe gaming, streetwear, Y2K "
                    "hoặc outfit đi sự kiện game thì mình vẫn tư vấn được nha! ✨"
                )


        entertainment_patterns = [
            r"\b(?:phim|movie|cinema|rạp phim|box office)\b",
            r"\b(?:anime|manga|manhwa|comic|truyện tranh)\b",
            r"\b(?:netflix|disney|hbo|prime video)\b",
            r"\b(?:diễn viên|đạo diễn|nhân vật phim|review phim)\b",
            r"\b(?:spoiler|nội dung phim|phim hay|phim mới)\b",
        ]

        for pat in entertainment_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist tập trung vào thời trang nên không hỗ trợ "
                    "review hay phân tích phim, anime hoặc manga ạ! 🎬\n\n"
                    "Nếu bạn muốn tìm outfit lấy cảm hứng từ nhân vật hoặc phong cách "
                    "anime, Hàn Quốc, Nhật Bản thì mình có thể hỗ trợ nha! ✨"
                )


        music_patterns = [
            r"\b(?:bài hát|bài nhạc|ca sĩ|singer|album|concert)\b",
            r"\b(?:spotify|youtube music|apple music)\b",
            r"\b(?:nhạc việt|nhạc trung|kpop|cpop|jpop|usuk)\b",
            r"\b(?:rap|rapper|hiphop|kpop idol|idol)\b",
            r"\b(?:lời bài hát|lyrics|nghe nhạc|playlist)\b",
        ]

        for pat in music_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist không chuyên về âm nhạc hay thông tin ca sĩ ạ! 🎵\n\n"
                    "Nếu bạn muốn chọn outfit đi concert, gặp idol hoặc theo vibe "
                    "K-pop, C-pop, J-pop thì mình có thể tư vấn nhé! ✨"
                )


        beauty_patterns = [
            r"\b(?:mỹ phẩm|my pham|cosmetic|makeup|trang điểm)\b",
            r"\b(?:son|phấn|kem nền|foundation|mascara|eyeliner)\b",
            r"\b(?:skincare|chăm sóc da|serum|toner|kem dưỡng|sữa rửa mặt)\b",
            r"\b(?:mụn|da dầu|da khô|da nhạy cảm)\b",
            r"\b(?:nước hoa|perfume|fragrance)\b",
            r"\b(?:dầu gội|sữa tắm|kem chống nắng)\b",
        ]

        for pat in beauty_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion tập trung vào quần áo và phụ kiện thời trang "
                    "nên không kinh doanh mỹ phẩm hay sản phẩm skincare ạ! 💄\n\n"
                    "Nếu bạn muốn phối outfit với makeup, màu son hoặc vibe tổng thể "
                    "thì mình có thể tư vấn phần trang phục cho bạn nha! ✨"
                )


        pet_patterns = [
            r"\b(?:chó|mèo|cún|boss|pet|thú cưng)\b",
            r"\b(?:thức ăn cho chó|thức ăn cho mèo|hạt cho mèo|pate cho mèo)\b",
            r"\b(?:chuồng|lồng|đồ chơi cho chó|đồ chơi cho mèo)\b",
            r"\b(?:bác sĩ thú y|thú y|tiêm phòng cho chó|tiêm phòng cho mèo)\b",
        ]

        for pat in pet_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh sản phẩm dành cho thú cưng ạ! 🐶🐱\n\n"
                    "Shop hiện tập trung vào thời trang và phụ kiện cho khách hàng."
                )


        home_patterns = [
            r"\b(?:bàn ghế|sofa|ghế sofa|giường ngủ|tủ quần áo)\b",
            r"\b(?:nội thất|noi that|decor|trang trí nhà|đồ gia dụng)\b",
            r"\b(?:đèn ngủ|đèn bàn|đèn trang trí|rèm cửa)\b",
            r"\b(?:bàn làm việc|ghế làm việc|kệ sách|tủ lạnh|máy giặt)\b",
        ]

        for pat in home_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh nội thất hay đồ trang trí nhà cửa ạ! 🏠\n\n"
                    "Nếu bạn đang tìm đồ mặc ở nhà, đồ ngủ hoặc outfit tối giản "
                    "thì mình có thể tư vấn nhé! ✨"
                )


        vehicle_patterns = [
            r"\b(?:xe máy|xe tay ga|xe số|ô tô|oto|car|motorbike|motorcycle)\b",
            r"\b(?:honda|yamaha|suzuki|vespa|vinfast|toyota|kia|mazda|bmw|mercedes)\b",
            r"\b(?:mua xe|bán xe|giá xe|sửa xe|bảo dưỡng xe)\b",
            r"\b(?:bằng lái xe|giấy phép lái xe|bằng b2|bằng a1)\b",
        ]

        for pat in vehicle_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh xe hoặc phụ tùng phương tiện ạ! 🛵\n\n"
                    "Nếu bạn đang tìm outfit đi phượt, đi xe máy hoặc đi du lịch "
                    "thì mình có thể gợi ý trang phục phù hợp nhé!"
                )


        law_patterns = [
            r"\b(?:luật|pháp luật|luat|phap luat|luật sư|luat su|lawyer)\b",
            r"\b(?:hợp đồng|hop dong|tranh chấp|khiếu nại|khởi kiện)\b",
            r"\b(?:công an|tòa án|toa an|vi phạm|phạt tiền|án phạt)\b",
            r"\b(?:ly hôn|ly hon|di chúc|thừa kế|thừa kế tài sản)\b",
            r"\b(?:giấy khai sinh|căn cước|cccd|hộ khẩu|giấy tờ)\b",
        ]

        for pat in law_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist không phải trợ lý pháp lý nên mình không hỗ trợ "
                    "tư vấn luật hay thủ tục pháp lý ạ! ⚖️\n\n"
                    "Mình có thể hỗ trợ bạn về sản phẩm, size, màu sắc, phối đồ "
                    "và chính sách mua hàng của Evern Fashion nhé."
                )


        job_patterns = [
            r"\b(?:tìm việc|tim viec|việc làm|viec lam|job|career|tuyển dụng)\b",
            r"\b(?:cv|resume|xin việc|phỏng vấn xin việc)\b",
            r"\b(?:lương|mức lương|salary|thu nhập|đãi ngộ)\b",
            r"\b(?:part time|full time|freelance|intern|thực tập)\b",
        ]

        for pat in job_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist tập trung vào tư vấn thời trang cho khách hàng "
                    "nên không hỗ trợ tìm việc hay viết CV ạ! 💼\n\n"
                    "Nếu bạn cần chọn outfit đi phỏng vấn hoặc đi làm thì mình có thể "
                    "gợi ý phong cách phù hợp nhé! 👔"
                )


        agriculture_patterns = [
            r"\b(?:trồng cây|cây trồng|nông nghiệp|nuôi trồng)\b",
            r"\b(?:phân bón|thuốc trừ sâu|thuốc sâu|hạt giống)\b",
            r"\b(?:lúa|ngô|rau|cà phê|cây ăn quả)\b",
            r"\b(?:chăn nuôi|nuôi gà|nuôi heo|nuôi bò|nuôi cá)\b",
        ]

        for pat in agriculture_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh sản phẩm nông nghiệp ạ! 🌱\n\n"
                    "Nếu bạn cần tìm trang phục đi dã ngoại, làm vườn hoặc hoạt động ngoài trời "
                    "thì mình có thể tư vấn nhé!"
                )


        construction_patterns = [
            r"\b(?:xi măng|gạch|cát|đá xây dựng|sắt thép)\b",
            r"\b(?:sơn nhà|sơn tường|vữa|bê tông|ống nước)\b",
            r"\b(?:xây nhà|thiết kế nhà|kiến trúc|kiến trúc sư)\b",
            r"\b(?:thợ xây|thợ điện|thợ nước|công trình)\b",
        ]

        for pat in construction_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh vật liệu xây dựng hay dịch vụ xây dựng ạ! 🏗️"
                )


        stationery_patterns = [
            r"\b(?:bút|bút bi|bút chì|bút máy|vở|sổ tay)\b",
            r"\b(?:giấy|giấy in|máy in|mực in|printer)\b",
            r"\b(?:văn phòng phẩm|office supplies|đồ dùng học tập)\b",
            r"\b(?:kẹp giấy|bấm kim|dập ghim|file tài liệu)\b",
        ]

        for pat in stationery_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh văn phòng phẩm hay đồ dùng học tập ạ! ✏️\n\n"
                    "Nếu bạn cần outfit đi học hoặc đi làm văn phòng thì mình có thể tư vấn nha!"
                )


        toy_patterns = [
            r"\b(?:đồ chơi|đồ chơi trẻ em|toy|toys)\b",
            r"\b(?:lego|barbie|gấu bông|búp bê|xe đồ chơi)\b",
            r"\b(?:robot đồ chơi|đồ chơi giáo dục|board game)\b",
        ]

        for pat in toy_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh đồ chơi ạ! 🧸\n\n"
                    "Shop có thể hỗ trợ bạn tìm trang phục thời trang cho trẻ em "
                    "nếu hệ thống đang có sản phẩm phù hợp nhé."
                )


        restaurant_patterns = [
            r"\b(?:nhà hàng|restaurant|quán ăn|quán nhậu)\b",
            r"\b(?:menu|thực đơn|đặt bàn|đặt món)\b",
            r"\b(?:ship đồ ăn|giao đồ ăn|food delivery)\b",
            r"\b(?:grabfood|shopeefood|befood)\b",
        ]

        for pat in restaurant_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không cung cấp dịch vụ nhà hàng hay giao đồ ăn ạ! 🍜\n\n"
                    "Nếu bạn chuẩn bị đi ăn tối, đi cafe hoặc hẹn hò và cần chọn outfit "
                    "thì mình có thể giúp bạn nha! ✨"
                )


        news_patterns = [
            r"\b(?:tin tức|tin mới|tin hôm nay|breaking news)\b",
            r"\b(?:chính trị|chinh tri|politics|bầu cử|bau cu)\b",
            r"\b(?:tổng thống|thủ tướng|quốc hội|chính phủ)\b",
            r"\b(?:chiến tranh|xung đột|quốc tế|thời sự)\b",
        ]

        for pat in news_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist tập trung vào lĩnh vực thời trang nên không cung cấp "
                    "tin tức thời sự hay tư vấn các vấn đề chính trị ạ! 📰\n\n"
                    "Mình có thể giúp bạn tìm outfit theo phong cách, màu sắc, mùa hoặc dịp sử dụng nhé."
                )


        science_patterns = [
            r"\b(?:vật lý|vat ly|physics|hóa học|hoa hoc|chemistry)\b",
            r"\b(?:sinh học|sinh hoc|biology|di truyền học)\b",
            r"\b(?:nguyên tử|phân tử|electron|proton|neutron)\b",
            r"\b(?:phản ứng hóa học|công thức hóa học|phương trình hóa học)\b",
            r"\b(?:dna|rna|tế bào|gen|nhiễm sắc thể)\b",
            r"\b(?:vũ trụ|thiên văn|hành tinh|black hole|lỗ đen)\b",
        ]

        for pat in science_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist chuyên hỗ trợ thời trang nên không phải trợ lý "
                    "chuyên môn về khoa học tự nhiên ạ! 🔬\n\n"
                    "Nếu bạn cần outfit cho phòng thí nghiệm, trường học hoặc sự kiện "
                    "khoa học thì mình vẫn có thể tư vấn trang phục nhé!"
                )


        psychology_patterns = [
            r"\b(?:tâm lý|tam ly|psychology|stress|căng thẳng)\b",
            r"\b(?:buồn|lo lắng|lo âu|anxiety|mất ngủ)\b",
            r"\b(?:tư vấn tâm lý|tâm sự|trầm cảm|depression)\b",
            r"\b(?:mối quan hệ|relationship|chia tay|người yêu)\b",
        ]

        for pat in psychology_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist chủ yếu hỗ trợ thời trang và mua sắm nên không "
                    "thay thế chuyên gia tư vấn tâm lý ạ. 💙\n\n"
                    "Nếu bạn muốn chọn một outfit thoải mái, phù hợp với dịp hoặc phong cách "
                    "của mình thì mình vẫn rất sẵn sàng hỗ trợ nhé!"
                )


        religion_patterns = [
            r"\b(?:tôn giáo|ton giao|religion)\b",
            r"\b(?:phật giáo|phat giao|đạo phật|thiên chúa giáo|công giáo)\b",
            r"\b(?:nhà thờ|chùa|đền|thánh đường)\b",
            r"\b(?:kinh thánh|phật pháp|giáo lý)\b",
        ]

        for pat in religion_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist không phải trợ lý chuyên về tôn giáo hay tín ngưỡng ạ! 🙏\n\n"
                    "Nếu bạn cần trang phục lịch sự để tham dự một buổi lễ hoặc sự kiện "
                    "thì mình có thể tư vấn theo yêu cầu về trang phục nhé."
                )


        camera_patterns = [
            r"\b(?:máy ảnh|camera|dslr|mirrorless)\b",
            r"\b(?:canon|nikon|sony alpha|fujifilm|leica)\b",
            r"\b(?:ống kính|lens|tripod|chân máy ảnh)\b",
            r"\b(?:chụp ảnh|nhiếp ảnh|photography|photoshoot)\b",
        ]

        for pat in camera_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh máy ảnh hay thiết bị nhiếp ảnh ạ! 📷\n\n"
                    "Nếu bạn chuẩn bị chụp ảnh và muốn chọn outfit phù hợp với concept "
                    "thì mình có thể giúp bạn lên đồ nhé! ✨"
                )


        logistics_patterns = [
            r"\b(?:vận chuyển hàng hóa|logistics|cargo|freight)\b",
            r"\b(?:gửi hàng|gửi kiện hàng|chuyển phát)\b",
            r"\b(?:viettel post|vnpost|ghn|ghtk|j&t|jt express)\b",
            r"\b(?:container|kho hàng|xe tải chở hàng)\b",
        ]

        for pat in logistics_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không phải đơn vị logistics độc lập ạ! 📦\n\n"
                    "Nếu bạn đang hỏi về việc giao đơn hàng Evern Fashion thì mình có thể "
                    "hỗ trợ kiểm tra thông tin đơn hàng theo dữ liệu của shop nhé."
                )


        gambling_patterns = [
            r"\b(?:casino|cá cược|ca cuoc|bet|betting)\b",
            r"\b(?:lô đề|lo de|xổ số|xo so|lottery)\b",
            r"\b(?:nhà cái|nha cai|kèo bóng|keo bong)\b",
            r"\b(?:slot|poker|blackjack)\b",
        ]

        for pat in gambling_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không cung cấp dịch vụ liên quan đến cá cược "
                    "hay trò chơi may rủi ạ! 🎲"
                )


        jewelry_patterns = [
            r"\b(?:vàng|vang|gold|bạc|silver|platinum)\b",
            r"\b(?:kim cương|diamond|đá quý|ngọc trai)\b",
            r"\b(?:nhẫn|vòng cổ|dây chuyền|bông tai|hoa tai)\b",
            r"\b(?:trang sức|jewelry|jewellery)\b",
        ]

        for pat in jewelry_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion tập trung vào quần áo và phụ kiện thời trang "
                    "trong danh mục của shop, không kinh doanh vàng bạc hay trang sức cao cấp ạ! 💎\n\n"
                    "Nếu bạn cần phối phụ kiện với outfit thì mình có thể gợi ý "
                    "theo phong cách bạn muốn nhé!"
                )


        appliance_patterns = [
            r"\b(?:tivi|tv|smart tv|tủ lạnh|máy giặt)\b",
            r"\b(?:điều hòa|máy lạnh|quạt điện|quạt hơi nước)\b",
            r"\b(?:lò vi sóng|nồi chiên không dầu|nồi cơm điện)\b",
            r"\b(?:máy hút bụi|robot hút bụi|máy lọc không khí)\b",
        ]

        for pat in appliance_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh thiết bị điện gia dụng ạ! 🏠⚡\n\n"
                    "Shop chuyên về quần áo và phụ kiện thời trang."
                )


        electronics_patterns = [
            r"\b(?:arduino|raspberry pi|esp32|esp8266)\b",
            r"\b(?:mạch điện|linh kiện điện tử|điện trở|tụ điện|transistor)\b",
            r"\b(?:breadboard|relay|module|sensor|cảm biến)\b",
            r"\b(?:hàn mạch|lập trình arduino|robot)\b",
        ]

        for pat in electronics_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không kinh doanh linh kiện điện tử hay thiết bị lập trình "
                    "phần cứng ạ! 🔌"
                )


        business_patterns = [
            r"\b(?:marketing|digital marketing|quảng cáo|facebook ads|google ads)\b",
            r"\b(?:seo|content marketing|branding|brand strategy)\b",
            r"\b(?:kinh doanh|business|startup|khởi nghiệp)\b",
            r"\b(?:doanh thu|lợi nhuận|kế toán|thuế doanh nghiệp)\b",
        ]

        for pat in business_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist tập trung vào tư vấn mua sắm thời trang nên không "
                    "hỗ trợ tư vấn chuyên sâu về marketing hay kinh doanh ạ! 📊\n\n"
                    "Nếu bạn cần thông tin về sản phẩm, phong cách hoặc chính sách mua hàng "
                    "của Evern Fashion thì mình có thể hỗ trợ nhé."
                )


        language_patterns = [
            r"\b(?:dịch sang tiếng anh|dịch tiếng anh|translate english)\b",
            r"\b(?:dịch sang tiếng trung|dịch tiếng trung|translate chinese)\b",
            r"\b(?:dịch tiếng nhật|dịch tiếng hàn|dịch tiếng pháp)\b",
            r"\b(?:ngữ pháp|grammar|từ vựng|vocabulary|phát âm)\b",
        ]

        for pat in language_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist tập trung vào lĩnh vực thời trang nên không phải "
                    "trợ lý dịch thuật chuyên dụng ạ! 🌍\n\n"
                    "Tuy nhiên mình có thể hỗ trợ giải thích tên sản phẩm, phong cách "
                    "hoặc thuật ngữ thời trang bằng tiếng Anh nếu cần nhé."
                )


        fortune_patterns = [
            r"\b(?:bói toán|boi toan|tử vi|tu vi|horoscope)\b",
            r"\b(?:cung hoàng đạo|cung hoang dao|zodiac)\b",
            r"\b(?:tarot|xem tarot|bói bài)\b",
            r"\b(?:phong thủy|phong thuy|feng shui)\b",
        ]

        for pat in fortune_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Stylist không cung cấp dịch vụ bói toán, tử vi hay dự đoán "
                    "tương lai ạ! 🔮\n\n"
                    "Nếu bạn muốn chọn màu sắc hoặc phong cách trang phục theo sở thích "
                    "cá nhân thì mình có thể hỗ trợ nhé."
                )


        currency_patterns = [
            r"\b(?:tỷ giá|ty gia|usd|eur|jpy|cny|krw|gbp)\b",
            r"\b(?:đổi tiền|doi tien|ngoại tệ|ngoai te|exchange rate)\b",
            r"\b(?:giá đô|giá usd|giá euro|giá yên)\b",
        ]

        for pat in currency_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion không cung cấp dịch vụ đổi ngoại tệ hay tư vấn tỷ giá ạ! 💱"
                )


        generic_nonfashion_patterns = [
            r"\b(?:bán cho tôi|mua cho tôi|tìm cho tôi|có bán)\s+"
            r"(?:điện thoại|laptop|tivi|tủ lạnh|xe máy|ô tô|bàn ghế|sách|thuốc)\b",

            r"\b(?:shop có|cửa hàng có|có hàng)\s+"
            r"(?:điện thoại|laptop|xe máy|ô tô|sách|thuốc|đồ ăn|mỹ phẩm)\b",
        ]

        for pat in generic_nonfashion_patterns:
            if re.search(pat, msg_l):
                return True, (
                    "Dạ Evern Fashion hiện chỉ kinh doanh các sản phẩm thời trang "
                    "và phụ kiện liên quan ạ! ✨\n\n"
                    "Mình có thể giúp bạn tìm áo, quần, váy, đầm, áo khoác "
                    "hoặc phụ kiện phù hợp với nhu cầu của bạn nha."
                )

        return False, ""

    def _detect_product_in_text(self, text: str, user_gender: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Nhận diện trực tiếp sản phẩm thực tế từ CSDL SQLite nếu người dùng nhắc đến
        tên sản phẩm, mã sản phẩm hoặc một phần tiêu đề đặc trưng trong câu chat.
        Có kiểm tra xung đột giới tính (nam/nữ), xung đột danh mục và bỏ qua khi hỏi tìm kiếm/gợi ý.
        """
        if not text or len(text.strip()) < 3:
            return None
        text_lower = text.lower().strip()

        # Nếu câu hỏi là hỏi tìm kiếm, gợi ý chung chung về outfit hoặc hỏi xem shop có mẫu nào hay không
        # KHÔNG tự ý gán vào 1 sản phẩm đơn lẻ bằng heuristic từ khóa rời rạc
        is_search_or_recommendation_query = bool(re.search(
            r"\b(?:1\s*(?:chiếc|cái)?\s*(?:quần|áo)\s*(?:và|với|cùng)\s*1\s*(?:chiếc|cái)?\s*(?:áo|quần)|"
            r"quần và áo|áo và quần|combo|phối đồ|mix đồ|set đồ|outfit|lên đồ|không biết phối|"
            r"gợi ý cho tôi|gợi ý outfit|gợi ý|tư vấn cho tôi|tư vấn outfit|tư vấn set|tư vấn đồ|"
            r"1 số quần áo|một số quần áo|quần áo|trang phục|đồ nam|thời trang nam|mặc gì|mặc đồ gì|"
            r"shop có|bên shop có|cửa hàng có|có\s*(?:chiếc|cái|mẫu|sản phẩm|loại|bộ)?\s*(?:áo|quần|váy|đầm|khoác|len|đồ)|"
            r"chiếc\s*áo\s*nào|mẫu\s*áo\s*nào|áo\s*nào|quần\s*nào|mẫu\s*nào|sản phẩm nào|loại nào|"
            r"tìm\s*(?:áo|quần|váy|đầm|khoác|len|đồ)|mua\s*(?:áo|quần|váy|đầm|khoác|len|đồ))\b",
            text_lower
        ))

        # Tự động nhận diện giới tính nếu chưa có
        if not user_gender:
            if re.search(r"\b(?:tôi là nam|mình là nam|cho nam|đồ nam|thời trang nam|bạn trai|con trai|quý ông)\b", text_lower):
                user_gender = "nam"
            elif re.search(r"\b(?:tôi là nữ|mình là nữ|cho nữ|đồ nữ|thời trang nữ|bạn gái|con gái)\b", text_lower):
                user_gender = "nữ"

        conn = self.db_service._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        conn.close()

        def is_gender_mismatch(p_obj: Dict[str, Any]) -> bool:
            p_n = (p_obj.get("name") or "").lower()
            p_cat = (p_obj.get("category") or "").lower()
            raw_tags = p_obj.get("tags") or ""
            p_tags = " ".join(raw_tags).lower() if isinstance(raw_tags, list) else str(raw_tags).lower()
            is_unisex = "nam nữ" in p_n or "unisex" in p_n or "unisex" in p_tags
            if is_unisex:
                return False
            if user_gender == "nam":
                if any(w in p_n for w in [" nữ", "nữ ", "(nữ)", "tiểu thư", "nữ tính", "croptop", "hai dây", "váy", "đầm", "chân váy", "quần tất", "legging", "kẹp tóc", "chun buộc tóc"]):
                    return True
                if p_cat in ["váy & đầm", "đầm", "chân váy"]:
                    return True
                if "thời trang nữ" in p_tags or "dành cho nữ" in p_tags:
                    return True
            elif user_gender == "nữ":
                if any(w in p_n for w in [" nam", "nam ", "(nam)", "quý ông", "cà vạt", "ví da nam"]):
                    return True
                if "thời trang nam" in p_tags or "dành cho nam" in p_tags:
                    return True
            return False

        def is_category_mismatch(p_obj: Dict[str, Any]) -> bool:
            p_cat = (p_obj.get("category") or "").lower()
            p_subcat = (p_obj.get("sub_category") or "").lower()
            p_name = (p_obj.get("name") or "").lower()
            
            # Nếu người dùng chỉ hỏi về ÁO (không nhắc quần, tất, chân váy...)
            if re.search(r"\b(?:áo|chiếc áo|áo nào)\b", text_lower) and not re.search(r"\b(?:quần|tất|váy|đầm)\b", text_lower):
                if p_cat in ["phụ kiện", "quần tây", "quần jean"] or any(w in p_subcat or w in p_name for w in ["quần", "tất", "legging", "chân váy"]):
                    return True
            # Nếu người dùng chỉ hỏi về QUẦN
            if re.search(r"\b(?:quần|chiếc quần|quần nào)\b", text_lower) and not re.search(r"\b(?:áo|váy|đầm)\b", text_lower):
                if p_cat in ["áo sơ mi", "áo polo", "áo thun phông", "áo khoác"] or any(w in p_subcat or w in p_name for w in ["áo ", "sơ mi", "polo"]):
                    return True
            # Nếu người dùng chỉ hỏi về VÁY / ĐẦM
            if re.search(r"\b(?:váy|đầm)\b", text_lower) and not re.search(r"\b(?:quần|áo)\b", text_lower):
                if p_cat in ["áo sơ mi", "áo polo", "áo thun phông", "quần tây", "quần jean"]:
                    return True
            return False

        # 1. Tìm theo mã sản phẩm (EVN-dy1, HM589011, AR258043...)
        for r in rows:
            p = self.db_service._format_product(r)
            code = (p.get("code") or "").lower()
            if code and len(code) >= 4 and code in text_lower:
                if not is_gender_mismatch(p) and not is_category_mismatch(p):
                    return p

        # 2. Tìm theo tên sản phẩm chính xác 100% trong câu
        for r in rows:
            p = self.db_service._format_product(r)
            name = (p.get("name") or "").lower()
            if name and name in text_lower:
                if not is_gender_mismatch(p) and not is_category_mismatch(p):
                    return p

        # 3. Tìm theo tên sản phẩm đã bỏ phần trong ngoặc đơn (VD: 'Set 2 Kẹp Tóc Kim Loại Sang Chảnh')
        for r in rows:
            p = self.db_service._format_product(r)
            name = (p.get("name") or "").lower()
            clean_name = re.sub(r"\(.*?\)", "", name).strip()
            if len(clean_name) >= 10 and clean_name in text_lower:
                if not is_gender_mismatch(p) and not is_category_mismatch(p):
                    return p

        # 4. Tìm theo cụm từ đặc trưng tối thiểu 2 từ liền kề (CHỈ áp dụng khi KHÔNG phải hỏi tìm kiếm/gợi ý)
        if not is_search_or_recommendation_query:
            best_match = None
            best_score = 0
            generic_words = {
                "đen", "trắng", "nam", "nữ", "set", "hàng", "cao", "cấp", "quần", "áo", 
                "phong", "cách", "dáng", "thời", "trang", "trẻ", "trung", "hiện", "đại", 
                "phù", "hợp", "giới", "cho", "mẫu", "kiểu", "loại", "đẹp", "mới", "cá", 
                "tính", "năng", "động", "basic", "form", "rộng", "ôm", "ngắn", "dài", 
                "tay", "cổ", "màu", "vải", "chất", "siêu", "nhẹ", "mát",
                # Mùa, thời tiết, nhiệt độ
                "mùa", "đông", "hè", "thu", "xuân", "nắng", "mưa", "lạnh", "nóng", "ấm",
                "rét", "nồm", "ẩm", "gió", "nhiệt", "giữ", "chống", "bão", "thời", "tiết", "trời",
                # Từ hỏi, trợ từ, đại từ, hành động
                "nào", "gì", "sao", "thế", "chiếc", "cái", "con", "bộ", "người", "shop", "cửa",
                "hàng", "có", "không", "hay", "cực", "kỳ", "rất", "quá", "đậm", "hại", "năm",
                "nay", "hôm", "ngày", "tuần", "tháng", "xem", "mua", "tìm", "kiếm", "cần",
                "muốn", "bán", "tư", "vấn", "gợi", "ý", "chọn", "hỏi", "giới", "thiệu",
                "với", "cho", "em", "anh", "chị", "mình", "bạn", "của", "và", "là", "ở", "trong",
                "váy", "đầm", "đồ", "phục"
            }
            for r in rows:
                p = self.db_service._format_product(r)
                if is_gender_mismatch(p) or is_category_mismatch(p):
                    continue
                name = (p.get("name") or "").lower()
                clean_n = re.sub(r"[(),/_-]+", " ", name)
                words = [w for w in clean_n.split() if len(w) >= 2 and w not in generic_words]
                
                # Kiểm tra xem có cụm 2 từ liền kề có nghĩa xuất hiện trong text_lower hay không
                n_tokens = clean_n.split()
                has_bigram = False
                for i in range(len(n_tokens) - 1):
                    bi = f"{n_tokens[i]} {n_tokens[i+1]}"
                    if len(bi) >= 6 and n_tokens[i] not in generic_words and n_tokens[i+1] not in generic_words and bi in text_lower:
                        has_bigram = True
                        break
                if has_bigram and len(words) >= 2:
                    matched_words = [w for w in words if w in text_lower]
                    if len(matched_words) >= 2 and len(matched_words) > best_score:
                        best_score = len(matched_words)
                        best_match = p

            if best_match and best_score >= 2:
                return best_match

        return None

    def _resolve_anaphora(
        self,
        user_message: str,
        entities: Dict[str, Any],
        context: Dict[str, Any],
        current_product: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Giải quyết đại từ chỉ định ('mẫu này', 'áo này', 'quần này', 'nó', 'cái vừa rồi'...)
        hoặc số thứ tự ('mẫu 1', 'mẫu 2', 'mẫu đầu', 'mẫu thứ nhất', 'sp 1', 'cái 1'...)
        để liên kết chuẩn xác với sản phẩm ở các lượt chat trước.
        TUYỆT ĐỐI KHÔNG ép buộc lưu sản phẩm cũ khi người dùng đã chuyển sang câu hỏi khác!
        """
        msg_lower = user_message.lower().strip()

        # -1. Ưu tiên cao nhất: Kiểm tra xem người dùng có nhắc trực tiếp mã sản phẩm hoặc tên sản phẩm cụ thể trong câu hỏi hay không
        explicit_product = self._detect_product_in_text(user_message, user_gender=entities.get("gender"))
        if explicit_product:
            # Kiểm tra xung đột danh mục giữa thực thể người dùng hỏi và explicit_product
            user_cat = (entities.get("category") or "").lower()
            prod_cat = (explicit_product.get("category") or "").lower()
            prod_subcat = (explicit_product.get("sub_category") or "").lower()
            prod_name = (explicit_product.get("name") or "").lower()
            
            conflict = False
            if user_cat == "áo" and (prod_cat in ["phụ kiện", "quần tây", "quần jean"] or any(w in prod_subcat or w in prod_name for w in ["quần", "tất", "chân váy"])):
                conflict = True
            elif user_cat in ["quần", "quần tây", "quần jean"] and (prod_cat.startswith("áo") or "áo" in prod_subcat):
                conflict = True

            if not conflict:
                if not entities.get("product_code"):
                    entities["product_code"] = explicit_product.get("code")
                if not entities.get("category"):
                    entities["category"] = explicit_product.get("category")
                if not entities.get("sub_category"):
                    entities["sub_category"] = explicit_product.get("sub_category")
                context["active_product"] = explicit_product
                return entities, explicit_product

        last_prods = context.get("last_products", [])
        active_prod = context.get("active_product")
        resolved_product = None

        # Kiểm tra sự xuất hiện của các đại từ chỉ định rõ ràng
        pronoun_patterns = [
            r"\b(?:mẫu này|mau nay|áo này|ao nay|quần này|quan nay|váy này|đầm này|cái này|cai nay)\b",
            r"\b(?:nó|no|em này|bộ này|set này|chiếc này)\b",
            r"\b(?:mẫu đó|mẫu đấy|cái đó|cái đấy|sp này|sp đó|sản phẩm này)\b",
            r"\b(?:mẫu vừa rồi|mẫu trên|mẫu trước|cái vừa rồi|áo vừa rồi|mẫu vừa xem)\b"
        ]
        has_pronoun = any(re.search(pat, msg_lower) for pat in pronoun_patterns)

        # -0. Nếu người dùng đang mở trang chi tiết sản phẩm trên website và dùng đại từ ('mẫu này', 'sản phẩm này'...)
        if current_product:
            c_code = current_product.get("code") or current_product.get("id")
            if c_code:
                page_prod, _ = self.db_service.get_product(str(c_code))
                if page_prod:
                    if has_pronoun or any(w in msg_lower for w in ["tư vấn", "chi tiết", "giá", "size", "chất liệu", "mặc với", "phối"]):
                        if not entities.get("product_code"):
                            entities["product_code"] = page_prod.get("code")
                        if not entities.get("category"):
                            entities["category"] = page_prod.get("category")
                        context["active_product"] = page_prod
                        return entities, page_prod

        # 0. Nếu người dùng yêu cầu tìm mẫu khác / đổi mẫu / xem thêm mẫu
        wants_different = any(kw in msg_lower for kw in [
            "tìm mẫu khác", "mẫu khác", "đổi mẫu", "xem mẫu khác", "có mẫu nào khác", "xem thêm mẫu", "mẫu mới", "thay đổi"
        ])
        if wants_different and not has_pronoun:
            return entities, None

        # 1. Nếu người dùng chuyển sang một danh mục thời trang mới rõ rệt (VD: hỏi sang áo sơ mi, áo polo, quần jeans, áo khoác...)
        has_new_category = bool(entities.get("category") or entities.get("sub_category"))
        if has_new_category and not has_pronoun:
            return entities, None

        # 2. Nếu câu hỏi là tìm kiếm mới hoàn toàn hoặc gợi ý outfit chung chung mà không dùng đại từ
        is_general_query = any(kw in msg_lower for kw in [
            "1 số đồ", "gợi ý đồ", "set đồ", "outfit", "mặc gì", "phối đồ", "mix đồ",
            "tìm đồ", "chọn đồ", "đồ phù hợp", "đi chơi", "đi làm", "đi tiệc",
            "hôm nay mặc gì", "ngày mai", "chủ nhật", "thứ hai", "thứ 2", "cuối tuần", "mát mẻ"
        ])
        if is_general_query and not has_pronoun:
            return entities, None

        # 3. Kiểm tra tham chiếu số thứ tự rõ ràng (Mẫu 1, Mẫu 2, Mẫu 3, Cái 1, Sp 1, Mẫu đầu tiên...)
        resolved_idx = None
        if re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:số\s*)?1\b", msg_lower) or \
           re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:thứ\s*)?(?:nhất|đầu|đầu tiên)\b", msg_lower) or \
           re.search(r"\b(?:số\s*1|thứ\s*nhất|đầu tiên)\b", msg_lower):
            resolved_idx = 0
        elif re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:số\s*)?2\b", msg_lower) or \
             re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:thứ\s*)?(?:2|hai)\b", msg_lower) or \
             re.search(r"\b(?:số\s*2|thứ\s*hai)\b", msg_lower):
            resolved_idx = 1
        elif re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:số\s*)?3\b", msg_lower) or \
             re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:thứ\s*)?(?:3|ba)\b", msg_lower) or \
             re.search(r"\b(?:số\s*3|thứ\s*ba)\b", msg_lower):
            resolved_idx = 2
        elif re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:số\s*)?4\b", msg_lower) or \
             re.search(r"\b(?:mẫu|cái|sp|sản phẩm)\s*(?:thứ\s*)?(?:4|tư|bốn)\b", msg_lower) or \
             re.search(r"\b(?:số\s*4|thứ\s*tư)\b", msg_lower):
            resolved_idx = 3

        if resolved_idx is not None and (last_prods or active_prod):
            if last_prods and resolved_idx < len(last_prods):
                resolved_product = last_prods[resolved_idx]
            elif active_prod and resolved_idx == 0:
                resolved_product = active_prod
            elif last_prods:
                resolved_product = last_prods[0]

        # 3.5. Kiểm tra người dùng tham chiếu đến CẢ SET hoặc NHIỀU MÓN ĐỒ trong set từ lượt trước
        # (VD: "mẫu áo và quần trong set này", "cả set này", "set này", "cả áo và quần", "cả 2 mẫu"...)
        is_multi_item_ref = bool(re.search(
            r"\b(?:áo và quần|quần và áo|cả áo và quần|cả áo lẫn quần|mẫu áo và quần|mẫu quần và áo|"
            r"cả hai món|cả 2 món|cả hai mẫu|cả 2 mẫu|cả hai|cả 2|các mẫu này|những mẫu này|"
            r"cả set|cả bộ|set này|bộ này|outfit này|trong set này|trong set|trong bộ)\b",
            msg_lower
        )) or (("áo" in msg_lower and "quần" in msg_lower) and any(w in msg_lower for w in ["set", "bộ", "cả", "trong"]))

        # Trường hợp người dùng chỉ hỏi size chung chung sau khi bot vừa gợi ý set đồ gồm nhiều món
        has_measurement = bool(entities.get("height") or entities.get("weight"))
        is_size_query = any(w in msg_lower for w in ["size gì", "mặc size", "cỡ nào", "vừa không", "mặc vừa", "chọn size", "mặc số mấy", "bảng size", "bao nhiêu kg", "tư vấn size"])
        is_asking_size_for_recent_set = (has_measurement or is_size_query) and last_prods and len(last_prods) >= 2 and not any(w in msg_lower for w in ["mẫu khác", "đổi mẫu", "tìm đồ"])

        if (is_multi_item_ref or is_asking_size_for_recent_set) and last_prods:
            user_only_wants_shirt = ("áo" in msg_lower and not any(w in msg_lower for w in ["quần", "cả", "và", "với", "set", "bộ"]))
            user_only_wants_pants = ("quần" in msg_lower and not any(w in msg_lower for w in ["áo", "cả", "và", "với", "set", "bộ"]))

            if user_only_wants_shirt:
                for lp in last_prods:
                    cat = ((lp.get("category") or "") + " " + (lp.get("sub_category") or "") + " " + lp.get("name", "")).lower()
                    if "áo" in cat or any(w in cat for w in ["sơ mi", "polo", "thun", "khoác", "len"]):
                        resolved_product = lp
                        break
            elif user_only_wants_pants:
                for lp in last_prods:
                    cat = ((lp.get("category") or "") + " " + (lp.get("sub_category") or "") + " " + lp.get("name", "")).lower()
                    if "quần" in cat or any(w in cat for w in ["jean", "âu", "tây", "kaki", "short", "loe"]):
                        resolved_product = lp
                        break
            else:
                # Người dùng hỏi về CẢ SET (Cả áo và quần, hoặc cả set vừa gợi ý)
                entities["is_set_reference"] = True
                entities["is_outfit_query"] = True
                entities["category"] = "Set Outfit (Áo & Quần)"
                context["active_product"] = None
                return entities, None

        # 4. Kiểm tra đại từ chỉ định ('mẫu này', 'áo này', 'em này', 'cái đó'...)
        if resolved_product is None and has_pronoun and (last_prods or active_prod):
            if active_prod:
                resolved_product = active_prod
            elif last_prods:
                resolved_product = last_prods[0]

        # 5. Nếu người dùng THỰC SỰ cung cấp số đo chiều cao / cân nặng hoặc hỏi size và đang có sản phẩm trong ngữ cảnh
        if resolved_product is None and (active_prod or last_prods):
            has_measurement = bool(entities.get("height") or entities.get("weight"))
            is_size_query = any(w in msg_lower for w in ["size gì", "mặc size", "cỡ nào", "vừa không", "mặc vừa", "chọn size", "mặc số mấy", "bảng size", "bao nhiêu kg"])
            
            # CHỈ liên kết với sản phẩm trước KHI người dùng THỰC SỰ cung cấp số đo hoặc hỏi size
            # TUYỆT ĐỐI KHÔNG dùng bot_asked_size độc lập để ép sản phẩm cũ khi người dùng hỏi việc khác!
            if (has_measurement or is_size_query) and not has_new_category:
                resolved_product = active_prod or last_prods[0]

        if resolved_product:
            if not entities.get("product_code"):
                entities["product_code"] = resolved_product.get("code")
            if not entities.get("category"):
                entities["category"] = resolved_product.get("category") or resolved_product.get("sub_category")
            if not entities.get("sub_category") and resolved_product.get("sub_category"):
                entities["sub_category"] = resolved_product.get("sub_category")

        return entities, resolved_product

    def _is_product_query(self, user_message: str, intent: str, entities: Dict[str, Any]) -> bool:
        """Xác định người dùng đang hỏi tìm sản phẩm, xem mẫu, hỏi giá, hỏi size hay cần tư vấn trang phục."""
        if intent == "out_of_scope" or intent == "complaint":
            return False

        if intent == "weather":
            has_fashion = bool(entities.get("category") or entities.get("sub_category") or entities.get("is_outfit_query") or any(w in user_message.lower() for w in ["áo", "quần", "váy", "đầm", "khoác", "len", "mặc", "đồ", "outfit", "set"]))
            if not has_fashion and not entities.get("product_code"):
                return False

        non_product_intents = ["greeting", "goodbye", "shipping_return", "store_location", "payment_method", "care_instruction", "thank_you", "complaint", "discount"]
        if intent in non_product_intents and not entities.get("product_code"):
            return False

        product_intents = [
            "search_product", "search_by_price", "search_by_category",
            "product_price", "product_stock", "recommendation",
            "style_young", "style_office", "style_mature", "men_fashion", "order", "color",
            "product_detail", "size_guide", "gift"
        ]
        if intent in product_intents:
            return True

        if (
            entities.get("category")
            or entities.get("product_code")
            or entities.get("color")
            or entities.get("max_price")
            or entities.get("min_price")
            or entities.get("height")
            or entities.get("weight")
        ):
            return True

        msg_lower = user_message.lower()
        # Chỉ nhận là product query khi có từ khóa thời trang hoặc hành động mua sắm thời trang cụ thể
        fashion_product_keywords = [
            "áo", "quần", "váy", "đầm", "set đồ", "outfit", "chân váy", "blazer", "sơ mi", "polo", "thun",
            "khoác", "jeans", "jean", "kaki", "tây", "âu", "baggy", "loe", "suông", "pijama",
            "thắt lưng", "ví da", "giày", "cà vạt", "kính mát", "phụ kiện", "bộ đồ", "đồ"
        ]
        has_fashion_kw = any(kw in msg_lower for kw in fashion_product_keywords)
        action_keywords = ["mua đồ", "giá bao nhiêu", "giá nhiêu", "bao nhiêu tiền", "còn hàng", "phối đồ", "mặc đi", "tư vấn mẫu", "cho tôi xem mẫu", "tìm đồ", "đi date", "date", "tết", "du xuân", "gợi ý"]

        return has_fashion_kw or any(kw in msg_lower for kw in action_keywords)

    def _fetch_products_from_db(
        self,
        user_message: str,
        entities: Dict[str, Any],
        resolved_product: Optional[Dict[str, Any]] = None,
        intent: str = ""
    ) -> List[Dict[str, Any]]:
        """Truy vấn trực tiếp CSDL SQLite để lấy sản phẩm thực tế phù hợp nhất."""
        # 0. Nếu đã xác định được sản phẩm từ ngữ cảnh hội thoại trước
        if resolved_product and not any(kw in user_message.lower() for kw in ["tìm mẫu khác", "mẫu khác", "đổi mẫu", "xem mẫu khác"]):
            return [resolved_product]

        # 0.1 Nếu câu hỏi nhắc đến tên hoặc mã sản phẩm cụ thể trong CSDL
        detected_p = self._detect_product_in_text(user_message, user_gender=entities.get("gender"))
        if detected_p:
            return [detected_p]

        # 1. Nếu có mã sản phẩm cụ thể (VD: AR258043DR26, ST260155...)
        if entities.get("product_code"):
            p, _ = self.db_service.get_product(entities["product_code"])
            if p:
                return [p]

        category = entities.get("category") or ""
        msg_l = user_message.lower()

        # 2. Nếu người dùng yêu cầu tư vấn phối đồ / gợi ý outfit trọn bộ
        # LƯU Ý: Nếu người dùng đã nêu rõ danh mục đơn lẻ (như chỉ hỏi ÁO hoặc chỉ hỏi QUẦN),
        # thì đây là tìm kiếm sản phẩm theo danh mục/style chứ KHÔNG phải yêu cầu sinh cả set outfit hỗn hợp!
        has_both_pieces = ("áo" in msg_l and "quần" in msg_l) or len(entities.get("categories", [])) >= 2 or entities.get("is_outfit_query")
        user_wants_single_piece = (
            bool(category)
            and not has_both_pieces
            and not any(w in msg_l for w in ["set đồ", "outfit", "bộ đồ", "lên đồ", "phối đồ", "mix đồ", "mặc với gì", "trang phục", "quần áo", "gợi ý"])
        )

        is_outfit_req = (
            intent in ["recommendation", "style_young", "style_office", "style_mature", "men_fashion", "gift"]
            or entities.get("is_outfit_query")
            or entities.get("occasion")
            or any(kw in msg_l for kw in [
                "đi chơi", "dạo phố", "cafe", "hẹn hò", "phối đồ", "mix đồ",
                "set đồ", "outfit", "mặc gì", "chủ nhật", "cuối tuần", "1 số đồ",
                "gợi ý đồ", "đồ phù hợp", "hôm nay mặc gì", "mát mẻ", "thời tiết",
                "đi date", "date", "tết", "quần áo tết", "đồ tết", "du xuân", "gặp crush"
            ])
        )

        is_general_outfit = (
            entities.get("is_outfit_query")
            or bool(entities.get("occasion"))
            or any(kw in msg_l for kw in [
                "quần áo", "trang phục", "lên đồ", "phối đồ", "set đồ", "outfit",
                "mặc gì", "đồ phù hợp", "gợi ý đồ", "bữa tiệc", "sinh nhật",
                "đi date", "date", "tết", "quần áo tết", "đồ tết", "du xuân", "bộ đồ"
            ])
        )

        if is_outfit_req and not user_wants_single_piece and (is_general_outfit or not category or not entities.get("sub_category")):
            outfit = self.recommender.recommend_outfit(user_message=user_message, entities=entities, limit=4)
            if outfit:
                return outfit

        sub_category = entities.get("sub_category") or ""
        # Ánh xạ từ khóa tiếng Việt cụ thể sang sub_category chuẩn
        subcat_patterns = [
            (r"\b(?:áo khoác jeans|ao khoac jeans|áo khoác jean|ao khoac jean|khoác jeans|khoác jean|denim jacket)\b", "áo khoác jeans"),
            (r"\b(?:áo khoác da|ao khoac da|khoác da|biker jacket|da biker)\b", "áo khoác da"),
            (r"\b(?:áo khoác hoodie|ao khoac hoodie|hoodie|áo hoodie)\b", "áo khoác hoodie"),
            (r"\b(?:áo khoác gió|ao khoac gio|áo gió|windbreaker)\b", "áo khoác gió"),
            (r"\b(?:áo khoác bomber|ao khoac bomber|áo bomber|bomber)\b", "áo khoác bomber"),
            (r"\b(?:áo khoác cardigan|cardigan|áo khoác len)\b", "áo len"),
            (r"\b(?:áo măng tô|ao mang to|măng tô|trench coat)\b", "áo măng tô"),
            (r"\b(?:quần loe|quan loe|ống loe|ong loe|quần ống loe|quan ong loe|flared|flare)\b", "quần loe"),
            (r"\b(?:quần ống rộng|quan ong rong|ống rộng|ong rong|wide leg)\b", "quần ống rộng"),
            (r"\b(?:quần ống suông|quan ong suong|ống suông|ong suong)\b", "quần ống suông"),
            (r"\b(?:quần baggy|quan baggy|baggy)\b", "quần baggy"),
            (r"\b(?:quần âu|quan au|quần tây|quan tay|quần tây âu)\b", "quần âu"),
            (r"\b(?:quần short|quan short|quần đùi|quần soóc)\b", "quần short"),
            (r"\b(?:quần kaki|quần khaki|quan kaki|quan khaki)\b", "quần khaki"),
            (r"\b(?:quần jean|quần jeans|quần bò|quan jean|quan bo)\b", "quần jeans"),
            (r"\b(?:áo sơ mi|ao so mi|sơ mi|so mi)\b", "áo sơ mi"),
            (r"\b(?:áo polo|ao polo|polo)\b", "áo polo"),
            (r"\b(?:áo thun|ao thun|áo phông|ao phong|t-shirt)\b", "áo thun"),
            (r"\b(?:blazer|áo blazer)\b", "blazer"),
            (r"\b(?:áo khoác|ao khoac)\b", "áo khoác"),
            (r"\b(?:áo len|ao len)\b", "áo len"),
            (r"\b(?:chân váy|chan vay)\b", "chân váy"),
            (r"\b(?:đầm dạ hội|đầm tiệc|váy tiệc|đầm cưới|đầm đám cưới|váy đám cưới|đầm sang trọng|váy đi tiệc|đầm đi tiệc)\b", "đầm dạ hội / đầm tiệc cưới"),
            (r"\b(?:váy ngủ|vay ngu|đồ ngủ|do ngu|pijama|pyjama|đồ mặc nhà|do mac nha)\b", "váy ngủ / đồ mặc nhà"),
            (r"\b(?:giày|sneaker|giày thể thao)\b", "giày"),
            (r"\b(?:thắt lưng|that lung|dây lưng)\b", "thắt lưng"),
            (r"\b(?:ví da|vi da|ví cầm tay)\b", "ví da"),
            (r"\b(?:cà vạt|ca vat|caravat)\b", "cà vạt"),
            (r"\b(?:kính mát|kinh mat|kính râm)\b", "kính mát"),
            (r"\b(?:kẹp tóc|kep toc|càng cua|cột tóc|buộc tóc|chun buộc tóc)\b", "kẹp tóc"),
            (r"\b(?:quần tất|quan tat|tất chân|tất da chân)\b", "quần tất"),
            (r"\b(?:dù|ô cầm tay|dù che mưa)\b", "dù")
        ]
        for pat, sc in subcat_patterns:
            if re.search(pat, msg_l):
                sub_category = sc
                break

        # Nhận diện người dùng chỉ hỏi về áo hoặc chỉ hỏi về quần
        user_asks_shirt_only = (
            re.search(r"\b(?:áo|ao)\b", msg_l)
            and not re.search(r"\b(?:quần|quan)\b", msg_l)
            and not re.search(r"\b(?:tất|tat|legging)\b", msg_l)
        )
        user_asks_pants_only = (
            re.search(r"\b(?:quần|quan)\b", msg_l)
            and not re.search(r"\b(?:áo|ao)\b", msg_l)
        )

        season_val = entities.get("season") or ""
        is_four_seasons_query = (
            season_val == "bốn mùa"
            or any(w in msg_l for w in ["4 mùa", "4 mua", "bốn mùa", "bon mua", "quanh năm"])
            or (
                any(w in msg_l for w in ["xuân", "xuan"])
                and any(w in msg_l for w in ["hè", "he", "hạ"])
                and any(w in msg_l for w in ["thu", "autumn"])
                and any(w in msg_l for w in ["đông", "dong", "winter"])
            )
        )
        is_summer_query = season_val == "mùa hè" or any(w in msg_l for w in ["mùa hè", "mua he", "mùa hạ", "mua ha", "ngày hè", "ngay he", "hè", "nóng", "oi bức", "nắng nóng"])
        is_winter_query = season_val == "mùa đông" or any(w in msg_l for w in ["mùa đông", "mua dong", "ngày đông", "tiết đông", "đông", "giữ ấm", "giữ nhiệt", "rét", "lạnh", "rét đậm", "rét hại", "chống rét"])
        is_fall_query = season_val == "mùa thu" or any(w in msg_l for w in ["mùa thu", "mua thu", "ngày thu", "trời thu", "tiết thu", "thu", "se lạnh", "mát mẻ", "mát"])
        is_spring_query = season_val == "mùa xuân" or any(w in msg_l for w in ["mùa xuân", "mua xuan", "ngày xuân", "tiết xuân", "xuân", "du xuân", "chúc tết", "năm mới"])

        # 0. Xử lý truy xuất 4 sản phẩm đại diện cho cả 4 mùa (Xuân - Hè - Thu - Đông)
        if is_four_seasons_query:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            season_showcase = []
            
            # 1. Mùa Xuân: Sơ mi cổ tàu đũi linen / Sơ mi lụa tơ tằm / Đầm ren pastel
            cursor.execute("""
                SELECT * FROM products 
                WHERE (name LIKE '%Cổ Tàu%' OR name LIKE '%Sơ Mi Lụa%' OR name LIKE '%Đầm Xoè%')
                  AND name NOT LIKE '%quần%' AND name NOT LIKE '%tất%'
                ORDER BY RANDOM() LIMIT 1
            """)
            r_xuan = cursor.fetchone()
            if r_xuan:
                season_showcase.append(self.db_service._format_product(r_xuan))
                
            # 2. Mùa Hè: Áo thun cotton oversize / Áo polo Nano / Quần short khaki mùa hè
            cursor.execute("""
                SELECT * FROM products 
                WHERE (name LIKE '%Cotton Oversize%' OR name LIKE '%Polo Nano%' OR name LIKE '%Cuba%' OR name LIKE '%Short Khaki Mùa Hè%')
                ORDER BY RANDOM() LIMIT 1
            """)
            r_he = cursor.fetchone()
            if r_he:
                season_showcase.append(self.db_service._format_product(r_he))
                
            # 3. Mùa Thu: Áo cardigan len mỏng trắng kem / Áo khoác gió trượt nước / Quần khaki chino
            cursor.execute("""
                SELECT * FROM products 
                WHERE (name LIKE '%Cardigan Len Mỏng%' OR name LIKE '%Gió Chống Nước%' OR name LIKE '%Khaki Chino%')
                ORDER BY RANDOM() LIMIT 1
            """)
            r_thu = cursor.fetchone()
            if r_thu:
                season_showcase.append(self.db_service._format_product(r_thu))
                
            # 4. Mùa Đông: Áo len mỏng cổ lọ AL250918 / Áo khoác jeans đen chỉ nổi / Áo măng tô / Áo chần bông
            cursor.execute("""
                SELECT * FROM products 
                WHERE (name LIKE '%Len Mỏng Cổ Lọ%' OR name LIKE '%Măng Tô%' OR name LIKE '%Chần Bông%' OR name LIKE '%Khoác Jeans%')
                ORDER BY RANDOM() LIMIT 1
            """)
            r_dong = cursor.fetchone()
            if r_dong:
                season_showcase.append(self.db_service._format_product(r_dong))
                
            conn.close()
            if len(season_showcase) >= 3:
                return season_showcase

        # Nhận diện ngữ cảnh đám cưới / tiệc cưới sang trọng
        is_wedding_query = any(w in msg_l for w in ["đám cưới", "tiệc cưới", "dự cưới", "khách sạn 5 sao", "5 sao", "cô dâu"])
        is_sleepwear_query = any(w in msg_l for w in ["váy ngủ", "vay ngu", "đồ ngủ", "do ngu", "pijama", "pyjama", "mặc nhà"])

        if is_winter_query and user_asks_shirt_only and category in ["áo", ""] and not sub_category:
            category = "Áo khoác"
            sub_category = "áo khoác"

        if is_wedding_query:
            sub_category = "đầm dạ hội / đầm tiệc cưới"
            category = "Váy & Đầm"
        elif is_sleepwear_query:
            sub_category = "váy ngủ / đồ mặc nhà"
            category = "Váy & Đầm"

        # Nếu sub_category xác định rõ danh mục cha
        if sub_category in ["quần âu", "quần short", "quần khaki"]:
            category = "Quần tây"
        elif sub_category in ["quần jeans", "quần bò"]:
            category = "Quần jean"
        elif sub_category in ["quần loe", "quần ống rộng", "quần ống suông", "quần baggy"]:
            category = ""
        elif sub_category in ["áo sơ mi"]:
            category = "Áo sơ mi"
        elif sub_category in ["áo polo"]:
            category = "Áo polo"
        elif sub_category in ["áo thun"]:
            category = "Áo thun phông"
        elif sub_category in ["blazer", "áo khoác", "áo len", "áo khoác jeans", "áo khoác da", "áo khoác hoodie", "áo khoác gió", "áo khoác bomber", "áo măng tô"]:
            category = "Áo khoác"
        elif sub_category in ["chân váy", "đầm dạ hội", "đầm dạ hội / đầm tiệc cưới", "váy ngủ / đồ mặc nhà"]:
            category = "Váy & Đầm"
        elif sub_category in ["giày", "thắt lưng", "ví da", "cà vạt", "kính mát", "kẹp tóc", "quần tất", "dù"]:
            category = "Phụ kiện"

        color = entities.get("color") or ""
        size = entities.get("size") or ""
        min_p = entities.get("min_price") or 0
        max_p = entities.get("max_price") or 0
        gender = entities.get("gender") or ""

        material = entities.get("material") or ""
        clean_kw = ""
        if material:
            clean_kw = material
        elif entities.get("keywords"):
            stop_kw = {"tư", "vấn", "gợi", "ý", "mặc", "diện", "vào", "trong", "mùa", "hè", "thu", "đông", "xuân", "hạ", "số", "chiếc", "cái", "cho", "tôi", "em", "mình"}
            valid_kw = [k for k in entities["keywords"] if k.lower() not in stop_kw]
            if valid_kw:
                clean_kw = " ".join(valid_kw)
        elif not category and not sub_category:
            keywords = [
                "blazer", "sơ mi", "polo", "thun", "khoác", "jean", "âu", "kaki", "đầm", "váy", "suit", "len",
                "giày", "ví", "cà vạt", "loe", "suông", "rộng", "baggy",
                "kẹp tóc", "càng cua", "quần tất", "tất", "dù", "phụ kiện"
            ]
            for w in keywords:
                if w in user_message.lower():
                    clean_kw = w
                    break
        elif sub_category in ["quần loe", "quần ống rộng", "quần ống suông", "quần baggy"]:
            if "loe" in sub_category:
                clean_kw = "loe"
            elif "suông" in sub_category:
                clean_kw = "suông"
            elif "rộng" in sub_category:
                clean_kw = "rộng"
            elif "baggy" in sub_category:
                clean_kw = "baggy"
        elif sub_category in ["áo khoác jeans", "áo khoác da", "áo khoác hoodie", "áo khoác gió", "áo khoác bomber", "áo măng tô"]:
            if "jean" in sub_category:
                clean_kw = "jean"
            elif "da" in sub_category:
                clean_kw = "da"
            elif "hoodie" in sub_category:
                clean_kw = "hoodie"
            elif "gió" in sub_category:
                clean_kw = "gió"
            elif "bomber" in sub_category:
                clean_kw = "bomber"
            elif "măng tô" in sub_category:
                clean_kw = "măng tô"

        # Xử lý ưu tiên cho đám cưới: Lọc đầm tiệc cưới, cấm tuyệt đối váy ngủ và màu trắng lấn át cô dâu
        if is_wedding_query:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE category = 'Váy & Đầm' 
                  AND (sub_category LIKE '%đầm%' OR tags LIKE '%đầm%')
                  AND sub_category NOT LIKE '%đồ mặc nhà%'
                  AND name NOT LIKE '%Váy Ngủ%'
                  AND color NOT IN ('trắng', 'trắng ngọc')
                ORDER BY price ASC LIMIT 4
            """)
            wedding_rows = cursor.fetchall()
            conn.close()
            if wedding_rows:
                return [self.db_service._format_product(r) for r in wedding_rows]

        # Xử lý ưu tiên cho váy ngủ / pijama
        if is_sleepwear_query:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (sub_category LIKE '%đồ mặc nhà%' OR name LIKE '%Váy Ngủ%' OR tags LIKE '%váy ngủ%')
                ORDER BY price ASC LIMIT 4
            """)
            sleep_rows = cursor.fetchall()
            conn.close()
            if sleep_rows:
                return [self.db_service._format_product(r) for r in sleep_rows]

        # 1. Ưu tiên Áo mùa hè
        if is_summer_query and user_asks_shirt_only:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (category IN ('Áo thun phông', 'Áo polo', 'Áo sơ mi', 'Áo thun'))
                  AND py_lower(category) NOT IN ('phụ kiện', 'quần tây', 'quần jean')
                  AND name NOT LIKE '%quần%' AND name NOT LIKE '%tất%'
                ORDER BY 
                  CASE 
                    WHEN name LIKE '%Cotton%' OR tags LIKE '%cotton%' OR tags LIKE '%mát%' OR tags LIKE '%hè%' THEN 1
                    WHEN category = 'Áo thun phông' OR category = 'Áo thun' THEN 2
                    WHEN category = 'Áo polo' THEN 3
                    WHEN category = 'Áo sơ mi' AND (name LIKE '%Ngắn Tay%' OR name LIKE '%Cộc Tay%' OR name LIKE '%Cuba%' OR name LIKE '%Cổ Tàu%') THEN 4
                    ELSE 5
                  END ASC, price ASC
                LIMIT 4
            """)
            summer_shirt_rows = cursor.fetchall()
            conn.close()
            if summer_shirt_rows:
                return [self.db_service._format_product(r) for r in summer_shirt_rows]

        # 2. Ưu tiên Quần mùa hè
        if is_summer_query and user_asks_pants_only:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (category IN ('Quần tây', 'Quần jean', 'Quần loe') OR sub_category IN ('quần short', 'quần khaki', 'quần jeans'))
                  AND name NOT LIKE '%áo%' AND name NOT LIKE '%tất%' AND name NOT LIKE '%nỉ%'
                ORDER BY 
                  CASE 
                    WHEN sub_category LIKE '%short%' OR name LIKE '%short%' THEN 1
                    WHEN name LIKE '%Khaki%' OR name LIKE '%Chino%' THEN 2
                    WHEN category = 'Quần jean' OR category = 'Quần loe' THEN 3
                    ELSE 4
                  END ASC, price ASC
                LIMIT 4
            """)
            summer_pants_rows = cursor.fetchall()
            conn.close()
            if summer_pants_rows:
                return [self.db_service._format_product(r) for r in summer_pants_rows]

        # 3. Ưu tiên Áo mùa đông
        if is_winter_query and user_asks_shirt_only:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (category = 'Áo khoác' OR sub_category IN ('áo khoác', 'áo len', 'áo măng tô', 'áo khoác bomber', 'áo khoác hoodie'))
                  AND py_lower(category) NOT IN ('phụ kiện', 'quần tây', 'quần jean')
                  AND name NOT LIKE '%quần%' AND name NOT LIKE '%tất%'
                ORDER BY 
                  CASE 
                    WHEN name LIKE '%Măng Tô%' OR tags LIKE '%măng tô%' THEN 1
                    WHEN name LIKE '%Chần Bông%' OR tags LIKE '%chần bông%' THEN 2
                    WHEN name LIKE '%Len%' OR sub_category = 'áo len' THEN 3
                    WHEN name LIKE '%Jeans%' OR name LIKE '%Biker%' THEN 4
                    WHEN name LIKE '%Hoodie%' OR name LIKE '%Bomber%' THEN 5
                    ELSE 6
                  END ASC, price ASC
                LIMIT 4
            """)
            winter_rows = cursor.fetchall()
            conn.close()
            if winter_rows:
                return [self.db_service._format_product(r) for r in winter_rows]

        # 4. Ưu tiên Quần mùa đông
        if is_winter_query and user_asks_pants_only:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (category IN ('Quần tây', 'Quần jean') OR sub_category IN ('quần jogger', 'quần jeans', 'quần âu'))
                  AND name NOT LIKE '%short%' AND name NOT LIKE '%áo%'
                ORDER BY 
                  CASE 
                    WHEN name LIKE '%Jogger%' OR name LIKE '%Nỉ%' OR sub_category = 'quần jogger' THEN 1
                    WHEN category = 'Quần jean' THEN 2
                    WHEN category = 'Quần tây' THEN 3
                    ELSE 4
                  END ASC, price ASC
                LIMIT 4
            """)
            winter_pants_rows = cursor.fetchall()
            conn.close()
            if winter_pants_rows:
                return [self.db_service._format_product(r) for r in winter_pants_rows]

        # 5. Ưu tiên Áo mùa thu
        if is_fall_query and user_asks_shirt_only:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (category IN ('Áo khoác', 'Áo sơ mi', 'Áo polo', 'Áo thun'))
                  AND name NOT LIKE '%quần%' AND name NOT LIKE '%tất%'
                ORDER BY 
                  CASE 
                    WHEN name LIKE '%Cardigan%' OR name LIKE '%Gió%' THEN 1
                    WHEN name LIKE '%Suit%' OR sub_category = 'blazer' THEN 2
                    WHEN category = 'Áo sơ mi' AND (name LIKE '%Dài Tay%' OR name LIKE '%Caro%' OR tags LIKE '%bamboo%' OR tags LIKE '%nano%') THEN 3
                    WHEN name LIKE '%Dài Tay%' THEN 4
                    ELSE 5
                  END ASC, price ASC
                LIMIT 4
            """)
            fall_rows = cursor.fetchall()
            conn.close()
            if fall_rows:
                return [self.db_service._format_product(r) for r in fall_rows]

        # 6. Ưu tiên Áo mùa xuân
        if is_spring_query and user_asks_shirt_only:
            conn = self.db_service._get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE (category IN ('Áo sơ mi', 'Áo polo', 'Áo khoác', 'Váy & Đầm', 'Áo thun phông'))
                  AND name NOT LIKE '%quần%' AND name NOT LIKE '%tất%' AND name NOT LIKE '%váy ngủ%' AND name NOT LIKE '%đồ ngủ%'
                ORDER BY 
                  CASE 
                    WHEN name LIKE '%Cổ Tàu%' OR name LIKE '%Lụa%' THEN 1
                    WHEN name LIKE '%Polo Dệt Kim%' THEN 2
                    WHEN name LIKE '%Cardigan%' THEN 3
                    WHEN name LIKE '%Pastel%' THEN 4
                    ELSE 5
                  END ASC, price ASC
                LIMIT 4
            """)
            spring_rows = cursor.fetchall()
            conn.close()
            if spring_rows:
                return [self.db_service._format_product(r) for r in spring_rows]

        products, _ = self.db_service.search_products(
            query=clean_kw,
            category=category,
            sub_category=sub_category,
            min_price=min_p,
            max_price=max_p,
            color=color,
            size=size,
            gender=gender,
            style=entities.get("style") or "",
            material=material,
            limit=4
        )

        is_specific_query = bool(
            clean_kw
            or material
            or color
            or sub_category
            or any(kw in user_message.lower() for kw in [
                "loe", "ống loe", "baggy", "ống rộng", "ống suông", "douyin", "y2k", "cạp thấp",
                "short", "khaki", "kaki", "sơ mi", "polo", "blazer", "lông cừu", "lông vũ"
            ])
        )

        # CHỈ bổ sung thêm sản phẩm khi ĐÃ TÌM THẤY ít nhất 1 sản phẩm thực tế (1 <= len(products) < 2)
        # và câu hỏi mang tính gợi ý mở, không phải tìm kiếm sản phẩm cụ thể.
        # TUYỆT ĐỐI KHÔNG bổ sung khi len(products) == 0 để tránh hiển thị sản phẩm ngẫu nhiên khi shop không có hàng.
        if not is_specific_query and intent != "product_detail" and (1 <= len(products) < 2) and (category or entities.get("occasion")):
            extra_products = self.recommender.recommend(entities, limit=4)
            seen_ids = {p["id"] for p in products}
            for p in extra_products:
                if p["id"] not in seen_ids:
                    products.append(p)
                    seen_ids.add(p["id"])

        is_general_browse = any(kw in user_message.lower() for kw in [
            "xem mẫu", "gợi ý", "sản phẩm hot", "bán chạy", "mới về", "có gì mới", "có gì hot", "có gì đẹp", "xem đồ", "mẫu đẹp", "outfit", "set đồ"
        ])
        if not products and is_general_browse and not is_specific_query and not category:
            products, _ = self.db_service.search_products(limit=4)

        # Post-filter: Loại bỏ sản phẩm không phù hợp khi người dùng rõ ràng chỉ hỏi về "áo"
        # VD: Hỏi "áo ấm mùa đông" thì không trả về quần tất, legging, chân váy...
        if user_asks_shirt_only and products:
            non_shirt_keywords = ["quần tất", "legging", "chân váy", "quần short", "quần jean", "quần âu", "quần tây", "thắt lưng", "ví da", "kính mát", "giày", "dù"]
            filtered = []
            for p in products:
                p_name = (p.get("name") or "").lower()
                p_cat = (p.get("category") or "").lower()
                is_non_shirt = any(nsk in p_name for nsk in non_shirt_keywords) or p_cat in ["phụ kiện", "quần tây", "quần jean", "quần loe"]
                if not is_non_shirt:
                    filtered.append(p)
            if filtered:
                products = filtered

        return products[:4]

    def _check_unsupported_item(self, msg: str) -> Tuple[bool, str]:
        """
        Phát hiện khi khách hàng hỏi về các mặt hàng thời trang/phụ kiện mà shop KHÔNG kinh doanh
        (như: mũ/nón, túi xách/balo, trang sức/vòng cổ/khuyên tai, giày cao gót/dép, đồ bơi, đồ lót, đồ em bé, mỹ phẩm...)
        Tự động thông báo rõ ràng là shop chưa có những sản phẩm này kèm giới thiệu danh mục hiện có.
        """
        msg_l = msg.lower().strip()
        
        unsupported_map = [
            (
                r"\b(?:mũ|nón|mũ len|mũ lưỡi trai|nón kết|nón bucket|mũ bucket|mũ nồi|mũ beret|mũ tai bèo|nón lá|mũ bảo hiểm|hat|cap)\b",
                "mũ / nón thời trang"
            ),
            (
                r"\b(?:túi xách|túi tote|túi đeo chéo|túi bao tử|túi đeo|handbag|tote bag|crossbody|balo|ba lô|backpack|cặp sách|vali)\b",
                "túi xách, balo hay cặp túi"
            ),
            (
                r"\b(?:vòng cổ|dây chuyền|khuyên tai|bông tai|hoa tai|nhẫn|lắc tay|vòng tay|đồng hồ|vòng đeo tay)\b",
                "trang sức (vòng cổ, khuyên tai, nhẫn, đồng hồ)"
            ),
            (
                r"\b(?:giày cao gót|guốc|dép|dép lê|dép quai hậu|sandal|xăng đan|dép xỏ ngón|ủng)\b",
                "giày cao gót, dép hay sandal"
            ),
            (
                r"\b(?:đồ lót|áo lót|quần lót|bra|áo ngực|nội y|quần sịp|boxer|underwear)\b",
                "đồ lót / nội y"
            ),
            (
                r"\b(?:đồ bơi|bikini|áo tắm|quần bơi|đồ tắm|swimwear)\b",
                "đồ bơi / đồ tắm biển"
            ),
            (
                r"\b(?:đồ trẻ em|quần áo trẻ em|đồ em bé|đồ sơ sinh|quần áo bé trai|quần áo bé gái|váy bé gái|quần áo trẻ con)\b",
                "quần áo trẻ em hay đồ sơ sinh"
            ),
            (
                r"\b(?:mỹ phẩm|son|son môi|nước hoa|phấn|kem dưỡng|skincare|makeup)\b",
                "mỹ phẩm, son môi hay nước hoa"
            )
        ]

        for pattern, display_name in unsupported_map:
            if re.search(pattern, msg_l):
                # Ngoại lệ: "có mũ" trong "áo khoác có mũ" / "hoodie có mũ"
                if "có mũ" in msg_l or "kèm mũ" in msg_l or "liền mũ" in msg_l:
                    if any(w in msg_l for w in ["áo", "khoác", "hoodie", "bomber", "phao"]):
                        continue
                reply = (
                    f"Dạ hiện tại bên Evern Fashion **chưa có kinh doanh mặt hàng {display_name}** rồi bạn ơi! 🥺\n\n"
                    f"Showroom của tụi mình chuyên về các dòng thời trang thiết kế cao cấp hiện đại cho cả nam và nữ:\n"
                    f"👔 **1. Áo thời trang:** Áo sơ mi công sở/lụa, Áo polo dệt kim/cotton, Áo thun basic/oversize, Áo khoác blazer, bomber, măng tô, hoodie nỉ, áo len...\n"
                    f"👖 **2. Các dòng quần:** Quần tây âu đứng phom, Quần jeans ống suông/loe/baggy, Quần kaki, Quần short...\n"
                    f"👗 **3. Váy & Đầm thiết kế:** Đầm dạ hội, đầm tiệc cưới, chân váy chữ A/xếp ly, váy ngủ lụa satin...\n"
                    f"👟 **4. Giày da & Phụ kiện:** Giày sneaker retro da thật, Giày tây Oxford/Derby, Thắt lưng da bò, Ví da nam, Cà vạt lụa, Kính mát titanium, Quần tất, Kẹp tóc...\n\n"
                    f"Bạn có muốn tham khảo các mẫu trang phục có sẵn nào khác của shop không nè? Evern Stylist luôn sẵn sàng hỗ trợ bạn! ❤️"
                )
                return True, reply

        return False, ""

    def _is_catalog_overview_query(self, msg: str) -> bool:
        """Phát hiện câu hỏi hỏi về danh mục tổng quan các mặt hàng shop kinh doanh."""
        msg_l = msg.lower().strip()
        # Nếu có từ khóa hỏi cụ thể một món đồ ("shop có bán áo polo không", "có quần jean không")
        if any(w in msg_l for w in ["không", "ko", "chưa", "k0"]):
            specific_items = ["áo", "quần", "váy", "đầm", "sơ mi", "polo", "thun", "khoác", "jean", "âu", "kaki", "sịp", "lót", "giày", "ví", "thắt lưng", "blazer", "chinos", "short", "đồ lót", "nội y", "bikini"]
            if any(it in msg_l for it in specific_items):
                return False

        catalog_patterns = [
            r"\b(?:bán gì|bán những gì|bán cái gì|bán những cái gì|kinh doanh gì|kinh doanh những gì|có những mặt hàng gì|có những sản phẩm nào|có những đồ gì|có đồ gì bán|bán đồ gì|bán các loại đồ nào)\b",
            r"\b(?:danh mục sản phẩm|danh mục hàng|danh sách mặt hàng|các mặt hàng của shop|các dòng sản phẩm|tất cả mặt hàng)\b",
            r"\b(?:shop|cửa hàng|bên shop|bên bạn|ở đây|showroom|evern)\s+(?:có|bán|kinh doanh|có bán|đang bán)\s+(?:những|các)?\s*(?:gì|cái gì|mặt hàng gì|sản phẩm gì|món gì|đồ gì)\b",
            r"^(?:bên shop|shop|cửa hàng|ở đây|evern)?\s*(?:có gì|bán gì|kinh doanh gì|có những gì|bán những gì|bán những cái gì|có bán những gì)\??$"
        ]
        return any(re.search(pat, msg_l) for pat in catalog_patterns)

    def _fetch_catalog_showcase_products(self) -> List[Dict[str, Any]]:
        """Lấy 4 sản phẩm đại diện tiêu biểu (1 Áo, 1 Quần, 1 Váy/Đầm, 1 Phụ kiện) để hiển thị khi khách hỏi shop bán gì."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        showcase = []

        # 1. Một mẫu áo tiêu biểu (Sơ mi hoặc Polo)
        cursor.execute("SELECT * FROM products WHERE category IN ('Áo sơ mi', 'Áo polo') AND stock > 0 ORDER BY id ASC LIMIT 1")
        row_shirt = cursor.fetchone()
        if row_shirt:
            showcase.append(self.db_service._format_product(row_shirt))

        # 2. Một mẫu quần tiêu biểu (Quần tây hoặc Quần jean)
        cursor.execute("SELECT * FROM products WHERE category IN ('Quần tây', 'Quần jean') AND stock > 0 ORDER BY id ASC LIMIT 1")
        row_pants = cursor.fetchone()
        if row_pants:
            showcase.append(self.db_service._format_product(row_pants))

        # 3. Một mẫu Váy/Đầm tiêu biểu
        cursor.execute("SELECT * FROM products WHERE category = 'Váy & Đầm' AND stock > 0 ORDER BY id ASC LIMIT 1")
        row_dress = cursor.fetchone()
        if row_dress:
            showcase.append(self.db_service._format_product(row_dress))

        # 4. Một mẫu Phụ kiện / Giày tiêu biểu
        cursor.execute("SELECT * FROM products WHERE category = 'Phụ kiện' AND stock > 0 ORDER BY id ASC LIMIT 1")
        row_acc = cursor.fetchone()
        if row_acc:
            showcase.append(self.db_service._format_product(row_acc))

        conn.close()
        return showcase

    def respond(
        self,
        user_message: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        current_product: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Xử lý tin nhắn của khách hàng có bộ nhớ ngữ cảnh đa lượt (Multi-turn Context Memory):
        1. Phục hồi ngữ cảnh trò chuyện từ session/user_id để hiểu các đại từ ('mẫu này', 'nó', 'áo vừa rồi').
        2. Nhận diện ý định và thực thể chính xác, loại bỏ hoàn toàn việc phân loại nhầm sang 'order'.
        3. Truy cập CSDL SQLite để lấy sản phẩm thực tế (kèm bảng thông số, thẻ Card UI).
        4. Tích hợp Local LLM (Ollama) truyền đầy đủ lịch sử hội thoại gần nhất để sinh lời tư vấn mượt mà.
        5. Cập nhật bộ nhớ ngữ cảnh và lưu lịch sử chat vào SQLite.
        """
        if not user_message or not user_message.strip():
            return {
                "reply": "Dạ Evern chào bạn nha! ✨ Mình là Evern AI Stylist. Bạn đang tìm trang phục nào cho hôm nay hay cần mình gợi ý mẫu đẹp nhé? 😊",
                "intent": "greeting",
                "confidence": 1.0,
                "entities": {},
                "products": [],
                "ai_pipeline": "default",
                "local_llm_used": False
            }

        msg = user_message.strip()
        session_key = self._get_session_key(user_id, session_id)
        context = self._get_context(session_key, user_id=user_id)

        # 0. Kiểm tra câu hỏi ngoài phạm vi (Out-of-scope: máy móc cơ khí, sách, thiết bị điện tử, IT...)
        is_oos, oos_reply = self._check_out_of_scope(msg)
        if is_oos:
            # Giải phóng sản phẩm đang ghim khỏi bộ nhớ ngữ cảnh
            context["active_product"] = None
            context["last_products"] = []
            self._update_context(session_key, msg, oos_reply, "out_of_scope", [], {})
            self.log_chat(msg, oos_reply, intent="out_of_scope", user_id=user_id)
            return {
                "reply": oos_reply,
                "intent": "out_of_scope",
                "confidence": 1.0,
                "entities": {},
                "products": [],
                "ai_pipeline": "local_guardrail",
                "local_llm_used": False,
                "gemini_used": False
            }

        # 0.05 Kiểm tra các mặt hàng mà shop KHÔNG kinh doanh (mũ/nón, túi xách/balo, trang sức, đồ bơi, đồ lót, đồ em bé...)
        is_unsupported, unsupported_reply = self._check_unsupported_item(msg)
        if is_unsupported:
            context["active_product"] = None
            context["last_products"] = []
            self._update_context(session_key, msg, unsupported_reply, "search_product", [], {})
            self.log_chat(msg, unsupported_reply, intent="search_product", user_id=user_id)
            return {
                "reply": unsupported_reply,
                "intent": "search_product",
                "confidence": 1.0,
                "entities": {},
                "products": [],
                "ai_pipeline": "catalog_unsupported_guardrail",
                "local_llm_used": False,
                "gemini_used": False
            }

        # 0.1 Kiểm tra câu hỏi hỏi về danh mục tổng quan các mặt hàng shop kinh doanh ("shop bán những cái gì")
        if self._is_catalog_overview_query(msg):
            showcase_products = self._fetch_catalog_showcase_products()
            catalog_reply = (
                "Dạ Evern Fashion là thương hiệu thời trang thiết kế cao cấp, chuyên cung cấp các dòng trang phục hiện đại, thanh lịch và chuẩn xu hướng cho cả nam và nữ: ✨\n\n"
                "👔 1. **Áo thời trang nam & nữ:**\n"
                "• **Áo sơ mi:** Sơ mi công sở cao cấp, sơ mi lụa, sơ mi linen thoáng mát, sơ mi form rộng Hàn Quốc.\n"
                "• **Áo polo:** Polo cotton thoáng mát, polo dệt kim retro thanh lịch và tôn dáng.\n"
                "• **Áo thun / Phông:** Basic casual, áo thun oversize streetwear cá tính, năng động.\n"
                "• **Áo khoác thời thượng:** Blazer may đo chỉn chu, áo khoác jeans đen chỉ nổi, bomber, áo gió dù cản nước, măng tô dạ mùa đông.\n\n"
                "👖 2. **Các dòng quần tôn dáng:**\n"
                "• **Quần tây / Quần âu:** Phom đứng chuẩn chỉ, chất vải tuyết mưa mềm mại, chống nhăn cực tốt.\n"
                "• **Quần jeans:** Jeans ống suông vintage, jeans loe nhẹ hack chân dài, baggy, skinny cạp cao.\n"
                "• **Quần khaki / chinos & quần short:** Thoải mái, năng động cho ngày hè dạo phố.\n\n"
                "👗 3. **Váy & Đầm thiết kế nữ:**\n"
                "• **Đầm dạ hội / Đầm tiệc cưới:** Sang trọng, quý phái, kiêu sa dưới ánh đèn.\n"
                "• **Đầm dạo phố & Đầm maxi:** Bay bổng, nữ tính, rực rỡ khi đi du lịch, đi biển.\n"
                "• **Chân váy:** Chân váy chữ A thanh lịch, chân váy xếp ly tennis trẻ trung, đầm body tôn đường cong.\n"
                "• **Váy ngủ & Pijama:** Váy ngủ lụa satin mềm mượt, pijama mặc nhà êm ái, cao cấp.\n\n"
                "👟 4. **Giày da & Phụ kiện thời trang:**\n"
                "• Giày sneaker retro da thật, giày loafer quý ông lịch lãm.\n"
                "• Thắt lưng da bò nguyên tấm, ví da nam, cà vạt lụa, kính mát thời thượng...\n\n"
                "🛍️ *Dưới đây là một số mẫu sản phẩm tiêu biểu đại diện cho các dòng hàng đang rất được ưa chuộng tại showroom, bạn tham khảo nhé!*\n\n"
                "💡 Bạn có thể bấm vào mục **'Sản phẩm'** trên thanh menu để xem trọn bộ sưu tập, hoặc chia sẻ với Evern Stylist nhu cầu cụ thể (VD: *'Tìm áo polo dưới 300k'*, *'Tư vấn outfit đi cafe với bạn'*) để mình hỗ trợ bạn ngay nhé! ❤️"
            )
            context["active_product"] = None
            context["last_products"] = showcase_products
            self._update_context(session_key, msg, catalog_reply, "greeting", showcase_products, {})
            self.log_chat(msg, catalog_reply, intent="greeting", user_id=user_id)
            return {
                "reply": catalog_reply,
                "intent": "greeting",
                "confidence": 1.0,
                "entities": {},
                "products": showcase_products,
                "ai_pipeline": "catalog_overview",
                "local_llm_used": False,
                "gemini_used": False
            }

        # 1. Bóc tách thực thể và giải quyết đại từ chỉ định từ ngữ cảnh trước
        entities = EntityExtractor.extract(msg)
        entities, resolved_product = self._resolve_anaphora(msg, entities, context, current_product=current_product)

        # Kế thừa thông tin nhân trắc học và sở thích nếu lượt này khách chưa cung cấp mới
        last_ents = context.get("last_entities", {})
        for trait in ["height", "weight", "gender", "style", "age"]:
            if not entities.get(trait) and last_ents.get(trait):
                entities[trait] = last_ents[trait]

        # 2. Phân loại ý định
        intent, conf, default_reply = self.intent_classifier.predict(msg)

        # Nếu người dùng đang tham chiếu đến 1 sản phẩm cụ thể từ lượt trước (mẫu 1, mẫu này, gửi chiều cao/cân nặng...)
        # Hoặc đang tham chiếu đến CẢ SET ĐỒ vừa gợi ý
        if resolved_product or entities.get("is_set_reference"):
            msg_lower = msg.lower()
            if entities.get("height") or entities.get("weight") or any(w in msg_lower for w in ["size", "bảng size", "chọn size", "mặc vừa", "mặc size gì", "số đo", "vừa không", "tư vấn size"]):
                intent = "size_guide"
                conf = 0.99
            elif any(w in msg_lower for w in ["giá", "nhiêu", "tiền", "sale", "bao nhiêu", "đắt"]):
                intent = "product_price"
                conf = 0.99
            elif any(w in msg_lower for w in ["còn hàng", "hết hàng", "còn không", "kho"]):
                intent = "product_stock"
                conf = 0.99
            elif any(w in msg_lower for w in [
                "tư vấn", "chi tiết", "vải gì", "form gì", "giới thiệu", "thông số", 
                "thế nào", "chất liệu", "thông tin", "xem kỹ", "hỏi về", "mẫu", "cái", "sp", "sản phẩm"
            ]):
                intent = "product_detail"
                conf = 0.99
            elif any(w in msg_lower for w in ["mẫu này", "áo này", "quần này", "váy này", "đầm này", "nó", "cái này"]):
                intent = "product_detail"
                conf = 0.95

        is_prod = self._is_product_query(msg, intent, entities)

        products = []
        local_llm_used = False
        reply = ""

        if is_prod:
            if entities.get("is_set_reference") and context.get("last_products"):
                all_set_prods = list(context["last_products"])
                msg_l = msg.lower()

                # Kiểm tra xem người dùng có yêu cầu cụ thể "áo và quần" / "áo với quần"
                wants_shirt = any(w in msg_l for w in ["áo", "ao", "sơ mi", "so mi", "polo", "thun", "khoác", "khoac"])
                wants_pants = any(w in msg_l for w in ["quần", "quan", "jean", "âu", "au", "kaki", "tây", "tay", "short"])
                wants_shoes_acc_or_all = any(w in msg_l for w in ["giày", "giay", "sneaker", "phụ kiện", "phu kien", "tất cả", "tat ca", "full", "cả 3", "ba món", "hết", "toàn bộ", "cả set", "cả bộ"])

                if wants_shirt and wants_pants and not wants_shoes_acc_or_all:
                    filtered_set = []
                    found_shirt = False
                    found_pants = False
                    for p in all_set_prods:
                        cat = ((p.get("category") or "") + " " + (p.get("sub_category") or "") + " " + p.get("name", "")).lower()
                        is_p_shirt = any(w in cat for w in ["áo", "sơ mi", "polo", "thun", "khoác", "len", "blazer", "vest"])
                        is_p_pants = any(w in cat for w in ["quần", "jean", "âu", "tây", "kaki", "short", "loe", "jogger", "chinos"])
                        
                        if is_p_shirt and not found_shirt:
                            filtered_set.append(p)
                            found_shirt = True
                        elif is_p_pants and not found_pants:
                            filtered_set.append(p)
                            found_pants = True
                    if len(filtered_set) >= 2:
                        products = filtered_set
                    else:
                        products = all_set_prods
                else:
                    products = all_set_prods
            else:
                # Truy xuất sản phẩm từ SQLite (hỗ trợ đề xuất Outfit trọn bộ khi tư vấn phối đồ)
                products = self._fetch_products_from_db(msg, entities, resolved_product=resolved_product, intent=intent)

            # Nếu KHÔNG tìm thấy sản phẩm nào trong CSDL SQLite:
            # Tự động thông báo rõ ràng là shop chưa có những sản phẩm này theo đúng yêu cầu
            if not products:
                empty_reply = ResponseGenerator.generate(
                    intent="empty_product",
                    entities=entities,
                    products=[],
                    db_info={},
                    default_dataset_reply="",
                    user_message=msg,
                    context=context
                )
                context["active_product"] = None
                context["last_products"] = []
                self._update_context(session_key, msg, empty_reply, intent, [], entities)
                self.log_chat(msg, empty_reply, intent=intent, user_id=user_id)
                return {
                    "reply": empty_reply,
                    "intent": intent,
                    "confidence": conf,
                    "entities": entities,
                    "products": [],
                    "ai_pipeline": "database_empty_guardrail",
                    "local_llm_used": False,
                    "gemini_used": False
                }

            # Nếu người dùng yêu cầu tư vấn chi tiết hoặc hỏi thông tin 1 mẫu sản phẩm cụ thể
            # Chỉ giữ lại DUY NHẤT sản phẩm đó trên danh sách UI Card để tránh lấy tràn lan cả loạt sản phẩm cùng loại
            is_single_item_query = (
                not entities.get("is_set_reference")
                and (
                    intent in ["product_detail", "product_price", "product_stock"]
                    or bool(resolved_product)
                    or any(w in msg.lower() for w in ["tư vấn chi tiết", "chi tiết cho tôi", "thông tin chi tiết", "xem chi tiết", "cho tôi áo khoác jeans"])
                )
            )
            is_outfit_intent = (intent in ["recommendation", "style_young", "style_office", "style_mature", "men_fashion"] or entities.get("is_outfit_query") or entities.get("is_set_reference"))
            if is_single_item_query and not is_outfit_intent and products:
                products = [products[0]]
            db_info = {}
            if products and intent in ["product_price", "product_stock", "product_detail"]:
                db_info["product"] = products[0]
                _, db_info["stock_status"] = self.db_service.check_stock(
                    str(products[0].get("id", "")),
                    size=entities.get("size") or "",
                    color=entities.get("color") or ""
                )

            # Tạo câu trả lời dự phòng bằng ResponseGenerator (100% chuẩn sản phẩm từ SQLite)
            draft_reply = ResponseGenerator.generate(
                intent=intent,
                entities=entities,
                products=products,
                db_info=db_info,
                default_dataset_reply=default_reply,
                user_message=msg,
                context=context
            )

            # Lấy cẩm nang phối đồ RAG nếu có
            styling_guide = ""
            try:
                rag_docs = self.rag_engine.retrieve(msg, top_k=2)
                guide_parts = [doc.page_content for doc, _ in rag_docs if doc.metadata.get("type") != "product"]
                if guide_parts:
                    styling_guide = "\n\n".join(guide_parts[:2])
            except Exception:
                pass

            intent_map = {
                "recommendation": "Tư vấn gợi ý outfit thời trang",
                "product_detail": "Tư vấn thông số và thiết kế chi tiết sản phẩm",
                "style_young": "Tư vấn phong cách trẻ trung năng động Douyin Gen Z",
                "style_office": "Tư vấn phong cách công sở thanh lịch",
                "men_fashion": "Tư vấn thời trang nam"
            }
            intent_friendly = intent_map.get(intent, intent)

            # Gọi Local LLM (Ollama) kết hợp Lịch sử hội thoại
            try:
                # Lọc sạch context turns nếu câu hỏi hiện tại có chủ đề / dịp / sản phẩm mới
                clean_history = []
                raw_turns = context.get("turns", [])
                msg_low = msg.lower()
                is_wedding_query = any(w in msg_low for w in ["đám cưới", "tiệc cưới", "dự cưới", "khách sạn 5 sao", "5 sao", "cô dâu"])
                is_category_switch = bool(entities.get("category") and resolved_product is None)
                is_occasion_switch = bool(entities.get("occasion"))
                is_new_topic = (
                    is_wedding_query
                    or is_category_switch
                    or is_occasion_switch
                    or any(w in msg_low for w in ["váy ngủ", "đi biển", "du lịch", "ở nhà", "set đồ", "outfit", "mẫu khác", "đổi mẫu"])
                )

                # Chỉ truyền lịch sử khi người dùng đang tiếp tục câu chuyện/sản phẩm hiện tại
                if not is_new_topic:
                    for turn in raw_turns:
                        t_text = turn.get("text", "").lower()
                        if any(w in t_text for w in ["phỏng vấn", "ngân hàng", "tuyển dụng", "xin việc"]):
                            continue
                        clean_history.append(turn)

                llm_reply = self.llm_service.assist_stylist_response(
                    user_message=msg,
                    intent=intent_friendly,
                    products=products,
                    facts_summary=styling_guide,
                    draft_reply=draft_reply,
                    chat_history=clean_history
                )
                
                llm_lower = llm_reply.lower()
                has_product_mention = False
                for p in products[:3]:
                    p_name = (p.get("name") or "").lower()
                    p_code = (p.get("code") or "").lower()
                    clean_name = re.sub(r"-\s*[a-z0-9]+", "", p_name).strip()
                    sub_cat = (p.get("sub_category") or p.get("category") or "").lower()
                    if (p_code and p_code in llm_lower) or (clean_name and len(clean_name) >= 5 and clean_name in llm_lower) or (sub_cat and sub_cat in llm_lower):
                        has_product_mention = True
                        break

                is_styling_reply = any(w in llm_lower for w in ["phối", "outfit", "set đồ", "kết hợp", "chủ nhật", "mát mẻ", "đi chơi", "áo thun", "quần jeans", "sneaker", "áo khoác", "đầm", "váy"])

                is_counter_question = any(kw in llm_reply.lower() for kw in [
                    "nói tên hoặc mã", "cho mình xin mã", "bạn muốn tìm sản phẩm theo", 
                    "tìm sản phẩm nào", "muốn tìm sản phẩm nào", "kiểm tra danh sách sản phẩm", 
                    "style_young", "style_office", "cho mình biết màu", "bạn cho mình biết",
                    "gửi mình tên", "gửi tên hoặc mã", "gửi mình mã", "gửi mã sản phẩm",
                    "chọn sản phẩm cụ thể", "sản phẩm cụ thể", "gửi cho mình tên", "bạn gửi mình",
                    "bạn muốn tìm kiếm trang phục nào", "muốn tìm kiếm trang phục nào", 
                    "rất xin lỗi vì đã gây nhầm lẫn", "gây nhầm lẫn"
                ])
                
                is_single_product_degeneration = False
                if len(products) >= 2 and intent in ["recommendation", "style_young", "style_office", "men_fashion"]:
                    if any(phrase in llm_lower for phrase in ["hướng dẫn bạn lựa chọn mẫu", "hướng dẫn lựa chọn mẫu", "lựa chọn mẫu **áo thun", "lựa chọn mẫu áo thun"]):
                        is_single_product_degeneration = True
                    elif not any(w in llm_lower for w in ["quần", "jeans", "giày", "sneaker", "khoác", "set đồ", "outfit", "combo", "phối cùng", "đầm", "váy"]):
                        is_single_product_degeneration = True

                is_prompt_leak = self.llm_service.has_prompt_leakage(llm_reply)

                # Chống nhiễm ngữ cảnh cũ (Context Bleeding Guardrails)
                is_context_corrupted = False
                if not any(w in msg_low for w in ["phỏng vấn", "ngân hàng", "tuyển dụng"]) and any(w in llm_lower for w in ["phỏng vấn", "ngân hàng", "quan hệ khách hàng"]):
                    is_context_corrupted = True
                if not any(w in msg_low for w in ["váy ngủ", "đồ ngủ", "ngủ"]) and any(w in llm_lower for w in ["váy ngủ", "đồ ngủ", "ngủ"]):
                    is_context_corrupted = True
                if not any(w in msg_low for w in ["chân váy", "chan vay", "skirt"]) and any(w in llm_lower for w in ["chân váy", "cv250807", "chân váy xếp ly"]):
                    is_context_corrupted = True
                # 1. Phát hiện câu cú lủng củng, dịch máy, xưng hô sai hoặc không tự nhiên
                is_awkward_language = any(kw in llm_lower for kw in [
                    "chào mọi người", "chào các bạn", "chào cả nhà", "tôi sẽ giúp bạn", "tôi rất vui được",
                    "có những gợi ý set đồ cực kì ưng ý cho dịp này không nào", "hãy cùng xem nhé",
                    "chuẩn bài", "cực kì thời trang và lịch lãm cho bạn", "quý khách của bạn", "cô gái của bạn",
                    "bạn có muốn chọn áo polo", "bạn có muốn chọn áo", "được giới thiệu những sản phẩm phù hợp với",
                    "nếu cần thêm thông tin"
                ])

                # 2. Phát hiện câu bị cắt cụt lửng lơ do hết token
                clean_end = llm_reply.strip()
                valid_endings = ('.', '!', '?', '…', '✨', '🌟', '🥰', '❤️', '😊', '😄', '🛍️', '"', "'", '”')
                is_cut_off = not clean_end.endswith(valid_endings)

                # Kiểm tra độ tin cậy và chất lượng của câu trả lời từ LLM
                is_valid_llm = (
                    llm_reply 
                    and llm_reply.strip() 
                    and not is_prompt_leak
                    and not is_context_corrupted
                    and not is_counter_question 
                    and not is_single_product_degeneration 
                    and not is_awkward_language
                    and not is_cut_off
                    and len(llm_reply) >= 80
                    and (has_product_mention or is_styling_reply)
                )

                if intent == "product_detail":
                    # Khách yêu cầu tư vấn chi tiết thông số: dùng draft_reply chuẩn xác tuyệt đối từ CSDL (chất liệu, cạp quần, form dáng, giá, size)
                    reply = draft_reply
                elif intent == "size_guide" and (entities.get("height") or entities.get("weight")):
                    # Tư vấn size theo chiều cao/cân nặng: dùng bảng tính chuẩn xác số học, tránh LLM suy đoán mơ hồ
                    reply = draft_reply
                elif is_valid_llm:
                    # Ưu tiên câu trả lời mượt mà, ngôn từ tự nhiên từ Local LLM / Stylist
                    reply = llm_reply
                    local_llm_used = True
                else:
                    reply = draft_reply
            except Exception as e:
                print(f"[Chatbot] Local LLM stylist exception: {e}")
                reply = draft_reply

        else:
            if entities.get("category") and intent not in ["complaint", "shipping_return", "store_location", "payment_method", "care_instruction", "greeting", "goodbye"]:
                products = self._fetch_products_from_db(msg, entities, resolved_product=resolved_product)

            # Trả lời tức thì (< 0.005s) cho các câu hỏi chính sách / chào hỏi tiêu chuẩn / khiếu nại đã có câu trả lời chuẩn xác từ intents.json
            quick_reply_intents = [
                "greeting", "goodbye", "shipping_return", "store_location", 
                "payment_method", "care_instruction", "thank_you", "complaint",
                "discount", "weather"
            ]
            if intent in quick_reply_intents and default_reply and len(default_reply.strip()) > 10:
                reply = default_reply
            else:
                rag_output = self.rag_engine.query(msg)
                rag_reply = rag_output.get("reply", "")

                clean_rag = re.sub(r"\[.*?(?:\.md|\.txt|catalog)\]", "", rag_reply, flags=re.IGNORECASE)
                clean_rag = re.sub(r"^#+\s*", "", clean_rag, flags=re.MULTILINE).strip()

                try:
                    llm_reply = self.llm_service.assist_knowledge_response(
                        user_message=msg,
                        knowledge_context=clean_rag,
                        draft_reply=clean_rag or default_reply
                    )
                    is_evasive = any(kw in llm_reply.lower() for kw in [
                        "bạn gửi tên hoặc mã", "cho mình xin mã", "nói tên hoặc mã", 
                        "bạn muốn tìm sản phẩm", "muốn tìm sản phẩm nào", "kiểm tra bảng màu của mẫu",
                        "kiểm tra danh sách sản phẩm"
                    ])
                    if llm_reply and not is_evasive and len(llm_reply.strip()) > 30:
                        reply = llm_reply
                        local_llm_used = True
                    else:
                        reply = clean_rag or default_reply
                except Exception as e:
                    print(f"[Chatbot] Local LLM knowledge exception: {e}")
                    reply = clean_rag or default_reply

        # Cập nhật bộ nhớ ngữ cảnh đa lượt
        self._update_context(session_key, msg, reply, intent, products, entities)

        # Lưu lịch sử chat vào CSDL SQLite
        self.log_chat(msg, reply, intent=intent, user_id=user_id)

        return {
            "reply": reply,
            "intent": intent,
            "confidence": conf,
            "entities": entities,
            "products": products,
            "ai_pipeline": "sqlite_local_llm" if local_llm_used else "sqlite_local_rules",
            "local_llm_used": local_llm_used,
            "gemini_used": False
        }
