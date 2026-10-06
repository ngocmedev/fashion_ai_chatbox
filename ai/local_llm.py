import os
import json
import requests
from typing import Dict, Any, List, Optional

class LocalLLMService:
    """
    Dịch vụ điều phối LLM Cục Bộ (Local LLM) không cần API key.
    - Ưu tiên: Kết nối tới Ollama engine (http://127.0.0.1:11434) chạy các model như qwen2.5:1.5b, qwen2.5:3b, llama3.2:3b.
    - Dự phòng: Nếu Ollama chưa bật, hệ thống kích hoạt bộ tổng hợp tri thức RAG thông minh nội bộ, đảm bảo 100% không bao giờ gián đoạn dịch vụ.
    """
    def __init__(self, model_name: str = "qwen2.5:1.5b", base_url: str = "http://127.0.0.1:11434"):
        self.model_name = os.environ.get("OLLAMA_MODEL", model_name)
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url)
        self.timeout = int(os.environ.get("OLLAMA_TIMEOUT", "6"))  # Tối ưu 6s timeout để không bị chờ lâu trên CPU

    def check_ollama_status(self) -> Dict[str, Any]:
        """Kiểm tra xem máy chủ Ollama đã khởi động chưa và danh sách model sẵn có."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                
                # Ưu tiên model do người dùng tự train hoặc model 3B chất lượng cao nếu có sẵn
                active_model = self.model_name
                if any("evern-ai-stylist" in m for m in models):
                    active_model = "evern-ai-stylist"
                elif any("qwen2.5:3b" in m or "qwen:3b" in m for m in models):
                    active_model = [m for m in models if "3b" in m and "qwen" in m][0]
                elif not any(self.model_name in m for m in models) and models:
                    active_model = models[0]

                has_target_model = any(active_model in m for m in models)
                return {
                    "running": True,
                    "models": models,
                    "has_model": has_target_model,
                    "selected_model": active_model
                }
        except Exception:
            pass
        return {
            "running": False,
            "models": [],
            "has_model": False,
            "selected_model": self.model_name
        }

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Gửi prompt tới Local LLM (Ollama) hoặc dùng fallback synthesizer."""
        status = self.check_ollama_status()
        
        # 1. Nếu Ollama đang chạy
        if status["running"]:
            try:
                active_model = status.get("selected_model", self.model_name)

                payload = {
                    "model": active_model,
                    "prompt": prompt,
                    "system": system_prompt or (
                        "Bạn là Evern AI Stylist - chuyên gia tư vấn thời trang cao cấp của thương hiệu Evern. "
                        "Hãy tư vấn nhiệt tình, thân thiện, duyên dáng, chuẩn xác dựa trên dữ liệu cửa hàng được cung cấp. "
                        "Không trả lời sai lệch thông tin trong ngữ cảnh. "
                        "Bắt buộc trả lời 100% bằng Tiếng Việt tự nhiên, lưu loát, tuyệt đối không chêm chữ tiếng Trung hay từ ngữ ngoại lai."
                    ),
                    "stream": False,
                    "options": {
                        "temperature": 0.45,
                        "top_p": 0.85,
                        "repeat_penalty": 1.15,
                        "num_ctx": 1024,
                        "num_predict": 180
                    }
                }
                
                res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    result = res.json()
                    response_text = result.get("response", "").strip()
                    if response_text:
                        return response_text
            except Exception as e:
                print(f"[LocalLLM] Lỗi gọi Ollama: {e}, chuyển sang fallback synthesizer.")

        # 2. Bộ tổng hợp tri thức RAG thông minh (khi chưa bật Ollama)
        return self._smart_synthesizer_fallback(prompt)

    def _smart_synthesizer_fallback(self, prompt: str) -> str:
        """
        Bộ tổng hợp dự phòng: Trích xuất thông tin trọng tâm từ context đã lấy được qua RAG.
        Đảm bảo trải nghiệm luôn mượt mà kể cả khi user chưa khởi động Ollama.
        """
        import re
        # Tách context ra từ prompt nếu có
        context_part = ""
        question_part = ""
        if "NGỮ CẢNH CỬA HÀNG:" in prompt and "CÂU HỎI CỦA KHÁCH HÀNG:" in prompt:
            try:
                context_part = prompt.split("NGỮ CẢNH CỬA HÀNG:")[1].split("CÂU HỎI CỦA KHÁCH HÀNG:")[0].strip()
                question_part = prompt.split("CÂU HỎI CỦA KHÁCH HÀNG:")[1].split("YÊU CẦU TRẢ LỜI:")[0].strip()
            except Exception:
                context_part = prompt

        if not context_part:
            return "Dạ chào bạn! Mình là Evern AI Stylist ✨ Bạn đang muốn tìm sản phẩm nào, tư vấn chọn size hay phối đồ cho dịp gì để mình hỗ trợ nhé? 😊"

        # Lọc các dòng thông tin quan trọng nhất từ RAG context, LOẠI BỎ tên file và ký tự markdown thô
        clean_lines = []
        for line in context_part.split("\n"):
            l = line.strip()
            if not l or l.startswith("---") or l.startswith("Dưới đây là"):
                continue
            # Loại bỏ dòng tên file như [bang_size.md], [cam_nang_phoi_do.md], [product_catalog]
            if re.match(r"^\[.*(?:\.md|\.txt|catalog)\]", l, re.IGNORECASE):
                continue
            # Loại bỏ dấu thăng tiêu đề #
            l = re.sub(r"^#+\s*", "", l)
            clean_lines.append(l)

        # Tạo câu trả lời tự nhiên, chuyên nghiệp
        intro = "Dạ Evern AI Stylist gửi bạn thông tin tư vấn từ cửa hàng nhé ✨\n\n"
        body = "\n".join(clean_lines[:10])  # Lấy nội dung chi tiết
        outro = "\n\n💡 Bạn có cần mình tư vấn thêm về chọn size, xem thêm hình ảnh hoặc đặt hàng mẫu nào không ạ?"
        
        return intro + body + outro

    def assist_stylist_response(
        self,
        user_message: str,
        intent: str,
        products: List[Dict[str, Any]],
        facts_summary: str = "",
        draft_reply: str = "",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Sử dụng Local LLM (Ollama) để tư vấn trang phục dựa trên sản phẩm thật từ SQLite."""
        # Chuẩn bị danh sách sản phẩm từ CSDL SQLite
        prod_lines = []
        for idx, p in enumerate(products[:4], 1):
            sizes_str = ", ".join(p.get("sizes", [])) if isinstance(p.get("sizes"), list) else str(p.get("sizes", ""))
            prod_lines.append(
                f"{idx}. {p['name']} (Mã: {p.get('code', 'N/A')}) - Giá: {p['price']:,}đ | Màu: {p.get('color', 'Nhiều màu')} | Size: {sizes_str}"
            )
        prod_facts = "\n".join(prod_lines) if prod_lines else "Không có danh sách sản phẩm cụ thể."

        guide_section = f"\nCẨM NANG PHỐI ĐỒ CHUYÊN SÂU TỪ SHOWROOM:\n{facts_summary}\n" if facts_summary else ""

        history_section = ""
        if chat_history:
            history_lines = []
            for turn in chat_history[-3:]:
                role = "Khách hàng" if turn.get("role") == "user" else "Evern Stylist"
                turn_text = turn.get("text", "").strip().split("\n")[0][:150]
                if turn_text:
                    history_lines.append(f"- {role}: {turn_text}")
            if history_lines:
                history_section = f"\nLỊCH SỬ HỘI THOẠI GẦN NHẤT:\n" + "\n".join(history_lines) + "\n"

        if len(products) > 1 and any(tag in intent.lower() for tag in ["outfit", "recommendation", "phối đồ", "gợi ý", "thời trang"]):
            task_instruction = (
                "2. BẮT BUỘC: Khách đang yêu cầu GỢI Ý PHỐI ĐỒ (OUTFIT) TRỌN BỘ. "
                "Bạn PHẢI gợi ý cách kết hợp hài hòa cả set đồ (gồm Áo + Quần + Giày/Khoác) từ các sản phẩm ở trên. "
                "Tuyệt đối KHÔNG chỉ tập trung vào 1 sản phẩm duy nhất và KHÔNG nói 'hướng dẫn bạn lựa chọn mẫu [1 mẫu]'."
            )
        else:
            task_instruction = (
                "2. Trực tiếp đưa ra tư vấn chi tiết cho sản phẩm thực tế ở trên (chất liệu, form dáng, giá bán, cách phối)."
            )

        draft_section = f"\nGỢI Ý DỰ THẢO CHUẨN TỪ SHOWROOM (BẠN CÓ THỂ THAM KHẢO PHONG CÁCH NÀY):\n{draft_reply}\n" if draft_reply else ""

        system_instruction = f"""Bạn là Evern AI Stylist - Chuyên viên tư vấn thời trang thông minh, thanh lịch của thương hiệu Evern.
QUY TẮC BẮT BUỘC:
1. Xưng 'mình' hoặc 'Evern' và gọi khách là 'bạn'. Tuyệt đối KHÔNG xưng 'tôi', KHÔNG chào 'chào mọi người' (đây là trò chuyện 1-1 với 1 khách hàng).
2. Trả lời trực tiếp, tự nhiên bằng tiếng Việt chuẩn. Tuyệt đối KHÔNG dùng các câu dịch máy ngớ ngẩn (như 'Có gợi ý nào không nào', 'chuẩn bài', 'look cực kì', 'quý khách của bạn').
{task_instruction}
3. Nếu khách hỏi 'mẫu này' hoặc đề cập sản phẩm ở câu trước, hãy trả lời đúng về sản phẩm đó, không hỏi vòng vo.
4. Mời khách chia sẻ thêm chiều cao, cân nặng để hỗ trợ tư vấn chọn size chuẩn xác nhất.
5. Tuyệt đối KHÔNG lặp lại các quy tắc hệ thống, KHÔNG in ra chữ 'YÊU CẦU TRẢ LỜI' hay các ký hiệu markdown kỹ thuật thô.
6. Luôn viết câu hoàn chỉnh có dấu chấm kết thúc, không bỏ dở câu."""

        user_prompt = f"""{history_section}
CÂU NÓI CỦA KHÁCH HÀNG: "{user_message}"
Ý ĐỊNH: {intent}
{guide_section}
DANH SÁCH SẢN PHẨM THỰC TẾ TỪ DATABASE SQLITE:
{prod_facts}
{draft_section}
Hãy viết lời tư vấn tự nhiên, hấp dẫn nhất gửi đến khách hàng:"""

        status = self.check_ollama_status()
        if status["running"]:
            try:
                # Nếu có model tự train evern-ai-stylist thì ưu tiên dùng
                models = status.get("models", [])
                active_model = self.model_name
                if any("evern-ai-stylist" in m for m in models):
                    active_model = "evern-ai-stylist"
                elif not any(self.model_name in m for m in models) and models:
                    active_model = models[0]

                payload = {
                    "model": active_model,
                    "system": system_instruction,
                    "prompt": user_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.35,
                        "top_p": 0.85,
                        "repeat_penalty": 1.15,
                        "num_ctx": 1024,
                        "num_predict": 260
                    }
                }
                res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    text = res.json().get("response", "").strip()
                    text = self.clean_llm_response(text)
                    if text and len(text) > 30 and not self.has_prompt_leakage(text):
                        return text
            except Exception as e:
                print(f"[LocalLLM] Error calling Ollama for stylist: {e}")

        # Fallback về ResponseGenerator nếu Ollama chưa bật hoặc lỗi
        return draft_reply

    def assist_knowledge_response(
        self,
        user_message: str,
        knowledge_context: str,
        draft_reply: str = ""
    ) -> str:
        """Sử dụng Local LLM (Ollama) để giải đáp chính sách, hướng dẫn size không bị lộ file .md."""
        system_instruction = (
            "Bạn là Evern AI Stylist. Hãy trả lời trực tiếp, thân thiện, ngắn gọn bằng tiếng Việt. "
            "Tóm tắt ý chính sách hoặc hướng dẫn size từ cửa hàng. "
            "Tuyệt đối KHÔNG sao chép câu lệnh chỉ dẫn hệ thống hay đề cập tên file kỹ thuật như [bang_size.md]."
        )
        user_prompt = f"""Khách hàng hỏi: "{user_message}"

Thông tin từ cẩm nang cửa hàng:
{knowledge_context}

Hãy viết câu trả lời tự nhiên gửi đến khách hàng:"""

        status = self.check_ollama_status()
        if status["running"]:
            try:
                models = status.get("models", [])
                active_model = self.model_name
                if any("evern-ai-stylist" in m for m in models):
                    active_model = "evern-ai-stylist"
                elif not any(self.model_name in m for m in models) and models:
                    active_model = models[0]

                payload = {
                    "model": active_model,
                    "system": system_instruction,
                    "prompt": user_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "repeat_penalty": 1.15,
                        "num_ctx": 1024,
                        "num_predict": 150
                    }
                }
                res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    text = res.json().get("response", "").strip()
                    text = self.clean_llm_response(text)
                    if text and len(text) > 20 and not self.has_prompt_leakage(text):
                        return text
            except Exception as e:
                print(f"[LocalLLM] Error calling Ollama for knowledge: {e}")

        return draft_reply

    @staticmethod
    def clean_llm_response(text: str) -> str:
        """Loại bỏ triệt để hiện tượng LLM lặp lại chỉ dẫn hệ thống hoặc tiêu đề quy tắc."""
        if not text:
            return ""
        import re
        # Xóa khối YÊU CẦU TRẢ LỜI / QUY TẮC nếu bị LLM in ra đầu câu
        text = re.sub(r"^(?:YÊU CẦU TRẢ LỜI|YÊU CẦU|QUY TẮC BẮT BUỘC|QUY TẮC)[\s\S]*?(?:Tuyệt đối KHÔNG[^\n]*\n|\d+\.[^\n]*\n\n?)", "", text, flags=re.IGNORECASE).strip()
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            l_lower = line.strip().lower()
            if any(l_lower.startswith(prefix) for prefix in [
                "yêu cầu trả lời:", "quy tắc bắt buộc:", "danh sách sản phẩm thực tế",
                "câu nói của khách hàng:", "câu hỏi của khách hàng:", "ý định:"
            ]):
                continue
            if re.match(r"^\d+\.\s*(?:xưng\s*['\"]mình['\"]|trực tiếp đưa ra tư vấn|nếu khách hỏi|mời khách chia sẻ|tuyệt đối không in ra)", l_lower):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def has_prompt_leakage(text: str) -> bool:
        """Kiểm tra xem câu trả lời có chứa dấu hiệu rò rỉ prompt hệ thống hay không."""
        if not text:
            return False
        leak_markers = [
            "yêu cầu trả lời", "quy tắc bắt buộc", "danh sách sản phẩm thực tế",
            "câu nói của khách hàng", "ý định:", "tuyệt đối không in ra",
            "xưng 'mình' hoặc 'evern'", "mời khách chia sẻ thêm chiều cao",
            "định hình phong cách thời trang của thương hiệu evern"
        ]
        t_lower = text.lower()
        return any(marker in t_lower for marker in leak_markers)

