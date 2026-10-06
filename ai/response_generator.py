import re
import random
from typing import Dict, Any, List, Optional

# Bộ tổng hợp câu trả lời bán hàng tự nhiên theo ngữ cảnh
class ResponseGenerator:
    OPENERS = {
        "find_product": [
            # Cơ bản / Phổ thông
            "Dạ Evern chào bạn nha! ✨ Mình đã tìm thấy các mẫu khá sát với nhu cầu của bạn đây ạ:",
            "Chào bạn nhé! 👋 Mình vừa lọc nhanh trong kho những sản phẩm phù hợp với yêu cầu của bạn:",
            "Dạ có ngay cho bạn đây ạ! Mình đã tìm những mẫu phù hợp nhất với tiêu chí bạn vừa đưa:",
            "Mình tìm được một số mẫu khá đúng gu bạn rồi nè. Bạn tham khảo thử nhé! ✨",
            "Dạ Evern đã lọc xong rồi ạ. Đây là những mẫu phù hợp nhất với yêu cầu của bạn:",
            # Khách hỏi ngắn / cụt
            "Dạ có ạ! Mình tìm được một số mẫu phù hợp cho bạn đây:",
            "Có nha bạn! Đây là những mẫu hiện đang phù hợp nhất:",
            "Dạ được ạ, mình tìm cho bạn ngay đây:",
            "Có ngay bạn nhé! Bạn xem thử những mẫu này ạ:",
            "Dạ mình tìm thấy rồi ạ. Bạn tham khảo thử nhé:",
            # Khách muốn mua nhanh
            "Dạ nếu bạn muốn chọn nhanh thì mình đã lọc sẵn một số mẫu đáng tham khảo nhất:",
            "Nếu muốn chốt nhanh thì bạn có thể xem qua những mẫu này trước nha:",
            "Mình đã rút gọn danh sách để bạn dễ chọn hơn rồi ạ:",
            # Khách hỏi nhiều tiêu chí
            "Dạ mình đã kết hợp các tiêu chí bạn đưa ra và lọc những sản phẩm phù hợp nhất rồi ạ:",
            "Bạn đưa khá nhiều tiêu chí nhưng mình đã lọc lại giúp bạn rồi nha 😎 Đây là những mẫu phù hợp nhất:",
            "Mình đã ưu tiên đồng thời kiểu dáng, màu sắc, mức giá và phong cách bạn yêu cầu. Bạn xem thử nhé:"
        ],

        "find_outfit": [
            # Khách hỏi để đi đâu đó / phối đồ
            "Dạ mình đã ưu tiên những mẫu phù hợp với dịp bạn sắp tham gia rồi ạ:",
            "Đi dịp này thì mình nghĩ các mẫu dưới đây khá dễ mặc và phù hợp đó ạ:",
            "Mình đã lọc những thiết kế phù hợp với hoàn cảnh bạn vừa nói. Bạn tham khảo thử nhé:",
            "Dạ có một số mẫu khá hợp cho dịp này nè. Mình gửi bạn xem thử:",
            "Dạ Evern Stylist xin gợi ý outfit cực kỳ tôn dáng và chuẩn không khí cho dịp này của bạn đây ạ: ✨",
            "Tuyệt vời luôn nè! Với dịp này, Evern gợi ý cho bạn set đồ vừa thanh lịch, vừa tự tin và nổi bật nhất nha: 💫",
            "Lên đồ dịp này thì phối theo cách này chuẩn bài luôn bạn ơi! Evern Stylist gợi ý cho bạn set đồ cực ưng ý này nhé: 🌟",
            "Chào bạn nhé! Để bạn thật tự tin và cuốn hút trong dịp này, mình đã phối sẵn những gợi ý trang phục cực chuẩn gu dưới đây nè:"
        ],

        "find_outfit_general": [
            "Dạ Evern Stylist xin gợi ý cho bạn set trang phục phối sẵn cực kỳ tôn dáng, trẻ trung và dễ mặc dưới đây nhé: ✨",
            "Chào bạn nha! Để bạn có một vẻ ngoài thật tự tin và cuốn hút, Evern Stylist đã chuẩn bị set đồ phối sẵn cực chuẩn gu dưới đây nè: 🌟",
            "Dạ đây là set đồ được Evern Stylist kết hợp rất ăn ý về cả màu sắc và phom dáng, bạn tham khảo thử nhé: 💫",
            "Chào bạn nhé! Evern Stylist xin gửi bạn những gợi ý trang phục cực kỳ thời thượng và dễ ứng dụng hàng ngày đây ạ: ✨"
        ],

        "find_outfit_summer": [
            "Chào bạn nha! ☀️ Mùa hè rực rỡ với cái nắng oi ả, tiêu chí hàng đầu là sự mát mẻ, thoáng khí và thấm hút mồ hôi tốt. Evern Stylist gợi ý ngay cho bạn những mẫu trang phục mùa hè cực mát và năng động dưới đây nè: ✨",
            "Dạ lên đồ mùa hè thì chất vải cotton organic, đũi mát hoặc polo dệt tổ ong là số 1 luôn ạ! 🌴 Evern gửi bạn những gợi ý trang phục mùa hè vừa giải nhiệt vừa cực phong cách đây:",
            "Mùa hè bung xõa năng động cùng Evern nha! 🌊 Dưới đây là những thiết kế mùa hè siêu thoáng mát, nhẹ nhàng và thoải mái cho bạn tham khảo nè:"
        ],

        "find_outfit_winter": [
            "Chào bạn nhé! ❄️ Mùa đông lạnh giá thì outfit vừa phải giữ ấm tuyệt đối, vừa phải thời thượng và tôn dáng. Evern Stylist gợi ý ngay cho bạn những mẫu đồ đông ấm áp và phong độ nhất dưới đây: 🧥",
            "Dạ đón gió đông se lạnh cực ấm và sang chảnh cùng Evern nha! 🧣 Đây là những thiết kế mùa đông chất liệu len, nỉ và áo khoác dày dặn giữ nhiệt cực tốt dành cho bạn nè: ✨",
            "Mùa đông đến rồi, lên đồ ấm áp và thời trang cùng Evern thôi! ❄️ Mời bạn tham khảo những item mùa đông ấm áp và chuẩn gu dưới đây nhé:"
        ],

        "find_outfit_fall": [
            "Chào bạn nha! 🍂 Tiết trời thu mát mẻ se lạnh là thời điểm lý tưởng nhất để diện phong cách layering nhẹ nhàng, lãng tử và thanh lịch. Evern Stylist gửi bạn những gợi ý trang phục mùa thu cực cuốn hút dưới đây nhé: 🍁",
            "Dạ mùa thu dịu mát cùng những gam màu be, nâu, xám ấm áp! 🍂 Evern Stylist gợi ý cho bạn những set đồ mùa thu vừa nhẹ nhàng vừa chỉn chu dưới đây nè: ✨",
            "Lên đồ đón thu cùng Evern nha! 🍁 Những thiết kế cardigan mỏng, sơ mi dài tay và áo khoác gió nhẹ dưới đây sẽ giúp bạn có diện mạo mùa thu thật thơ và phong cách:"
        ],

        "find_outfit_spring": [
            "Chào bạn nhé! 🌸 Mùa xuân ấm áp tươi vui là mùa của khởi đầu mới, du xuân và gặp gỡ. Evern Stylist gợi ý ngay cho bạn những trang phục mùa xuân nhẹ nhàng, tươi tắn và tràn đầy năng lượng dưới đây nè: 🌷",
            "Dạ đón sắc xuân tươi mới cùng những gam màu pastel trẻ trung, thanh lịch! 🌸 Evern gửi bạn những gợi ý trang phục mùa xuân cực kỳ tôn dáng và may mắn đầu năm nè: ✨",
            "Du xuân rạng rỡ và thanh lịch cùng Evern nha! 🌸 Dưới đây là những mẫu áo đũi linen, polo dệt kim và váy đầm mùa xuân nhẹ tênh cho bạn tham khảo nhé:"
        ],

        "find_outfit_four_seasons": [
            "Chào bạn nha! ✨ Để bạn luôn mặc đẹp và tự tin suốt cả 4 mùa Xuân - Hạ - Thu - Đông, Evern Stylist đã tổng hợp bộ sưu tập trang phục 4 mùa chuẩn gu và đa năng nhất dưới đây nè: 🌟",
            "Dạ phối đồ chuẩn gu cho cả 4 mùa trong năm là bí quyết để luôn phong độ và thời thượng! 🌸☀️🍂❄️ Evern Stylist xin gửi bạn cẩm nang và gợi ý trang phục tiêu biểu cho từng mùa dưới đây nhé: ✨"
        ],

        "find_by_price": [
            "Dạ mình đã ưu tiên các mẫu nằm trong khoảng ngân sách bạn đưa ra rồi ạ. Bạn xem thử nhé:",
            "Mình đã lọc theo mức giá bạn mong muốn rồi nha 💰 Đây là những lựa chọn phù hợp:",
            "Với ngân sách này, mình tìm được một số mẫu khá ổn áp cho bạn:",
            "Dạ mình đã ưu tiên những mẫu vừa túi tiền và phù hợp với nhu cầu của bạn:",
            "Dạ có ngay ạ! Trong tầm ngân sách này, Evern có những mẫu cực kỳ chất lượng và bền đẹp dành cho bạn đây:",
            "Chào bạn nhé! Với mức giá cực kỳ hợp lý mà bạn tìm, Evern gợi ý những sản phẩm 'ngon - bổ - xịn' nhất tại shop nè: ✨"
        ],

        "find_by_style": [
            # Gen Z / Trẻ trung
            "Có hàng rồi nè bạn ơi 😎 Mình vừa lọc mấy em khá đúng vibe bạn đang tìm:",
            "Đúng gu là phải có hàng chứ 😎 Đây là mấy mẫu mình thấy khá hợp với yêu cầu của bạn:",
            "Evern vừa soi kho một vòng 👀 và tìm được mấy mẫu khá ổn áp cho bạn đây:",
            "Có ngay nhaaa ✨ Mấy mẫu dưới đây khá đúng vibe bạn đang tìm đó:",
            "Gu này Evern bắt được rồi nha 😎 Mình lọc ra vài mẫu đáng xem nhất cho bạn:",
            "Không cần lướt cả kho đâu 😆 Mình lọc sẵn những mẫu phù hợp nhất cho bạn rồi:",
            "Vibe này thì có vài em khá hợp đó nha 🔥 Bạn nghía thử mấy mẫu dưới đây:",
            "Evern bắt đúng keyword rồi nè 👀 Đây là những mẫu gần với gu bạn nhất:",
            # Khách hỏi theo phong cách
            "Dạ mình đã lọc theo phong cách bạn yêu thích rồi ạ. Đây là những mẫu gần với vibe đó nhất:",
            "Style bạn chọn khá rõ rồi nè 😎 Mình tìm được một số mẫu đúng hướng này:",
            "Nếu bạn đang theo vibe này thì mấy mẫu dưới đây khá hợp đó ạ:",
            "Mình đã ưu tiên những thiết kế đúng phong cách bạn mô tả. Bạn xem thử nhé:"
        ],

        "find_by_color": [
            "Dạ mình đã lọc theo màu bạn yêu cầu rồi ạ. Đây là những mẫu hiện có:",
            "Có đúng tone bạn tìm nha 🎨 Mình tìm được những mẫu này:",
            "Mình đã ưu tiên đúng màu bạn thích rồi. Bạn xem thử các mẫu bên dưới nhé:",
            "Dạ tone màu này cực kỳ tôn da và dễ phối đồ luôn ạ! Evern gửi bạn các mẫu chuẩn sắc màu bạn cần nè: ✨",
            "Chào bạn nhé! Tone màu này diện lên vừa thanh lịch vừa sang mắt, Evern vừa lọc nhanh các mẫu sẵn hàng cho bạn đây: 🎨"
        ],

        "find_by_size": [
            "Dạ mình đã ưu tiên những mẫu có form và size phù hợp với nhu cầu của bạn:",
            "Mình đã lọc những mẫu phù hợp với dáng và size bạn đang tìm rồi ạ:",
            "Với yêu cầu về form dáng này, mình tìm được một số lựa chọn khá phù hợp:",
            "Dạ shop đã kiểm tra kho và lọc sẵn các mẫu chuẩn size của bạn, phom dáng cực kỳ tôn dáng và thoải mái cử động nè: 📏",
            "Chào bạn nha! Với size bạn cần, Evern đang sẵn những thiết kế lên phom cực chuẩn và vừa vặn dưới đây nè: ✨"
        ],

        "recommend_gift": [
            "Dạ mình đã lọc những mẫu phù hợp với người bạn muốn mua tặng rồi ạ:",
            "Nếu bạn đang tìm quà cho người thân thì đây là một số lựa chọn khá dễ chọn:",
            "Mình đã ưu tiên những mẫu dễ mặc và dễ phối để bạn mua tặng nhé:",
            "Dạ, với nhu cầu mua tặng, mình đã chọn ra một số mẫu khá an toàn và dễ sử dụng:",
            "Dạ chọn quà tại Evern là chuẩn bài luôn ạ! ✨ Để người nhận cảm thấy bất ngờ và hạnh phúc, mình xin gợi ý những món quà cực kỳ tinh tế và dễ mặc này nhé: 🎁",
            "Tuyệt vời quá nè! Tặng quà thời trang vừa thiết thực lại vừa thể hiện sự quan tâm chu đáo. Dưới đây là những mẫu được khách chọn làm quà nhiều nhất tại shop:"
        ],

        "formal_advice": [
            "Dạ, tôi đã tìm những mẫu phù hợp với yêu cầu của cô/chú. Cô/chú tham khảo các mẫu dưới đây ạ:",
            "Dạ, cửa hàng hiện có một số mẫu khá phù hợp với nhu cầu của cô/chú. Mời cô/chú xem thử ạ:",
            "Dạ, tôi đã lọc theo kiểu dáng và mức giá cô/chú mong muốn. Đây là một số lựa chọn phù hợp ạ:",
            "Dạ, những mẫu dưới đây khá phù hợp để mặc đi làm, đi gặp gỡ hoặc sử dụng hằng ngày ạ:",
            "Dạ, tôi đã tìm những mẫu có thiết kế đơn giản, lịch sự và dễ mặc cho cô/chú tham khảo ạ:",
            "Dạ với người lớn tuổi hoặc độ tuổi trung niên, tiêu chí hàng đầu là chất liệu mềm mát, nhẹ nhàng và phom dáng đứng đắn, lịch thiệp. Evern xin gợi ý những mẫu rất được ưa chuộng dưới đây ạ: 👔"
        ],

        "empty_product": [
            # Cơ bản
            "Dạ rất tiếc là hiện tại hệ thống chưa tìm thấy mẫu khớp hoàn toàn với yêu cầu của bạn ạ.",
            "Tiếc quá nè! Hiện tại trong kho shop chưa có mẫu đáp ứng đầy đủ các tiêu chí bạn vừa đưa ra.",
            "Dạ shop vừa kiểm tra kho nhưng hiện chưa có sản phẩm phù hợp hoàn toàn với mô tả của bạn ạ.",
            # Thân thiện / Gen Z
            "Ui, tiêu chí này hơi khó một xíu 😭 Hiện tại kho chưa có mẫu khớp hoàn toàn với yêu cầu của bạn.",
            "Mình vừa soi kho khá kỹ 👀 nhưng hiện chưa tìm được em nào khớp 100% với yêu cầu này.",
            "Gu này hơi khó tìm hàng một chút nha 😭 Hiện tại shop chưa có mẫu đúng hoàn toàn.",
            "Kho hiện tại chưa bắt được đúng vibe bạn muốn rồi 🥲 Nhưng mình có thể tìm những mẫu gần nhất cho bạn.",
            # Không có đúng mẫu
            "Dạ hiện tại shop chưa có mẫu đúng chính xác như mô tả của bạn. Tuy nhiên, có thể thử mở rộng sang một số kiểu dáng tương tự.",
            "Mẫu đúng với tất cả tiêu chí hiện chưa có trong kho ạ. Nếu bạn linh hoạt một tiêu chí như màu hoặc kiểu dáng, mình có thể tìm thêm.",
            "Hiện tại chưa có sản phẩm đáp ứng đầy đủ yêu cầu. Bạn có thể cân nhắc nới một chút về màu sắc, kiểu dáng hoặc ngân sách.",
            # Khuyến khích thử lại
            "Bạn thử cho mình thêm một tiêu chí khác như màu sắc, mức giá hoặc kiểu dáng nhé. Mình sẽ lọc lại cho sát hơn.",
            "Nếu bạn muốn, mình có thể nới một trong các tiêu chí như giá, màu hoặc kiểu dáng để tìm thêm sản phẩm phù hợp.",
            "Bạn có thể thay đổi một tiêu chí nhỏ thôi, mình sẽ thử tìm lại những mẫu gần nhất cho bạn."
        ],

        "empty_budget": [
            "Dạ hiện tại shop chưa có mẫu đúng yêu cầu trong mức ngân sách này ạ. Nếu tăng ngân sách một chút, mình có thể tìm thêm lựa chọn gần nhất.",
            "Mình chưa tìm thấy sản phẩm phù hợp trong khoảng giá bạn đưa ra. Bạn có muốn tham khảo các mẫu có mức giá gần nhất không?",
            "Dạ tiếc quá, hiện tại trong tầm ngân sách này showroom chưa có mẫu sẵn khớp với yêu cầu của bạn rồi ạ.",
            "Tiếc quá nè! Mức giá bạn tìm hiện kho shop chưa có sản phẩm sẵn tiệm cận rồi ạ."
        ],

        "empty_color": [
            "Dạ kiểu dáng bạn tìm hiện có nhưng màu bạn yêu cầu chưa có trong kho ạ.",
            "Mẫu tương tự hiện đang có, tuy nhiên shop chưa có đúng màu bạn muốn. Bạn có thể tham khảo một vài tone gần giống nhé.",
            "Dạ tiếc quá, tone màu này cho mẫu bạn tìm hiện shop chưa có sẵn trong kho đợt này rồi ạ.",
            "Dạ màu sắc này hiện showroom tạm chưa có sẵn hàng cho thiết kế bạn tìm nha."
        ],

        "empty_size": [
            "Dạ hiện tại mẫu phù hợp với yêu cầu của bạn chưa có size bạn cần ạ.",
            "Mẫu bạn đang tìm có thể chưa còn size phù hợp. Mình có thể giúp bạn tìm những mẫu khác có size tương ứng.",
            "Dạ rất tiếc, kích cỡ này của dòng sản phẩm bạn tìm hiện đang tạm thời hết hàng tại showroom rồi ạ.",
            "Tiếc quá nè! Size bạn yêu cầu hiện kho shop vừa hết mất rồi, bạn có muốn tham khảo bảng size chi tiết hoặc mẫu tương tự không ạ?"
        ],

        "empty_style": [
            "Dạ hiện tại kho chưa có mẫu đúng phong cách bạn mô tả. Mình có thể tìm những thiết kế có vibe gần nhất cho bạn.",
            "Phong cách này hiện shop chưa có nhiều mẫu đúng chuẩn, nhưng vẫn có một số lựa chọn tương tự để bạn tham khảo.",
            "Dạ rất tiếc, thiết kế theo phong cách này hiện bộ sưu tập đợt này của shop chưa có mẫu sẵn hoàn toàn tương thích rồi ạ."
        ],

        "empty_formal": [
            "Dạ, hiện tại cửa hàng chưa có mẫu đúng hoàn toàn với yêu cầu của cô/chú ạ. Tôi có thể tìm những mẫu gần nhất để cô/chú tham khảo.",
            "Dạ, mẫu theo đúng tiêu chí này hiện chưa có trong kho ạ. Nếu cô/chú linh hoạt về màu sắc hoặc kiểu dáng, tôi có thể tìm thêm.",
            "Dạ rất tiếc, hiện tại cửa hàng chưa có sản phẩm phù hợp hoàn toàn. Cô/chú có thể cho tôi biết tiêu chí nào có thể thay đổi để tôi tìm lại ạ?"
        ],

        "empty_gift": [
            "Dạ hiện tại chưa tìm thấy mẫu đáp ứng đầy đủ yêu cầu để làm quà tặng. Mình có thể tìm những mẫu dễ mặc và dễ chọn hơn nhé.",
            "Mẫu đúng tiêu chí hiện chưa có ạ. Nếu bạn mua tặng, mình có thể ưu tiên những thiết kế dễ mặc và ít kén người dùng hơn."
        ],

        "ask_clarification": [
            "Dạ Evern AI Stylist rất sẵn lòng hỗ trợ bạn nè! ✨ Để mình lên outfit thật chuẩn gu và vừa vặn nhất, bạn chia sẻ thêm giúp mình một vài thông tin nhé:\n• Bạn đang tìm đồ cho **nam hay nữ** ạ?\n• Bạn dự định mặc đi đâu (**đi làm, đi chơi, hẹn hò hay dự tiệc**)?\n• Bạn có yêu thích màu sắc hay mức ngân sách nào không nè? ❤️",
            "Chào bạn nha! Evern có rất nhiều mẫu thời trang thiết kế đa dạng. Để chọn được trang phục đúng ý bạn nhất, bạn cho mình biết thêm:\n• Bạn muốn tìm dòng sản phẩm nào (**áo sơ mi, polo, thun, quần hay váy/đầm**) nè?\n• Dịp mặc và phong cách bạn hướng tới là gì ạ? ✨",
            "Dạ Evern Stylist sẵn sàng lên đồ cùng bạn đây ạ! Bạn có thể bật mí thêm bạn đang tìm trang phục cho dịp nào và gu ăn mặc bạn thích (trẻ trung, cá tính hay thanh lịch) không nè? 😊"
        ]
    }

    # Bí danh tiện lợi (Aliases) tương thích ngược và truy xuất trực tiếp
    OPENERS_FIND = OPENERS["find_product"]
    OPENERS_OUTFIT = OPENERS["find_outfit"]
    OPENERS_BUDGET = OPENERS["find_by_price"]
    OPENERS_STYLE = OPENERS["find_by_style"]
    OPENERS_COLOR = OPENERS["find_by_color"]
    OPENERS_SIZE = OPENERS["find_by_size"]
    OPENERS_GIFT = OPENERS["recommend_gift"]
    OPENERS_FORMAL = OPENERS["formal_advice"]
    OPENERS_EMPTY = OPENERS["empty_product"]
    OPENERS_CLARIFY = OPENERS["ask_clarification"]

    STYLING_TIPS_MALE = {
        "đi hẹn hò": "Với nam đi hẹn hò, set đồ ghi điểm tuyệt đối là áo sơ mi trơn hoặc polo dệt kim kết hợp cùng quần âu/chinos vừa vặn, đi kèm sneaker da trắng tối giản hoặc giày loafer để tạo cảm giác nam tính, gọn gàng và đáng tin cậy.",
        "hẹn hò": "Hẹn hò nam nên ưu tiên outfit chỉn chu nhưng gần gũi: áo sơ mi hoặc polo dệt kim phối cùng quần tây âu/chinos, có thể khoác nhẹ cardigan hoặc bomber khi trời mát.",
        "buổi hẹn đầu": "Buổi hẹn hò đầu tiên, bạn nam nên chọn outfit mang lại cảm giác sạch sẽ, nam tính và đáng tin cậy: áo polo có cổ phối quần chinos màu be hoặc âu xám, nước hoa nhẹ nhàng và đôi giày sạch tinh tươm.",
        "trưởng thành": "Phong cách trưởng thành, chững chạc cho nam nên ưu tiên áo polo có cổ hoặc sơ mi đơn sắc (trắng, xanh navy, be), phối cùng quần âu/chinos đứng phom và giày da hoặc loafer tối giản.",
        "thanh lịch": "Phong cách thanh lịch cho phái mạnh có thể bắt đầu với sơ mi hoặc polo dệt kim phối cùng quần tây âu, thắt lưng da và giày loafer hoặc sneaker tối giản.",
        "công sở": "Outfit công sở nam chuẩn mực gồm sơ mi hoặc polo phối cùng quần âu đứng phom, thắt lưng da và giày tây/loafer chỉn chu.",
        "đi làm": "Đi làm có thể chọn sơ mi hoặc polo kết hợp quần tây, jean tối màu và giày loafer hoặc sneaker tối giản.",
        "phỏng vấn": "Đi phỏng vấn, nam giới nên chọn sơ mi dài tay phối quần tây đen/xám than và giày tây sạch sẽ để toát lên vẻ nghiêm túc, chuyên nghiệp.",
        "đi phỏng vấn": "Đi phỏng vấn, nam giới nên ưu tiên sơ mi dài tay sạch sẽ, quần âu tối màu và giày tây hoặc giày da tối giản để tạo ấn tượng tin cậy.",
        "đám cưới": "Đi đám cưới, nam giới có thể chọn sơ mi trắng/xanh nhạt sơ vin cùng quần tây âu, đi giày da hoặc loafer để vừa lịch lãm vừa chỉn chu.",
        "tiệc sinh nhật": "Với tiệc sinh nhật, bạn nam có thể phối sơ mi hoặc polo cùng quần tây, jeans ống đứng hoặc áo khoác bomber/cardigan để tạo outfit vừa trẻ trung vừa phong độ.",
        "casual": "Phong cách casual nam rất dễ ứng dụng với áo thun basic, sơ mi khoác ngoài hoặc polo kết hợp quần jean, kaki và sneaker.",
        "smart casual": "Smart-casual cho nam có thể kết hợp polo dệt kim hoặc sơ mi với quần âu/chinos, giày loafer hoặc sneaker da tối giản.",
        "đi chơi": "Đi chơi bạn nam có thể chọn áo thun, polo hoặc sơ mi oversize kết hợp jean, cargo hoặc quần short.",
        "đi cafe": "Nam đi cafe sống ảo có thể chọn áo sơ mi cộc tay họa tiết tối giản hoặc sơ mi flannel khoác ngoài áo thun trắng, phối quần jeans suông và sneaker vintage để có những góc ảnh cực nghệ.",
        "đi du lịch": "Du lịch phái mạnh nên chọn các item thoáng mát, ít nhăn như áo thun cotton, áo sơ mi linen ngắn tay, quần short khaki hoặc quần túi hộp cargo kết hợp mũ lưỡi trai và sandal/sneaker thể thao.",
        "đi biển": "Đi biển bạn nam nên ưu tiên áo sơ mi cộc tay họa tiết hawaii hoặc sơ mi linen phanh cúc ngực, kết hợp quần short bơi hoặc short đũi sáng màu, đi dép quai ngang hoặc sandal da trẻ trung.",
        "clean fit": "Phong cách clean fit cho nam tôn vinh sự tối giản, sạch sẽ: áo phông trơn chất dày dặn kết hợp quần âu ống đứng vừa vặn qua mắt cá chân và sneaker trắng đế bằng tinh tế.",
        "boy phố": "Phong cách boy phố trẻ trung cá tính: áo polo zip hoặc sơ mi cổ mở phối cùng quần jeans ống đứng wash rách nhẹ hoặc quần âu cạp cao, đi giày bệt da bóng và phụ kiện thắt lưng da sang chảnh.",
        "doanh nhân": "Phong cách quý ông doanh nhân: bộ suit may đo cao cấp hoặc blazer màu navy phối sơ mi trắng cổ đức, quần âu đứng phom xếp ly, thắt lưng da thật và giày oxford/derby da bóng sang trọng.",
        "bad boy": "Phong cách bad boy cool ngầu: áo khoác da biker đen hoặc jacket jeans wash đậm phối cùng áo thun đen bó vừa vặn, quần jeans rách gối hoặc cargo và đôi boots chelsea/sneaker cổ cao hầm hố.",
        "hàn quốc": "Phong cách nam hàn quốc lãng tử: áo len dệt kim mỏng cổ tròn hoặc cardigan phối sơ mi trắng bên trong, quần tây ống rộng thả suông và giày loafer hoặc sneaker da retro.",
        "vintage": "Phong cách vintage retro cho nam: áo khoác denim wash bạc hoặc sơ mi caro flannel, quần jeans ống suông màu retro kết hợp thắt lưng da bản to và giày da cổ điển.",
        "người gầy": "Bạn nam dáng người gầy nên áp dụng quy tắc layering: mặc áo thun trắng bên trong khoác sơ mi hoặc jacket bên ngoài, ưu tiên trang phục màu sáng và quần ống đứng để thân hình trông đầy đặn, vạm vỡ hơn.",
        "người thấp": "Bạn nam có chiều cao khiêm tốn nên ưu tiên quần cạp cao ống đứng vừa vặn, sơ vin áo gọn gàng để tạo hiệu ứng 'kéo dài đôi chân', tránh mặc áo quá dài che qua mông.",
        "người mập": "Bạn nam đậm người nên ưu tiên trang phục phom suông đứng (regular fit), chọn tone màu tối như đen, xanh navy, xám than và tránh họa tiết to bản để tạo vóc dáng thon gọn, thanh thoát.",
        "mùa xuân": "Mùa xuân tiết trời ấm áp, bạn nam nên chọn áo sơ mi cổ tàu đũi linen hoặc áo polo dệt kim cổ đức viền sọc, phối cùng quần khaki chino kem be và sneaker năng động để có vẻ ngoài lãng tử, tươi mới du xuân.",
        "du xuân": "Du xuân chúc Tết đầu năm, bạn nam hãy diện áo sơ mi dài tay phối cùng quần âu/khaki đứng phom, khoác nhẹ vest/suit hoặc cardigan mỏng để vừa lịch lãm, phong độ lại đón trọn may mắn.",
        "mùa hè": "Mùa hè phái mạnh nên ưu tiên chất liệu cotton organic hoặc polo Nano dệt tổ ong thấm hút mồ hôi siêu tốc: combo áo thun/polo cùng quần short kaki ngang gối hoặc jeans mỏng nhẹ và sneaker phối lưới sẽ giúp bạn luôn mát mẻ và năng động suốt ngày dài.",
        "mùa thu": "Tiết trời thu mát mẻ se lạnh là mùa vàng của phong cách smart-casual: bạn nam hãy diện áo sơ mi dài tay Bamboo/Nano hoặc thun dài tay Dorian, khoác ngoài cardigan len mỏng, áo khoác gió trượt nước hoặc áo khoác bomber, kết hợp quần âu slimfit và giày derby/oxford chỉn chu.",
        "mùa đông": "Mùa đông rét buốt, bạn nam nên phối layer thông minh: mặc áo len mỏng cổ lọ hoặc áo thun giữ nhiệt bên trong, khoác ngoài áo khoác măng tô dáng dài, áo khoác chần bông siêu nhẹ hoặc áo khoác jeans lót bông/chỉ nổi, phối cùng quần jogger nỉ Jerry ấm áp hoặc quần jeans dày dặn và boots/sneaker da thật.",
        "4 mùa": "Bí quyết mặc đẹp 4 mùa cho phái mạnh: Xuân tươi mới với sơ mi cổ tàu & polo pastel; Hè mát mẻ cùng thun cotton & short khaki; Thu lịch lãm với sơ mi layer cardigan & quần âu; Đông ấm áp phong độ cùng áo len cổ lọ, măng tô & jogger nỉ.",
        "bốn mùa": "Bí quyết mặc đẹp 4 mùa cho phái mạnh: Xuân tươi mới với sơ mi cổ tàu & polo pastel; Hè mát mẻ cùng thun cotton & short khaki; Thu lịch lãm với sơ mi layer cardigan & quần âu; Đông ấm áp phong độ cùng áo len cổ lọ, măng tô & jogger nỉ.",
        "đi bar pub": "Đi bar hoặc pub chill cùng bạn bè, bạn nam có thể diện áo khoác da biker hoặc sơ mi đen lụa phanh cúc phối quần jeans tối màu và sneaker đen để tạo vẻ ngoài bí ẩn, cuốn hút.",
        "đi dạo phố": "Dạo phố cuối tuần, hãy chọn phong cách thoải mái nhất với áo thun oversize họa tiết graphic nhỏ, quần jogger nỉ thể thao hoặc quần short và một đôi sneaker thật êm chân.",
        "tối giản": "Phong cách minimal nam chỉ cần 2-3 gam màu cơ bản (trắng, đen, be, xám): áo thun trắng basic phối quần âu xám suông và sneaker trắng là đã có ngay outfit sang xịn mịn không bao giờ lỗi mốt.",
        "concert": "Đi concert quẩy hết mình thì ưu tiên số 1 là năng động và thoải mái: bạn nam hãy diện áo thun phông oversize graphic kết hợp cùng quần jeans ống suông hoặc jogger nỉ thể thao, khoác thêm áo khoác jeans/biker da và đôi sneaker êm chân để tha hồ bung xõa suốt đêm diễn nhé! 🔥",
        "đi concert": "Đi concert quẩy hết mình thì ưu tiên số 1 là năng động và thoải mái: bạn nam hãy diện áo thun phông oversize graphic kết hợp cùng quần jeans ống suông hoặc jogger nỉ thể thao, khoác thêm áo khoác jeans/biker da và đôi sneaker êm chân để tha hồ bung xõa suốt đêm diễn nhé! 🔥",
        "sơn tùng": "Đi concert của Sếp Sơn Tùng M-TP thì phong cách streetwear cá tính là chuẩn bài nhất: áo thun oversize phối layer cùng áo khoác biker/jeans, quần jeans ống suông và sneaker thể thao sẽ giúp bạn vừa 'cháy' vừa siêu thoải mái để quẩy cùng các bản hit! 🔥",
    }

    STYLING_TIPS_FEMALE = {
        "đi hẹn hò": "Với bạn nữ đi hẹn hò, outfit lý tưởng là đầm hoa nhí nhẹ nhàng hoặc áo dệt kim/sơ mi lụa phối cùng chân váy chữ A, kết hợp phụ kiện nhỏ xinh để toát lên vẻ duyên dáng, ngọt ngào.",
        "hẹn hò": "Hẹn hò nàng có thể chọn đầm midi thiết kế đơn giản, hoặc phối sơ mi lụa cùng chân váy vừa vặn và phụ kiện tối giản thanh lịch.",
        "buổi hẹn đầu": "Buổi hẹn hò đầu tiên, một chiếc đầm xòe midi nhẹ nhàng tone màu pastel hoặc áo dệt kim mềm ôm nhẹ phối chân váy chữ A sẽ giúp nàng toát lên vẻ dịu dàng, nữ tính và ghi điểm tuyệt đối.",
        "trưởng thành": "Phong cách trưởng thành, thanh lịch cho nữ có thể phối áo sơ mi lụa hoặc đầm suông trang nhã cùng blazer chiết eo, giày cao gót hoặc loafer mũi nhọn.",
        "thanh lịch": "Phong cách thanh lịch cho phái đẹp có thể bắt đầu với sơ mi lụa, áo dệt kim hoặc blazer phối cùng quần tây cạp cao hoặc chân váy midi.",
        "công sở": "Outfit công sở nữ có thể phối sơ mi hoặc áo kiểu với chân váy chữ A, quần tây xếp ly hoặc blazer tone trung tính.",
        "đi làm": "Đi làm có thể chọn sơ mi lụa hoặc polo nữ kết hợp quần tây cạp cao hoặc chân váy midi và giày bít mũi thanh lịch.",
        "phỏng vấn": "Đi phỏng vấn, bạn nữ nên chọn sơ mi kín đáo phối cùng chân váy midi qua gối hoặc quần tây cạp cao, đi giày cao gót 3-5cm hoặc búp bê lịch sự.",
        "đi phỏng vấn": "Ưu tiên trang phục sạch sẽ, vừa vặn và kín đáo. Sơ mi kết hợp quần tây hoặc chân váy dài qua gối là lựa chọn an toàn, chuyên nghiệp.",
        "đám cưới": "Đi đám cưới, phái đẹp có thể ưu tiên đầm midi, đầm ren hoặc đầm lụa với tone màu pastel, be hoặc xanh nhạt thanh lịch.",
        "tiệc sinh nhật": "Với tiệc sinh nhật, nàng có thể diện đầm xòe nhẹ nhàng hoặc sơ mi cách điệu phối cùng chân váy xếp ly và phụ kiện lấp lánh.",
        "dự tiệc": "Dự tiệc tối sang trọng, nàng nên chọn đầm lụa satin ôm dáng hoặc đầm xòe trễ vai phối giày cao gót mũi nhọn và ví cầm tay clutch lấp lánh để luôn tỏa sáng.",
        "dạ hội prom": "Tiệc prom tốt nghiệp hoặc dạ hội tối, nàng nên chọn đầm body đuôi cá xẻ tà quyến rũ hoặc đầm xòe công chúa trễ vai đính kim tuyến lấp lánh, đi giày cao gót quai mảnh để trở thành tâm điểm của đêm tiệc.",
        "đi cafe": "Nàng đi cafe check-in sống ảo nên chọn đầm hoa nhí tay bồng nhẹ nhàng hoặc áo croptop phối chân váy chữ A cạp cao, thêm một chiếc túi xách kẹp nách nhỏ xinh là lên hình lung linh ngay.",
        "đi du lịch": "Du lịch nàng hãy chuẩn bị những set đầm maxi thướt tha cho biển, hoặc áo thun oversize phối quần short/quần ống rộng và nón cói để vừa thoải mái di chuyển vừa có cả album ảnh đẹp.",
        "đi biển": "Đi biển nàng cứ tự tin bung xõa với váy maxi hoa hở lưng, đầm lụa 2 dây mềm mại hoặc set áo croptop phối chân váy xòe bồng bềnh, kết hợp kính râm và mũ cói rộng vành chuẩn nàng thơ mùa hè.",
        "tiểu thư": "Phong cách tiểu thư sang chảnh rất hợp với set áo dạ tweed phối chân váy xếp ly ngắn, đầm voan bèo nhún phối cùng giày búp bê mũi nhọn hoặc mary jane và kẹp tóc ngọc trai thanh nhã.",
        "bánh bèo": "Phong cách bánh bèo dễ thương ngọt ngào: nàng có thể chọn đầm babydoll xòe tone màu pastel (hồng phấn, vàng bơ, kem be), đi cùng giày búp bê hoặc sandal quai mảnh nữ tính.",
        "cá tính": "Phong cách cá tính, chất ngầu: áo croptop ôm sát hoặc áo corset phối cùng quần jeans ống rộng rách gối, khoác ngoài blazer da hoặc bomber thể thao và đi sneaker đế bánh mì hầm hố.",
        "y2k": "Phong cách Y2K nổi loạn và trẻ trung: áo thun baby tee ôm sát hoặc áo 2 dây phối chân váy cạp trễ, quần túi hộp ống thụng và phụ kiện kính râm mắt nhỏ, kẹp tóc cánh bướm rực rỡ.",
        "douyin": "Style Douyin triệu view cho nàng: áo thun form rộng giấu quần hoặc sơ mi cách điệu phối chân váy xếp ly tennis, mang tất cổ cao qua bắp chân cùng giày sneaker đế dày siêu hack dáng.",
        "vintage": "Phong cách vintage cổ điển hoài niệm: đầm chấm bi cổ sen, áo sơ mi tay bồng phối chân váy midi hoa nhí hoặc quần tây ống loe cạp cao tone nâu be ấm áp.",
        "minimal": "Phong cách minimal thanh lịch: đầm suông trơn màu trung tính (đen, trắng, be) hoặc áo sơ mi lụa phối quần tây cạp cao ống đứng, giày loafer tối giản tôn lên thần thái sang trọng tự nhiên.",
        "dáng người quả lê": "Nàng có dáng người quả lê (hông và đùi to hơn vai): nên tạo điểm nhấn ở phần thân trên với áo tay bồng, cổ vuông hoặc bèo nhún, kết hợp chân váy chữ A hoặc quần ống suông tối màu để che khuyết điểm hông đùi hoàn hảo.",
        "dáng người gầy": "Nàng dáng người mảnh mai nên chọn váy đầm nhiều tầng bồng bềnh, áo có họa tiết hoa nhí hoặc kẻ sọc ngang, phối layer cùng cardigan hoặc blazer để cơ thể trông đầy đặn và tràn đầy sức sống.",
        "dáng người tròn": "Nàng có vóc dáng mũm mĩm nên ưu tiên đầm chiết eo chữ V hoặc cổ vuông, phom dáng suông nhẹ chữ A và tone màu tối/trung tính để tạo cảm giác thon thả, thanh thoát.",
        "mùa xuân": "Mùa xuân ấm áp ngọt ngào, nàng hãy ưu tiên những mẫu đầm hoa nhí voan tơ bồng bềnh, áo sơ mi lụa tơ tằm pastel hoặc set chân váy xòe phối áo dệt kim mỏng để vừa dịu dàng, nữ tính vừa rạng rỡ du xuân.",
        "du xuân": "Du xuân chúc Tết hay chụp ảnh xuân, nàng hãy diện đầm ren pastel thanh lịch, đầm lụa mềm thướt tha hoặc set áo dạ tweed cách điệu phối chân váy xếp ly để vừa sang chảnh vừa đón trọn may mắn đầu năm.",
        "mùa hè": "Mùa hè nàng nên chọn chất liệu lụa satin, voan tơ hoặc cotton organic thoáng mát: các thiết kế đầm 2 dây mát mẻ hoặc áo croptop phối quần short sẽ giúp bạn luôn tự tin, dễ chịu.",
        "mùa thu": "Mùa thu se lạnh dịu dàng, nàng có thể diện áo cardigan len dệt kim mỏng phối chân váy chữ A, áo thun dài tay hoặc sơ mi lụa khoác blazer nhẹ tone be nâu ấm áp, kết hợp giày búp bê hoặc mary jane cổ điển.",
        "mùa đông": "Mùa đông nàng có thể diện áo len cổ lọ phối chân váy dạ midi và áo khoác dạ dáng dài măng tô, đi cùng boots đùi da hoặc boots cổ thấp vừa ấm áp vừa sang chảnh như sao Hàn.",
        "4 mùa": "Bí quyết mặc đẹp 4 mùa cho phái đẹp: Xuân rạng rỡ với đầm ren & sơ mi lụa pastel; Hè tươi trẻ cùng áo croptop, hai dây & short lụa; Thu dịu dàng với cardigan len & blazer tone be; Đông sang chảnh ấm áp cùng măng tô dạ, len cổ lọ & boots cao cổ.",
        "bốn mùa": "Bí quyết mặc đẹp 4 mùa cho phái đẹp: Xuân rạng rỡ với đầm ren & sơ mi lụa pastel; Hè tươi trẻ cùng áo croptop, hai dây & short lụa; Thu dịu dàng với cardigan len & blazer tone be; Đông sang chảnh ấm áp cùng măng tô dạ, len cổ lọ & boots cao cổ.",
        "đi bar pub": "Đi bar pub chill đêm, nàng có thể diện áo croptop cúp ngực phối chân váy da bóng ngắn, khoác hờ blazer đen bên ngoài và mang boots cao gót để vừa quyến rũ vừa sành điệu, sang chảnh.",
        "năng động": "Phong cách năng động hàng ngày: áo thun unisex form rộng phối quần short biker hoặc quần jeans suông, mũ lưỡi trai và sneaker thể thao giúp nàng tha hồ vận động cả ngày dài.",
        "concert": "Đi concert của Sơn Tùng M-TP nàng cứ tự tin bung xõa với phong cách Y2K hoặc Streetwear cá tính: áo croptop hoặc áo thun oversize phối chân váy xếp ly/quần loe cạp cao, khoác thêm jacket denim/bomber và đôi sneaker đế êm để vừa quẩy tưng bừng vừa hack dáng cực đỉnh nhé! 🔥",
        "đi concert": "Đi concert của Sơn Tùng M-TP nàng cứ tự tin bung xõa với phong cách Y2K hoặc Streetwear cá tính: áo croptop hoặc áo thun oversize phối chân váy xếp ly/quần loe cạp cao, khoác thêm jacket denim/bomber và đôi sneaker đế êm để vừa quẩy tưng bừng vừa hack dáng cực đỉnh nhé! 🔥",
        "sơn tùng": "Đi concert của Sơn Tùng M-TP nàng cứ tự tin diện phong cách Y2K hoặc Streetwear cá tính: áo croptop hoặc áo thun oversize phối chân váy xếp ly/quần loe cạp cao, khoác thêm jacket denim/bomber và đôi sneaker đế êm để vừa quẩy tưng bừng vừa hack dáng cực đỉnh nhé! 🔥",
    }

    STYLING_TIPS = {
        "áo sơ mi": "Mẫu sơ mi này cực kỳ dễ phối cùng quần âu thanh lịch hoặc quần jean tối màu, diện đi làm hay gặp đối tác đều rất sáng phom dáng nha!",
        "áo polo": "Áo polo có thể phối cùng quần short kaki dạo phố năng động hoặc quần tây ống đứng cho phong cách smart-casual hiện đại.",
        "áo thun": "Áo thun basic rất dễ mix & match với quần jean ống suông, chân váy hoặc khoác thêm blazer bên ngoài là có ngay outfit trẻ trung.",
        "quần jean": "Dáng quần này có thể phối cùng sneaker trắng và áo thun basic, hoặc kết hợp áo sơ mi oversize để tạo outfit trẻ trung, thoải mái.",
        "quần tây": "Quần tây phom đứng có thể sơ vin cùng áo sơ mi hoặc polo để tạo vẻ ngoài lịch sự, chỉn chu.",
        "áo khoác": "Áo khoác có thể kết hợp với áo thun, sơ mi hoặc hoodie bên trong tùy phong cách. Phối cùng quần jean hoặc quần ống rộng sẽ tạo outfit cân đối.",
        "váy & đầm": "Đầm có thể phối cùng giày cao gót, giày búp bê hoặc sneaker tùy hoàn cảnh. Thêm túi xách nhỏ sẽ giúp tổng thể hoàn thiện hơn.",
        "váy ngủ": "Chất liệu lụa satin cao cấp tạo cảm giác mềm mịn nhẹ tênh trên làn da, phom dáng rủ tự nhiên tôn lên vẻ đẹp quyến rũ và thoải mái tối đa khi ở nhà.",
        "áo polo dệt kim": "Áo polo dệt kim mang lại vibe cổ điển, lịch lãm và cực kỳ tôn dáng. Phối cùng quần âu suông hoặc quần chinos và giày loafer là chuẩn quý ông hiện đại.",
        "áo khoác dù": "Áo khoác gió/áo khoác dù vừa chống nước cản gió tốt vừa mang phong cách thể thao năng động. Phối cùng áo thun, quần jogger và sneaker là combo dạo phố cực chất.",
        "quần cargo": "Quần túi hộp cargo mang đậm hơi thở streetwear cá tính. Hãy phối cùng áo thun oversize hoặc croptop, kết hợp sneaker đế dày để tổng thể trông cực ngầu và khỏe khoắn.",
        "quần jogger": "Quần jogger bo gấu mang lại sự thoải mái tối đa cho ngày năng động. Rất hợp mix cùng hoodie, áo thun phông rộng hoặc áo nỉ sweater và sneaker thể thao.",
        "quần ống loe": "Quần ống loe là 'vũ khí hack chân dài' đỉnh cao. Bạn có thể phối cùng áo croptop, áo ôm body hoặc sơ mi sơ vin gọn gàng, đi kèm giày cao gót hoặc sneaker đế bánh mì.",
        "áo len cổ lọ": "Áo len cổ lọ là item kinh điển cho mùa lạnh. Mặc đơn lẻ hoặc layer bên trong áo blazer, măng tô dạ hay áo khoác da đều mang lại vẻ ngoài cực kỳ sang trọng và ấm áp.",
        "áo gile": "Áo gile len hoặc gile phao rất thích hợp để phối layer. Mặc bên ngoài áo sơ mi trắng hoặc áo thun dài tay sẽ tạo nên set đồ học đường trẻ trung, chuẩn phong cách Hàn Quốc.",
        "áo măng tô": "Áo khoác dáng dài măng tô dạ toát lên thần thái sang trọng, quý phái. Chỉ cần khoác ngoài set đồ basic và đi boots cổ thấp là bạn đã có diện mạo thời thượng như fashionista.",
        "áo dạ tweed": "Chất liệu dạ tweed mang đậm phong cách tiểu thư đài các, sang chảnh. Set áo dạ tweed phối cùng chân váy chữ A hoặc quần âu cạp cao rất thích hợp cho các buổi tiệc hay gặp mặt sang trọng.",
        "áo croptop ôm": "Áo croptop ôm sát giúp khoe trọn vòng eo thon gọn. Phối ăn ý nhất với quần ống rộng cạp cao hoặc chân váy xòe để tạo hiệu ứng tỷ lệ cơ thể chuẩn đồng hồ cát.",
        "chân váy tennis": "Chân váy xếp ly tennis mang lại nét đẹp tươi trẻ, ngọt ngào. Rất hợp mix cùng áo thun baby tee, áo polo hoặc sweater rộng và tất cổ cao phong cách Y2K.",
        "quần chinos": "Quần chinos là lựa chọn hoàn hảo thay thế quần tây cứng nhắc. Phối cùng áo polo, sơ mi xắn tay hoặc áo thun trơn mang lại vẻ ngoài smart-casual vừa lịch lãm vừa trẻ trung.",
        "áo ba lỗ": "Áo tank top/ba lỗ năng động rất hợp cho mùa hè hay tập gym. Có thể mặc riêng cùng quần short, hoặc mặc trong khoác ngoài sơ mi phanh cúc cực phóng khoáng.",
        "quần short đũi": "Quần short chất đũi/linen nhẹ tênh, thoáng mát là bạn đồng hành lý tưởng khi đi biển hay dạo phố. Phối cùng áo phông trơn hoặc sơ mi cộc tay họa tiết để có outfit đậm chất mùa hè.",
        "vải tuyết mưa": "Vải tuyết mưa có độ rủ nhẹ, co giãn tốt, không bám bụi và giữ phom đứng rất đẹp. Cực kỳ thích hợp cho các mẫu quần âu, chân váy công sở hay đầm suông thanh lịch.",
        "vải nỉ bông": "Chất nỉ bông dày dặn, giữ ấm vượt trội và mềm mại với làn da. Rất phù hợp cho các thiết kế hoodie, sweater hay quần jogger trong những ngày trời trở lạnh.",
        "vải satin": "Vải lụa satin có độ bóng nhẹ tự nhiên và rủ mềm quyến rũ. Các thiết kế đầm tiệc, sơ mi lụa satin luôn mang lại cảm giác kiêu sa, sang trọng và nổi bật dưới ánh đèn.",
        "vải dạ": "Vải dạ ép cao cấp đứng phom, chắn gió ấm áp và không bao giờ lỗi mốt. Lựa chọn tuyệt vời cho các mẫu áo khoác măng tô, áo vest dạ hay chân váy dạ mùa đông.",
        "vải thô đũi": "Chất thô đũi tự nhiên mộc mạc, thấm hút mồ hôi cực tốt và tạo cảm giác mát mẻ dễ chịu. Rất hợp cho các phong cách vintage, du lịch hay dạo phố thư thái.",
        "phối màu tương phản": "Quy tắc phối màu tương phản (như đen - trắng, xanh navy - cam đất) tạo ấn tượng thị giác mạnh mẽ, giúp outfit của bạn trông nổi bật và đầy tính thời trang.",
        "phối màu tone sur tone": "Phối đồ đơn sắc hoặc tone-sur-tone (cùng một dải màu với các sắc độ đậm nhạt khác nhau) là bí quyết đơn giản nhất để tạo vẻ ngoài tinh tế, sang trọng và hack chiều cao.",
        "phong cách retro": "Phong cách retro cổ điển chuộng các gam màu trầm ấm (nâu đất, vàng nghệ, xanh rêu) kết hợp họa tiết caro, chấm bi hoặc chất liệu denim wash bạc mang lại nét đẹp hoài niệm, nghệ thuật.",
        "phong cách bohemian": "Phong cách boho phóng khoáng với những thiết kế đầm maxi xòe bồng, họa tiết thổ cẩm độc đáo phối cùng phụ kiện da lộn, tua rua và nón rộng vành cho tâm hồn tự do.",
        "đi phượt": "Đi phượt dã ngoại nên ưu tiên sự bền bỉ và bảo vệ: áo khoác dù cản gió chống nước, quần túi hộp cargo hoặc quần jeans dày dặn, đi kèm giày cổ cao chống trơn trượt.",
        "đi cắm trại": "Đi cắm trại camping cuối tuần hãy chọn trang phục thoải mái: áo thun cotton thoáng mát, áo khoác gió mỏng, quần jogger hoặc short kaki và mũ tai bèo che nắng.",
        "tiệc công ty": "Dự tiệc công ty hoặc year-end party đòi hỏi sự chỉn chu nhưng cuốn hút: bạn nam có thể chọn suit cách điệu hoặc blazer phối sơ mi, bạn nữ có thể diện đầm midi lụa hoặc set dạ tweed sang trọng.",
        "prom": "Đêm dạ hội prom là lúc bạn tỏa sáng nhất: các bạn nam hãy chọn vest lịch lãm phối nơ hoặc cà vạt, các bạn nữ có thể diện đầm dạ hội dài quét đất hoặc đầm xòe công chúa lộng lẫy.",
        "buổi hẹn đầu tiên": "Buổi hẹn đầu tiên, chìa khóa là sự thoải mái và tự tin: chọn outfit vừa vặn, thơm tho, màu sắc trang nhã và tôn dáng tự nhiên để tạo thiện cảm gần gũi, đáng tin cậy.",
        "mùa xuân": "Mùa xuân tràn đầy sức sống với những gam màu tươi sáng, pastel nhẹ nhàng: áo kiểu hoa nhí, đầm voan bồng bềnh, sơ mi cổ tàu linen hay polo pastel mang lại năng lượng tươi mới.",
        "du xuân": "Du xuân rạng rỡ, bạn nên chọn trang phục lịch sự, tươi tắn như sơ mi sáng màu, polo dệt kim kết hợp quần khaki hoặc đầm voan ren nhẹ nhàng đón may mắn đầu năm.",
        "mùa hè": "Mùa hè ưu tiên các chất liệu tự nhiên, thoáng mát như cotton organic, thun lạnh dệt tổ ong, đũi linen nhẹ tênh: kết hợp áo thun/polo cùng quần short hoặc quần vải mỏng nhẹ giúp giải nhiệt tối đa.",
        "mùa thu": "Tiết trời mùa thu se lạnh cực hợp với phong cách layering nhẹ: áo thun mỏng phối ngoài cardigan dệt kim hoặc blazer mỏng, áo khoác gió trượt nước kết hợp tone màu be, nâu ấm áp.",
        "mùa đông": "Mùa đông rét buốt nên áp dụng nguyên tắc layering giữ nhiệt: lớp trong mỏng thấm hút (thun/len cổ lọ), lớp giữa cách nhiệt (cardigan/gile), lớp ngoài cản gió chống rét (áo khoác măng tô, chần bông hoặc jacket jeans dày dặn).",
        "4 mùa": "Thời trang 4 mùa linh hoạt: Xuân nhẹ nhàng tươi sáng, Hè thoáng mát năng động, Thu thanh lịch layer mỏng, Đông ấm áp và sang trọng với áo khoác dạ, măng tô.",
        "bốn mùa": "Thời trang 4 mùa linh hoạt: Xuân nhẹ nhàng tươi sáng, Hè thoáng mát năng động, Thu thanh lịch layer mỏng, Đông ấm áp và sang trọng với áo khoác dạ, măng tô.",
        "người vai rộng": "Người có bờ vai rộng nên chọn áo cổ chữ V, cổ tim hoặc áo tay raglan để tạo cảm giác vai thon gọn hơn, tránh các kiểu áo độn vai hoặc có cầu vai to.",
        "người bắp tay to": "Nếu có bắp tay hơi to, bạn nên ưu tiên áo sơ mi tay lỡ, áo tay bồng nhẹ hoặc khoác ngoài blazer/cardigan mỏng để che khuyết điểm khéo léo.",
        "người eo bánh mì": "Để giấu nhẹm vòng eo bánh mì, hãy chọn các mẫu đầm suông chữ A, đầm thắt eo cao empire waist hoặc phối áo peplum xòe nhẹ phần gấu quần cạp cao.",
        "concert": "Đi concert hãy diện outfit đậm chất nghệ sĩ, năng động và thoải mái để bạn thỏa sức hòa mình vào âm nhạc suốt đêm diễn.",
        "trẻ trung": "Phong cách trẻ trung thường hợp với áo thun, polo hoặc sơ mi oversize kết hợp quần jean, quần ống rộng và sneaker.",
        "trưởng thành": "Phong cách trưởng thành hướng tới sự chỉn chu và tinh tế. Bạn có thể ưu tiên áo sơ mi hoặc polo dệt kim tối màu phối cùng quần tây, quần chinos hoặc blazer casual và giày da/loafer sạch sẽ.",
        "năng động": "Bạn có thể ưu tiên áo thun oversize, polo hoặc hoodie kết hợp quần jean, quần short và sneaker để tạo cảm giác năng động.",
        "thanh lịch": "Phong cách thanh lịch có thể bắt đầu với sơ mi, polo hoặc blazer phối cùng quần tây, chân váy midi và giày đơn giản.",
        "công sở": "Outfit công sở có thể phối sơ mi hoặc polo với quần tây, chân váy chữ A hoặc blazer. Ưu tiên màu trung tính để tổng thể dễ phối.",
        "casual": "Phong cách casual dễ áp dụng với áo thun basic, sơ mi oversize hoặc polo kết hợp jean, kaki và sneaker.",
        "smart casual": "Smart-casual có thể kết hợp polo hoặc sơ mi với quần tây, jean tối màu và giày loafer hoặc sneaker tối giản.",
        "streetwear": "Streetwear thường hợp với áo oversize, hoodie, jacket hoặc sơ mi layer cùng quần cargo, jean rộng và sneaker.",
        "douyin": "Với phong cách Douyin cho tuổi đôi mươi, bạn có thể diện áo thun oversize phối layer cùng sơ mi khoác ngoài hoặc sơ vin vạt trước với quần ống rộng, kết hợp sneaker đế dày.",
        "minimal": "Phong cách minimal nên ưu tiên các item có thiết kế đơn giản, ít họa tiết và màu trung tính như trắng, đen, xám, be hoặc xanh navy.",
        "đi học": "Đi học nên ưu tiên outfit thoải mái và dễ vận động như áo thun, polo hoặc sơ mi phối cùng jean, kaki và sneaker.",
        "đi làm": "Đi làm có thể chọn sơ mi hoặc polo kết hợp quần tây, jean tối màu và giày loafer hoặc sneaker tối giản.",
        "đi chơi": "Đi chơi có thể thoải mái hơn với áo thun, polo hoặc sơ mi oversize kết hợp jean, cargo hoặc quần short.",
        "đi hẹn hò": "Buổi hẹn hò nên ưu tiên trang phục chỉn chu nhưng thoải mái: kết hợp sơ mi hoặc polo cùng quần âu/chinos, hoặc đầm/chân váy thanh lịch với phụ kiện tối giản.",
        "đi du lịch": "Đi du lịch nên ưu tiên những item nhẹ, thoải mái và dễ phối như áo thun, sơ mi mỏng, quần short hoặc quần ống rộng.",
        "đi biển": "Đi biển có thể chọn sơ mi linen, áo thun sáng màu, quần short hoặc váy maxi. Các màu trắng, xanh nhạt và be thường tạo cảm giác thoáng mát.",
        "đám cưới": "Đi đám cưới nên ưu tiên outfit lịch sự nhưng không quá nổi bật hơn nhân vật chính. Nam có thể chọn sơ mi và quần tây, nữ có thể chọn đầm midi hoặc thiết kế thanh lịch.",
        "đầm tiệc cưới": "Với tiệc cưới sang trọng, các thiết kế đầm midi, đầm lụa hoặc đầm ren với màu pastel, xanh nhạt hoặc đỏ rượu có thể tạo cảm giác thanh lịch.",
        "tiệc sinh nhật": "Với tiệc sinh nhật, bạn có thể phối sơ mi hoặc polo cùng quần tây, jeans ống suông hoặc blazer để tạo outfit vừa trẻ trung vừa chỉn chu.",
        "phỏng vấn": "Đi phỏng vấn nên ưu tiên trang phục đơn giản, sạch sẽ và lịch sự như sơ mi phối quần tây hoặc chân váy có độ dài phù hợp.",
        "đi cà phê": "Đi cà phê có thể chọn outfit casual như áo thun, polo hoặc sơ mi oversize phối cùng jean, kaki hoặc quần ống rộng.",
        "màu đen": "Màu đen rất dễ phối. Bạn có thể kết hợp với trắng, xám, be hoặc denim để tạo tổng thể cân bằng.",
        "màu trắng": "Màu trắng có thể phối cùng gần như mọi màu. Kết hợp với jean xanh, đen, be hoặc nâu sẽ rất dễ mặc.",
        "màu be": "Màu be hợp với trắng, nâu, đen, xanh denim và các tone trung tính, tạo cảm giác nhẹ nhàng và hiện đại.",
        "màu xanh": "Các tone xanh có thể phối cùng trắng, xám, be hoặc denim tùy sắc độ để tổng thể hài hòa.",
        "màu đỏ": "Màu đỏ là điểm nhấn khá mạnh, nên phối cùng những màu trung tính như đen, trắng, xám hoặc be để outfit cân bằng.",
        "màu pastel": "Pastel có thể phối cùng trắng, kem, be hoặc các màu pastel tương đồng để tạo outfit nhẹ nhàng.",
        "trời nóng": "Khi trời nóng, nên ưu tiên áo thun, polo, sơ mi linen hoặc các item có chất liệu nhẹ và thoáng.",
        "trời lạnh": "Khi trời lạnh, có thể mặc layer áo thun hoặc sơ mi bên trong rồi kết hợp cardigan, hoodie, jacket hoặc áo khoác.",
        "trời mưa": "Trời mưa nên ưu tiên trang phục gọn gàng, nhanh khô và hạn chế các item quá dài. Có thể kết hợp áo khoác nhẹ và giày dễ vệ sinh.",
        "người thấp": "Nếu muốn tạo cảm giác cân đối hơn, bạn có thể ưu tiên outfit có tỷ lệ gọn gàng, áo vừa người và quần có chiều dài phù hợp.",
        "người cao": "Người có chiều cao tốt có thể thử nhiều kiểu dáng như quần ống rộng, oversize hoặc layer để tạo thêm điểm nhấn cho outfit.",
        "dáng người gầy": "Có thể thử layering nhẹ, áo có phom đứng hoặc hơi rộng và phối nhiều lớp để tạo tổng thể cân đối.",
        "dáng người đầy đặn": "Có thể ưu tiên trang phục có phom vừa vặn, đường nét đơn giản và màu sắc hài hòa để tổng thể gọn gàng.",
        "sneaker": "Sneaker trắng hoặc màu trung tính có thể phối với jean, kaki, quần ống rộng và nhiều outfit casual khác.",
        "giày": "Hãy chọn giày dựa trên hoàn cảnh. Sneaker phù hợp outfit casual, loafer hợp smart-casual và giày da phù hợp những dịp trang trọng.",
        "túi xách": "Túi có màu trung tính như đen, trắng, be hoặc nâu sẽ dễ phối với nhiều outfit và có thể dùng trong nhiều hoàn cảnh.",
        "phụ kiện": "Nếu outfit đã có nhiều màu hoặc họa tiết, nên dùng phụ kiện đơn giản. Với outfit basic, đồng hồ, vòng tay, dây chuyền hoặc túi có thể trở thành điểm nhấn.",
        "layer": "Bạn có thể layer áo thun bên trong với sơ mi, cardigan, blazer hoặc jacket bên ngoài để outfit có chiều sâu hơn.",
        "oversize": "Đồ oversize nên cân bằng với một item có phom gọn hơn. Ví dụ áo oversize phối cùng quần straight hoặc quần vừa phom.",
        "quần ống rộng": "Quần ống rộng có thể phối với áo thun, polo, sơ mi hoặc croptop tùy phong cách. Nên cân đối tỷ lệ giữa áo và quần.",
        "áo croptop": "Áo croptop có thể phối cùng quần jean cạp cao, quần ống rộng hoặc chân váy để tạo outfit trẻ trung.",
        "mặc với gì": "Bạn cho mình biết món đồ bạn đang muốn phối hoặc hoàn cảnh bạn sắp tham gia nhé. Mình có thể gợi ý cả áo, quần, giày và phụ kiện.",
        "phối đồ": "Bạn cho mình biết món đồ chính, màu sắc và dịp mặc nhé. Mình sẽ gợi ý một set hoàn chỉnh thay vì chỉ đề xuất một món.",
        "set đồ": "Bạn có thể cho mình biết phong cách mong muốn như trẻ trung, thanh lịch, streetwear hoặc công sở. Mình sẽ gợi ý một outfit hoàn chỉnh.",
        "mặc gì": "Bạn sắp đi đâu và muốn theo phong cách nào? Mình có thể dựa vào dịp mặc, thời tiết và ngân sách để gợi ý outfit phù hợp.",
        "không biết mặc gì": "Không sao nha 😎 Bạn chỉ cần cho mình biết hôm nay đi đâu, thời tiết thế nào và thích phong cách nào, mình sẽ giúp bạn lên một outfit hoàn chỉnh.",
        "nên chọn": "Để chọn chính xác hơn, bạn có thể cho mình biết mục đích mặc, màu sắc yêu thích, ngân sách và phong cách mong muốn.",
        "nên mua": "Mình có thể giúp bạn so sánh các sản phẩm dựa trên giá, chất liệu, kiểu dáng, mục đích sử dụng và khả năng phối đồ.",
        "phù hợp không": "Bạn gửi mình sản phẩm hoặc mô tả outfit hiện tại nhé. Mình có thể xem xét màu sắc, kiểu dáng và hoàn cảnh sử dụng để đưa ra gợi ý phối đồ.",
        "cotton": "Cotton thường được lựa chọn cho trang phục hàng ngày vì cảm giác mềm và thoải mái. Phù hợp với áo thun, polo và nhiều outfit casual.",
        "linen": "Linen phù hợp với thời tiết nóng nhờ cảm giác nhẹ và thoáng. Sơ mi linen có thể phối cùng quần short, kaki hoặc quần ống rộng.",
        "jean": "Chất liệu denim có độ bền tốt và rất dễ phối. Bạn có thể kết hợp jean với áo thun, sơ mi, polo hoặc jacket.",
        "lụa": "Chất liệu lụa tạo cảm giác mềm mại và thanh lịch, phù hợp với các outfit dự tiệc, hẹn hò hoặc những dịp cần sự chỉn chu.",
        "sinh viên": "Sinh viên có thể ưu tiên các item dễ phối và sử dụng thường xuyên như áo thun, polo, sơ mi, jean, kaki và sneaker.",
        "người trẻ": "Phong cách trẻ có thể thử oversize, streetwear, smart-casual hoặc minimal tùy cá tính.",
        "trung niên": "Có thể ưu tiên những thiết kế đơn giản, phom vừa vặn và màu sắc trung tính để tạo cảm giác lịch sự, dễ mặc.",
        "hẹn hò": "Buổi hẹn hò nên ưu tiên một outfit vừa thoải mái vừa chỉn chu. Sơ mi hoặc polo gọn gàng phối quần âu/chinos, hoặc đầm thiết kế trang nhã đi kèm phụ kiện tinh tế.",
        "chụp ảnh": "Nếu mục đích là chụp ảnh, bạn có thể chọn outfit có một điểm nhấn rõ ràng như màu sắc, phụ kiện hoặc layer thay vì quá nhiều chi tiết cùng lúc.",
        "đi concert": "Đi concert nên ưu tiên outfit thoải mái, dễ vận động và có điểm nhấn cá tính như áo graphic, jacket, cargo hoặc sneaker.",
        "đi du lịch cùng bạn bè": "Bạn có thể chọn outfit thoải mái nhưng có màu sắc hoặc phụ kiện đồng điệu để vừa dễ vận động vừa đẹp khi chụp ảnh nhóm.",
        "đi phỏng vấn": "Ưu tiên trang phục sạch sẽ, vừa vặn và lịch sự. Sơ mi kết hợp quần tây âu hoặc chân váy dài qua gối là lựa chọn an toàn, chuyên nghiệp.",
        "chân váy": "Chân váy có thể phối với áo thun, sơ mi, cardigan hoặc blazer. Sneaker tạo cảm giác trẻ trung, còn loafer hoặc giày cao gót sẽ thiên về thanh lịch.",
        "váy maxi": "Váy maxi phù hợp với những chuyến du lịch hoặc đi biển. Có thể phối cùng sandal, túi cói và phụ kiện đơn giản.",
        "váy body": "Váy body có thể phối với blazer hoặc cardigan nếu muốn tạo tổng thể cân bằng và phù hợp nhiều hoàn cảnh hơn.",
        "áo cardigan": "Cardigan có thể mặc ngoài áo thun, sơ mi hoặc phối cùng chân váy và jean để tạo phong cách nhẹ nhàng.",
        "quần kaki": "Quần kaki có thể phối với polo, áo thun hoặc sơ mi. Kết hợp sneaker hoặc loafer tùy mức độ lịch sự mong muốn.",
        "hoodie": "Hoodie phù hợp với jean, cargo hoặc jogger. Kết hợp sneaker sẽ tạo outfit casual và năng động.",
        "jacket": "Jacket có thể layer cùng áo thun hoặc hoodie, phối với jean, cargo hoặc quần ống suông tùy phong cách.",
        "áo blazer": "Blazer có thể phối với sơ mi và quần tây cho phong cách lịch sự, hoặc áo thun và jean để tạo smart-casual.",
        "dễ phối": "Nếu ưu tiên khả năng phối đồ, hãy chọn những item có màu trung tính và thiết kế cơ bản như trắng, đen, be, xám hoặc navy.",
        "mặc được nhiều dịp": "Các item basic như polo, sơ mi, áo thun, jean tối màu hoặc blazer thường dễ biến đổi từ casual sang lịch sự.",
        "giá rẻ": "Nếu ngân sách hạn chế, nên ưu tiên những món basic có thể phối được với nhiều trang phục khác thay vì mua quá nhiều item theo xu hướng.",
        "đáng mua": "Một sản phẩm đáng cân nhắc không chỉ dựa vào giá mà còn phụ thuộc chất liệu, độ bền, kiểu dáng, tần suất sử dụng và khả năng phối với tủ đồ hiện tại.",
        "basic": "Nếu thích phong cách basic, hãy ưu tiên áo thun trơn, polo, sơ mi đơn giản, jean và các màu trung tính. Những món này rất dễ kết hợp với nhau."
    }

    CLOSINGS_BY_SITUATION = {
        "find_product": [
            # Chung
            "Bạn đang ưng mẫu nào nhất? Nếu cần mình tư vấn thêm về size, màu hoặc cách phối đồ thì cứ nhắn mình nha! ✨",
            "Bạn cứ xem kỹ các mẫu bên trên nhé. Ưng em nào thì gửi mình tên hoặc mã sản phẩm, mình tư vấn tiếp cho bạn nè! 🥰",
            "Nếu bạn chưa biết chọn mẫu nào, cứ nói mình phong cách bạn thích, mình chọn giúp luôn nha!",
            "Bạn thích mẫu nào thì mình có thể tư vấn thêm về chất liệu, form dáng, màu sắc và cách phối cho bạn nhé!",
            # Xem thêm
            "Nếu chưa thấy mẫu thật sự ưng ý, mình có thể tìm thêm theo màu, kiểu dáng, mức giá hoặc phong cách bạn muốn nhé!",
            "Muốn xem thêm mẫu tương tự cũng được nha. Bạn chỉ cần nói mình muốn thay đổi tiêu chí nào.",
            "Nếu muốn nhiều lựa chọn hơn, mình có thể mở rộng tìm kiếm sang các kiểu dáng hoặc màu gần giống.",
            # Chốt mua
            "Nếu bạn đã ưng mẫu nào thì gửi mình tên hoặc mã sản phẩm, mình hỗ trợ bạn kiểm tra thông tin tiếp nhé! 🛍️",
            "Đã chấm được em nào chưa nè? 😎 Nếu có rồi, gửi mình mẫu bạn thích để mình hỗ trợ bước tiếp theo nhé!",
            "Nếu đã chọn được mẫu, mình có thể hỗ trợ bạn kiểm tra size, màu và thông tin sản phẩm trước khi đặt nhé!",
            # Tự nhiên / Hội thoại
            "Cứ hỏi mình bất cứ điều gì về sản phẩm nhé, từ size, màu, chất liệu tới cách phối đồ đều được nha! ✨",
            "Bạn cứ mô tả thứ bạn đang cần bằng cách tự nhiên nhất, mình sẽ cố gắng tìm sản phẩm phù hợp cho bạn.",
            "Không cần nhớ tên sản phẩm đâu, bạn mô tả kiểu bạn muốn mặc là mình có thể hỗ trợ tìm theo nhu cầu nha!"
        ],

        "find_outfit": [
            # Phối đồ
            "Nếu bạn đã chọn được áo hoặc quần, gửi mình mẫu đó nhé. Mình có thể phối tiếp cả set từ đầu đến chân cho bạn. 👕👖👟",
            "Muốn outfit hoàn chỉnh hơn thì mình có thể gợi ý thêm quần, áo, giày và phụ kiện đi cùng nha!",
            "Nếu bạn muốn theo một vibe cụ thể như basic, Douyin, streetwear hay smart-casual, cứ nói mình biết nhé!",
            "Có món đồ rồi mà chưa biết phối gì? Cứ gửi mình, Evern phối outfit cho bạn luôn 😎",
            # Theo dịp
            "Nếu bạn đang tìm đồ cho một dịp cụ thể như đi làm, đi học, hẹn hò hay dự tiệc, nói mình biết để mình lên outfit phù hợp nhé!",
            "Bạn sắp đi đâu thì nói mình nha, mình có thể chọn outfit phù hợp với hoàn cảnh đó luôn!",
            "Nếu cần một set vừa đẹp vừa phù hợp hoàn cảnh, cứ cho mình biết bạn chuẩn bị đi đâu nhé!",
            "Chỉ cần nhắn chiều cao và cân nặng là Evern Stylist sẽ chọn size vừa vặn chuẩn chỉnh cho cả set đồ luôn nha! 🌟",
            "Bạn muốn set đồ này mang hơi hướng thanh lịch nhẹ nhàng hay cá tính nổi bật? Cứ chia sẻ gu thời trang bạn thích để mình mix & match trọn bộ nhé! ✨",
            "Nếu bạn cần thêm phụ kiện như túi xách, mũ, thắt lưng da hay giày ton-sur-ton để hoàn thiện set đồ thì bảo mình ngay nha! 👜👟",
            "Một outfit đẹp sẽ giúp bạn tự tin gấp bội! Bạn có muốn mình phối thử thêm 1-2 phương án khác với phong cách này không nè? 💫",
            "Set đồ này cực kỳ linh hoạt, có thể biến tấu nhiều kiểu mặc khác nhau. Bạn ưng ý cách phối trên chưa hay muốn điều chỉnh chi tiết nào ạ? ❤️",
            "Bạn đang nhắm set này cho chuyến đi hay dịp quan trọng nào sắp tới? Nhắn mình để mình check độ tiện dụng và thoải mái của cả set cho bạn nha! ✈️",
            "Muốn hack dáng đỉnh hơn với set đồ này, bạn có thể sơ vin vạt trước hoặc kết hợp giày đế bánh mì/cao gót nhé. Cần mình tư vấn chi tiết cách mặc cứ nhắn nha! 🔥",
            "Evern có sẵn trọn bộ từ áo, quần tới phụ kiện đi kèm. Bạn thích phối theo phong cách layer nhiều lớp hay tối giản gọn gàng nè? 🌿"
        ],

        "find_by_price": [
            "Nếu bạn có ngân sách cụ thể, cứ nói mức giá bạn muốn nhé. Mình có thể lọc những mẫu phù hợp hơn cho bạn. 💰",
            "Bạn muốn giữ ngân sách khoảng bao nhiêu? Mình có thể ưu tiên những lựa chọn vừa túi tiền hơn.",
            "Nếu các mẫu trên chưa đúng tầm giá, nói mình khoảng ngân sách của bạn, mình tìm lại nhé!",
            "Các mẫu trên đều đang có mức giá ưu đãi cực kỳ tốt trong tầm ngân sách của bạn đó ạ! Bạn thích mẫu nào nhất nè? 💸",
            "Mức giá siêu hời cho chất liệu cao cấp và bền đẹp! Bạn muốn mình giữ hàng mẫu nào trước cho bạn không nè? ✨",
            "Shop luôn có nhiều phân khúc giá từ học sinh sinh viên đến dòng thiết kế cao cấp. Bạn muốn xem thêm mẫu ở tầm giá nào nữa không ạ? 🏷️",
            "Tất cả các sản phẩm trên đều có tỷ lệ 'đáng tiền' cực cao về độ bền đường may và chất vải. Bạn cần mình tư vấn kỹ hơn về mẫu nào nè? 💎",
            "Nếu bạn muốn săn deal hot hoặc voucher giảm giá cho đơn hàng hôm nay, cứ nhắn mình để nhận ưu đãi tốt nhất nha! 🎁",
            "Mức giá này đã tối ưu nhất so với chất lượng trên thị trường rồi ạ. Bạn có muốn mình chốt giữ size cho mẫu bạn thích không? 🛍️",
            "Bạn đang muốn tìm mẫu 'ngon - bổ - rẻ' để mặc hàng ngày hay muốn đầu tư một món đồ thật xịn sò bền bỉ? Chia sẻ với mình nhé! 🌟",
            "Ngoài các mẫu trên, shop còn có các combo mua 2 tặng quà hoặc trợ giá freeship đó nha. Bạn có muốn xem thêm chi tiết không ạ? 🚚",
            "Chỉ từ mức giá này mà rinh được outfit vừa xịn vừa tôn dáng thì quá hời luôn nè! Bạn chấm em nào để mình kiểm tra kho nhé! 😉"
        ],

        "find_by_style": [
            # Khách trẻ / Gen Z
            "Ưng em nào thì hú mình một tiếng nha 😎 Mình tư vấn tiếp từ size, màu tới cách phối luôn!",
            "Nếu vẫn chưa thấy đúng vibe thì nói gu bạn muốn, mình tìm hướng khác cho tới khi bắt đúng style nha 🔥",
            "Chưa chốt được cũng không sao 😆 Bạn nói mình vibe muốn theo, Evern tìm tiếp cho!",
            "Muốn lên outfit xịn hơn thì quăng cho mình dịp mặc + ngân sách + style, mình build set cho luôn 👀✨",
            "Lên đồ phong cách này đảm bảo cực kỳ cuốn hút và có gu luôn nha! Bạn ưng ý item nào nhất trong set này nè? 🔥",
            "Style này đang là hot trend cực kỳ thịnh hành trên Douyin và Pinterest đó nha! Bạn muốn mix thêm phụ kiện gì cho chuẩn bài không? 🕶️",
            "Nếu bạn muốn thử biến hóa phong cách mới lạ hơn thường ngày, cứ để Evern Stylist gợi ý những cách mix độc đáo nhé! 💫",
            "Phong cách này vừa tôn lên cá tính riêng vừa không kén dáng người. Bạn thấy mẫu nào hợp với thần thái của mình nhất nè? 💖",
            "Bạn thích sự chỉn chu thanh lịch hay năng động phóng khoáng hơn một chút? Nói mình biết để mình tinh chỉnh outfit theo đúng gu nhé! 🎨",
            "Set đồ này diện lên chụp ảnh check-in sống ảo đảm bảo nghìn like luôn ạ! Bạn muốn mình gợi ý thêm góc phối đồ đẹp không nè? 📸",
            "Gu ăn mặc của bạn rất có chất riêng đó nha! Nếu muốn khám phá thêm các bộ sưu tập mang cùng hơi thở này thì nhắn mình liền nha! 🚀",
            "Chỉ cần thay đổi một chiếc áo khoác hoặc đôi giày là phong cách này có thể biến hóa từ đi làm sang đi chơi tức thì đó ạ! ✨"
        ],

        "find_by_color": [
            "Bạn đang phân vân màu nào thì nói mình nha. Mình có thể gợi ý màu dễ phối hoặc phù hợp với phong cách bạn thích. 🎨",
            "Nếu chưa biết chọn màu nào, mình có thể gợi ý những màu dễ mặc và dễ phối với tủ đồ hiện tại của bạn.",
            "Bạn thích tone sáng, tối hay trung tính? Mình có thể lọc lại cho bạn nhanh hơn nha!",
            "Tone màu này cực kỳ sáng da và dễ phối luôn ạ! Bạn muốn xem thêm chi tiết hay muốn mình tư vấn size cho mẫu nào nè? 🎨",
            "Màu sắc bên ngoài đảm bảo chuẩn đẹp và tôn da như ảnh. Bạn cần mình chọn size theo chiều cao/cân nặng không ạ? ❤️",
            "Nếu bạn thuộc tone da ngăm hoặc da trắng sáng, nhắn mình để mình chọn gam màu nâng tone da đẹp nhất cho bạn nhé! 🌈",
            "Tone màu này phối cùng các gam trung tính như be, trắng, đen hay denim là chuẩn không cần chỉnh luôn ạ! ✨",
            "Bạn muốn một gam màu an toàn dễ mặc mỗi ngày hay một tone màu bắt mắt, nổi bật để đi tiệc/đi chơi nè? 🌟",
            "Sắc độ màu này cực kỳ nhã nhặn và sang trọng, không lo lỗi mốt theo thời gian đâu ạ. Bạn ưng gam màu này chưa nè? 🌿",
            "Nếu tủ đồ của bạn đã có sẵn màu này, mình có thể gợi ý các phối màu tương phản hoặc tone-sur-tone cực sành điệu nhé! 👗",
            "Màu này ở ngoài ánh sáng tự nhiên nhìn rất mịn và hút mắt. Bạn muốn mình chụp cận cảnh chất vải và màu sắc không ạ? 📸",
            "Bạn có muốn xem thêm các phiên bản màu sắc khác của dòng sản phẩm này không, shop còn nhiều màu xinh lắm nha! 💖"
        ],

        "find_by_size": [
            "Nếu bạn chưa chắc về size, gửi mình chiều cao và cân nặng, mình hỗ trợ chọn size phù hợp nhé! 📏",
            "Không chắc nên lấy size nào cũng không sao nha. Bạn cho mình chiều cao, cân nặng và thích mặc vừa hay rộng, mình tư vấn tiếp cho!",
            "Bạn thích mặc vừa người hay form rộng thoải mái? Nói mình biết để mình hỗ trợ chọn size phù hợp hơn nha.",
            "Nếu đang phân vân giữa hai size, cứ gửi mình thông tin cơ bản của bạn, mình giúp bạn cân nhắc nhé!",
            "Tất cả mẫu trên đều đang sẵn đúng size bạn tìm ạ! Bạn muốn mình hỗ trợ lên đơn giữ hàng ngay không nè? 📏",
            "Phom dáng của mẫu này là regular fit chuẩn dáng người Việt. Chỉ cần cho mình chiều cao và cân nặng là chuẩn size 100% luôn ạ! 🎯",
            "Bạn thích form áo ôm nhẹ tôn dáng hay form rộng giấu quần/freesize thoải mái nè? Nhắn mình để mình lấy size đúng ý nha! 👕",
            "Nếu số đo của bạn nằm giữa 2 size, mình sẽ tư vấn chi tiết theo sở thích mặc rộng hay ôm của bạn nhé. Đừng ngần ngại nhắn mình! 💡",
            "Evern có chính sách hỗ trợ đổi size tận nhà cực kỳ nhanh chóng và thuận tiện nếu chẳng may không vừa vặn nha! 🔄",
            "Các mẫu này bảng size rất chuẩn, chất co giãn dễ chịu. Bạn cần mình check số đo chi tiết (dài áo, rộng vai, vòng ngực) không nè? 📐",
            "Size này đang là size bán chạy nhất của shop nên số lượng còn ít ạ, bạn ưng mẫu nào thì chốt sớm để mình giữ hàng nhé! ⚡",
            "Bạn cho mình xin chiều cao + cân nặng, mình sẽ báo ngay mẫu nào mặc lên người bạn chuẩn đẹp nhất nhé! ✨"
        ],

        "recommend_gift": [
            "Nếu bạn đang mua tặng người khác, cho mình biết độ tuổi, giới tính và phong cách của người nhận, mình có thể gợi ý dễ hơn nha! 🎁",
            "Mua quà mà sợ chọn khó mặc thì cứ nói mình người nhận thích phong cách nào, mình chọn những mẫu dễ sử dụng hơn cho bạn.",
            "Bạn có muốn shop hỗ trợ đóng hộp quà sang trọng kèm thiệp viết tay gửi tặng người nhận không nè? 🎁",
            "Món quà này vừa tinh tế vừa thiết thực, đảm bảo người nhận sẽ rất vui! Bạn cần mình tư vấn thêm về số đo để chọn size chuẩn nhất không ạ? ❤️",
            "Evern có hỗ trợ đổi size linh hoạt trong 7 ngày nên bạn hoàn toàn yên tâm chọn làm quà tặng nha! 🎀",
            "Tặng quà thời trang thể hiện sự quan tâm rất chu đáo! Bạn có muốn mình gợi ý thêm các item dễ mặc freesize để không lo bị lệch size không? 🌟",
            "Mẫu này đóng gói làm quà sinh nhật, kỷ niệm hay ngày lễ đều cực kỳ lịch sự và ghi điểm tuyệt đối luôn ạ! 💐",
            "Nếu bạn muốn ghi kèm lời chúc ý nghĩa, Evern sẽ tặng kèm thiệp viết tay thiết kế riêng gửi gắm tâm tư của bạn nhé! 💌",
            "Bạn đang tìm quà tặng bạn bè, người yêu hay người thân gia đình nè? Nhắn mình mối quan hệ để mình chọn món quà đúng tâm lý nhất nha! 💝",
            "Đây là những mẫu best-seller được khách hàng chọn làm quà tặng nhiều nhất tại shop đó ạ. Bạn ưng mắt mẫu nào nhất nè? 🛍️",
            "Shop có sẵn set hộp quà cao cấp thắt nơ sang trọng, bạn chỉ việc nhận hàng và mang tặng thôi nha! Cần mình hỗ trợ thêm không nè? 🎀",
            "Tặng một món đồ thời trang vừa vặn với gu của người nhận sẽ khiến họ nhớ mãi! Bạn có biết người ấy thích màu sắc gì không ạ? 🎨"
        ],

        "formal_advice": [
            "Nếu cô/chú cần tư vấn thêm về size, chất liệu hoặc màu sắc, cô/chú cứ cho tôi biết, tôi hỗ trợ thêm ạ.",
            "Nếu cô/chú cho tôi biết chiều cao, cân nặng và mục đích sử dụng, tôi có thể tư vấn mẫu phù hợp hơn ạ.",
            "Cô/chú đang phân vân mẫu nào thì cứ cho tôi biết, tôi có thể hỗ trợ so sánh và tư vấn thêm ạ.",
            "Các mẫu này phom dáng rất đứng đắn và chất liệu mềm mát, đảm bảo người mặc sẽ rất ưng ý. Bạn cần mình tư vấn thêm về cân nặng/chiều cao để chọn size chuẩn nhất không ạ? 👔",
            "Chất vải cao cấp, đứng phom và ít nhăn rất phù hợp cho người lớn tuổi. Bạn đang ưng mắt mẫu nào nhất ạ? 🌟",
            "Dạ các mẫu trên đều có thiết kế trang nhã, kín đáo và đường may rất tỉ mỉ. Cô/chú cần xem thêm chi tiết cổ áo hay chiều dài áo không ạ? 🌿",
            "Dạ chất liệu vải cotton lụa và tuyết mưa này mặc rất nhẹ, thoáng mồ hôi và không cần là ủi nhiều, rất tiện lợi cho các bác các chú ạ! 🌾",
            "Nếu cô/chú muốn chọn trang phục đi dự sự kiện quan trọng, cưới hỏi hay gặp mặt bạn bè, tôi có thể phối thêm áo khoác hoặc phụ kiện thanh lịch ạ. 👔",
            "Dạ showroom có đầy đủ các size lớn đến 3XL thoải mái cho các bác, cô chú. Quý khách cứ yên tâm để shop chọn kích cỡ vừa vặn nhất nhé ạ! 📏",
            "Màu sắc nhã nhặn, tôn lên vẻ đĩnh đạc và sang trọng của độ tuổi trung niên. Quý khách đang ưng ý thiết kế nào nhất ạ? ✨",
            "Dạ nếu quý khách mua tặng bố mẹ hoặc người lớn trong nhà, shop có hỗ trợ kiểm tra hàng trước khi thanh toán và đổi size tận nơi ạ! 🎁",
            "Các thiết kế này rất được các cô chú trung niên ưa chuộng nhờ phom suông che khuyết điểm bụng cực tốt. Cần hỗ trợ thêm gì cô/chú cứ nhắn tôi nhé ạ! 🌸"
        ],

        "compare": [
            "Nếu đang phân vân giữa vài mẫu, gửi mình các mẫu đó nhé. Mình có thể giúp bạn so sánh kiểu dáng, chất liệu, giá và mục đích sử dụng.",
            "Chưa biết chọn em nào cũng không sao 😎 Bạn gửi mình 2-3 mẫu đang phân vân, mình phân tích từng mẫu cho dễ quyết định hơn.",
            "Bạn cứ tham khảo từ từ nha, chưa cần chốt ngay đâu. Nếu cần mình so sánh các mẫu thì cứ gửi mình nhé!",
            "Nếu vẫn đang phân vân, bạn nói mình biết điều bạn quan tâm nhất: giá, form, chất liệu hay kiểu dáng, mình sẽ lọc theo tiêu chí đó.",
            "Mỗi mẫu đều có một nét cuốn hút riêng! Nếu bạn thích sự thoải mái hàng ngày thì mẫu A là số 1, còn nếu muốn nổi bật khi đi tiệc thì mẫu B sẽ vượt trội hơn đó nha. Bạn muốn mình so sánh chi tiết điểm nào nè? ⚖️",
            "Để chọn được em ưng ý nhất, bạn thử cân nhắc xem mẫu nào phối được nhiều món đồ có sẵn trong tủ quần áo của bạn hơn nhé! Cần mình so sánh tính đa dụng thì bảo mình nha! 💡",
            "Bạn đang lăn tăn về chất vải hay mức giá chênh lệch giữa các mẫu? Nhắn mình để mình phân tích ưu - nhược điểm của từng em cho bạn dễ chọn nha! 🔍",
            "Hai mẫu này phom dáng và chất liệu có sự khác biệt rõ rệt đó ạ. Bạn muốn phong cách trẻ trung năng động hay thanh lịch chững chạc hơn để mình gợi ý mẫu vượt trội hơn nè? ✨",
            "Nếu ngân sách cho phép, cả hai em này đều là những item 'đáng đồng tiền bát gạo'. Bạn muốn mình kiểm tra số lượng tồn kho xem mẫu nào sắp hết size trước không? ⏳",
            "So sánh về độ bền và tính ứng dụng: một bên cực kỳ dễ giặt ủi ít nhăn, một bên tôn dáng và sang chảnh hơn. Bạn ưu tiên tiêu chí nào nhất lúc này nè? 🎯",
            "Đừng lo nếu thấy khó chọn, bạn cứ gửi tên 2 sản phẩm bạn thích nhất, Evern Stylist sẽ lập bảng so sánh chi tiết từ A-Z giúp bạn chốt đơn chuẩn nhất nhé! 📊",
            "Mẫu nào cũng xinh xắn hết nè! Nếu bạn thích phong cách nổi bật thì chọn mẫu thứ nhất, còn thích an toàn dễ mặc đi muôn nơi thì mẫu thứ hai là chuẩn bài nha! 🥰"
        ],

        "default": [
            "Bạn đang ưng mẫu nào nhất? Nếu cần mình tư vấn thêm về size, màu hoặc cách phối đồ thì cứ nhắn mình nha! ✨",
            "Bạn cứ xem kỹ các mẫu bên trên nhé. Ưng em nào thì gửi mình tên hoặc mã sản phẩm, mình tư vấn tiếp cho bạn nè! 🥰",
            "Nếu bạn chưa biết chọn mẫu nào, cứ nói mình phong cách bạn thích, mình chọn giúp luôn nha!",
            "Bạn thích mẫu nào thì mình có thể tư vấn thêm về chất liệu, form dáng, màu sắc và cách phối cho bạn nhé!"
        ]
    }

    # Danh sách kết câu mặc định và bí danh tương thích ngược
    CLOSINGS = CLOSINGS_BY_SITUATION["default"]
    CLOSINGS_FIND = CLOSINGS_BY_SITUATION["find_product"]
    CLOSINGS_OUTFIT = CLOSINGS_BY_SITUATION["find_outfit"]
    CLOSINGS_BUDGET = CLOSINGS_BY_SITUATION["find_by_price"]
    CLOSINGS_STYLE = CLOSINGS_BY_SITUATION["find_by_style"]
    CLOSINGS_COLOR = CLOSINGS_BY_SITUATION["find_by_color"]
    CLOSINGS_SIZE = CLOSINGS_BY_SITUATION["find_by_size"]
    CLOSINGS_GIFT = CLOSINGS_BY_SITUATION["recommend_gift"]
    CLOSINGS_FORMAL = CLOSINGS_BY_SITUATION["formal_advice"]
    CLOSINGS_COMPARE = CLOSINGS_BY_SITUATION["compare"]

    @classmethod
    def get_opener(
        cls,
        situation: str = "find_product",
        user_message: str = "",
        entities: Optional[Dict[str, Any]] = None
    ) -> str:
        entities = entities or {}
        msg_l = (user_message or "").lower()

        # Hỗ trợ cả key chuẩn và alias
        key_map = {
            "find_product": "find_product",
            "find_outfit": "find_outfit",
            "find_outfit_general": "find_outfit_general",
            "find_by_price": "find_by_price",
            "budget": "find_by_price",
            "find_by_style": "find_by_style",
            "style": "find_by_style",
            "find_by_color": "find_by_color",
            "color": "find_by_color",
            "find_by_size": "find_by_size",
            "size": "find_by_size",
            "recommend_gift": "recommend_gift",
            "gift": "recommend_gift",
            "formal_advice": "formal_advice",
            "formal": "formal_advice",
            "ask_clarification": "ask_clarification",
            "clarify": "ask_clarification",
            "empty_product": "empty_product",
            "empty": "empty_product",
            "empty_budget": "empty_budget",
            "empty_size": "empty_size",
            "empty_color": "empty_color",
            "empty_style": "empty_style",
            "empty_formal": "empty_formal",
            "empty_gift": "empty_gift"
        }
        mapped_key = key_map.get(situation, situation)

        # Xử lý thông minh cho find_product theo số lượng tiêu chí người dùng đưa ra
        if mapped_key == "find_product":
            criteria_count = sum(1 for k in ["category", "sub_category", "color", "size", "max_price", "min_price", "style", "occasion", "gender"] if entities.get(k))
            wants_fast = any(w in msg_l for w in ["chốt nhanh", "mua nhanh", "chọn nhanh", "gấp", "lấy luôn"])
            
            if criteria_count >= 3:
                pool = [
                    "Dạ mình đã kết hợp các tiêu chí bạn đưa ra và lọc những sản phẩm phù hợp nhất rồi ạ:",
                    "Bạn đưa khá nhiều tiêu chí nhưng mình đã lọc lại giúp bạn rồi nha 😎 Đây là những mẫu phù hợp nhất:",
                    "Mình đã ưu tiên đồng thời kiểu dáng, màu sắc, mức giá và phong cách bạn yêu cầu. Bạn xem thử nhé:"
                ]
            elif wants_fast:
                pool = [
                    "Dạ nếu bạn muốn chọn nhanh thì mình đã lọc sẵn một số mẫu đáng tham khảo nhất:",
                    "Nếu muốn chốt nhanh thì bạn có thể xem qua những mẫu này trước nha:",
                    "Mình đã rút gọn danh sách để bạn dễ chọn hơn rồi ạ:"
                ]
            else:
                pool = [
                    "Dạ Evern chào bạn nha! ✨ Mình đã tìm thấy các mẫu khá sát với nhu cầu của bạn đây ạ:",
                    "Chào bạn nhé! 👋 Mình vừa lọc nhanh trong kho những sản phẩm phù hợp với yêu cầu của bạn:",
                    "Dạ có ngay cho bạn đây ạ! Mình đã tìm những mẫu phù hợp nhất với tiêu chí bạn vừa đưa:",
                    "Mình tìm được một số mẫu khá đúng gu bạn rồi nè. Bạn tham khảo thử nhé! ✨",
                    "Dạ Evern đã lọc xong rồi ạ. Đây là những mẫu phù hợp nhất với yêu cầu của bạn:",
                    "Có ngay bạn nhé! Bạn xem thử những mẫu này ạ:",
                    "Dạ mình tìm thấy rồi ạ. Bạn tham khảo thử nhé:"
                ]
            return random.choice(pool)

        pool = cls.OPENERS.get(mapped_key) or cls.OPENERS.get("find_product", ["Dạ Evern chào bạn nha! ✨"])
        return random.choice(pool)

    @classmethod
    def get_closing(cls, situation: str = "find_product") -> str:
        key_map = {
            "find_product": "find_product",
            "find_outfit": "find_outfit",
            "find_by_price": "find_by_price",
            "budget": "find_by_price",
            "find_by_style": "find_by_style",
            "style": "find_by_style",
            "find_by_color": "find_by_color",
            "color": "find_by_color",
            "find_by_size": "find_by_size",
            "size": "find_by_size",
            "recommend_gift": "recommend_gift",
            "gift": "recommend_gift",
            "formal_advice": "formal_advice",
            "formal": "formal_advice",
            "compare": "compare"
        }
        mapped_key = key_map.get(situation, "default")
        pool = cls.CLOSINGS_BY_SITUATION.get(mapped_key) or cls.CLOSINGS
        return random.choice(pool)

    @classmethod
    def detect_situation(
        cls,
        user_message: str = "",
        intent: str = "",
        entities: Optional[Dict[str, Any]] = None,
        products: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        entities = entities or {}
        products = products or []
        msg_l = (user_message or "").lower()

        # ----------------------------------------------------
        # Khi KHÔNG tìm thấy sản phẩm nào trong kho (Empty)
        # ----------------------------------------------------
        if not products:
            # 1. Kiểm tra câu hỏi quá mơ hồ, thiếu thông tin -> Cần hỏi lại (Clarify)
            has_specific_filter = bool(
                entities.get("category")
                or entities.get("sub_category")
                or entities.get("color")
                or entities.get("size")
                or entities.get("max_price")
                or entities.get("min_price")
                or entities.get("occasion")
                or entities.get("style")
                or entities.get("gender")
                or entities.get("product_code")
            )
            is_vague_query = (
                intent in ["ask_clarification", "other"]
                or (
                    not has_specific_filter
                    and any(w in msg_l for w in [
                        "tư vấn", "gợi ý đồ", "mua đồ", "chọn đồ", "có gì đẹp",
                        "đồ gì đẹp", "bán gì", "thời trang", "giúp mình", "giúp tôi",
                        "cần mua", "muốn mua"
                    ])
                )
            )
            if is_vague_query:
                return "ask_clarification"

            # 2. Không tìm thấy cho người lớn tuổi
            if any(w in msg_l for w in ["lớn tuổi", "trung niên", "người già", "đứng tuổi", "bố", "mẹ", "chú", "bác"]):
                return "empty_formal"

            # 3. Không tìm thấy khi mua quà tặng
            if any(w in msg_l for w in ["tặng quà", "mua quà", "quà tặng", "làm quà", "gift"]):
                return "empty_gift"

            # 4. Không tìm thấy do ngân sách (Budget)
            if (
                entities.get("max_price") is not None
                or entities.get("min_price") is not None
                or any(w in msg_l for w in ["dưới", "giá rẻ", "ngân sách", "tầm giá", "tiết kiệm", "hạt dẻ", "bao nhiêu k"])
            ):
                return "empty_budget"

            # 5. Không tìm thấy do kích cỡ (Size)
            if entities.get("size") or any(w in msg_l for w in ["size", "cỡ", "big size", "ngoại cỡ"]):
                return "empty_size"

            # 6. Không tìm thấy do màu sắc (Color)
            if entities.get("color"):
                return "empty_color"

            # 7. Không tìm thấy do phong cách (Style)
            if entities.get("style") or any(w in msg_l for w in ["phong cách", "style", "douyin", "y2k", "streetwear"]):
                return "empty_style"

            # 8. Mặc định là không tìm thấy sản phẩm
            return "empty_product"

        # ----------------------------------------------------
        # Khi CÓ sản phẩm gợi ý (Find)
        # ----------------------------------------------------
        # 1. Tư vấn quà tặng (Gift)
        gift_kws = [
            "tặng quà", "mua quà", "quà tặng", "tặng bạn", "tặng người yêu",
            "tặng bạn gái", "tặng bạn trai", "quà sinh nhật", "tặng vợ",
            "tặng chồng", "tặng mẹ", "tặng bố", "tặng sếp", "làm quà", "gift", "món quà"
        ]
        if any(w in msg_l for w in gift_kws):
            return "recommend_gift"

        # 2. Tư vấn người lớn tuổi / trung niên / trang trọng (Formal)
        formal_kws = [
            "lớn tuổi", "trung niên", "người già", "đứng tuổi", "u40", "u50", "u60", "tuổi trung niên",
            "nghiêm túc", "trang trọng", "gặp đối tác", "lịch thiệp"
        ]
        has_formal = any(w in msg_l for w in formal_kws) or bool(re.search(r"\b(?:bố|mẹ|chú|bác|ông|bà)\b", msg_l))
        if has_formal and not any(w in msg_l for w in ["sinh viên", "học sinh", "trẻ", "trẻ trung", "gen z", "tuổi teen", "teen"]):
            return "formal_advice"

        # 3. Tìm outfit / Phối đồ / Mặc gì đi đâu (Outfit)
        outfit_kws = [
            "mặc gì", "đi đâu", "đám cưới", "tiệc cưới", "đi tiệc", "dự tiệc", "dạ hội", "prom",
            "hẹn hò", "phối đồ", "mix đồ", "set đồ", "outfit", "lên đồ", "mặc với gì", "đi chơi",
            "đi làm", "công sở", "đi cafe", "đi cà phê", "đi du lịch", "đi biển", "khách sạn 5 sao",
            "chủ nhật", "cuối tuần", "không biết mặc gì", "mặc thế nào"
        ]
        is_outfit = (
            entities.get("is_outfit_query")
            or intent in ["recommendation", "style_office"]
            or bool(entities.get("occasion"))
            or any(w in msg_l for w in outfit_kws)
        )
        if is_outfit:
            return "find_outfit"

        # 4. Tìm theo ngân sách / Giá (Budget)
        budget_kws = [
            "dưới", "giá rẻ", "ngân sách", "tầm giá", "giá tốt", "hạt dẻ",
            "sinh viên", "tiết kiệm", "vừa túi tiền", "khoảng giá", "giá bao nhiêu"
        ]
        is_budget = (
            entities.get("max_price") is not None
            or entities.get("min_price") is not None
            or intent == "search_by_price"
            or any(w in msg_l for w in budget_kws)
        )
        if is_budget:
            return "find_by_price"

        # 5. Tìm theo phong cách (Style)
        style_kws = [
            "phong cách", "style", "douyin", "y2k", "streetwear", "hàn quốc", "korean", "vintage",
            "cá tính", "năng động", "thanh lịch", "minimal", "tối giản", "gen z", "trẻ trung"
        ]
        is_style = (
            bool(entities.get("style"))
            or intent == "style_young"
            or any(w in msg_l for w in style_kws)
        )
        if is_style:
            return "find_by_style"

        # 6. Tìm theo màu sắc (Color)
        if entities.get("color"):
            return "find_by_color"

        # 7. Tìm theo kích cỡ (Size)
        if entities.get("size") or any(w in msg_l for w in ["size", "kích cỡ", "big size", "ngoại cỡ", "form to", "form nhỏ"]):
            return "find_by_size"

        # 8. Mặc định: Tìm sản phẩm (Product)
        return "find_product"

    @classmethod
    def get_styling_tip(
        cls,
        user_message: str = "",
        entities: Optional[Dict[str, Any]] = None,
        products: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        entities = entities or {}
        products = products or []
        msg_l = (user_message or "").lower()
        style_key = (entities.get("style") or "").lower()
        occasion_key = (entities.get("occasion") or "").lower()
        weather_key = (entities.get("weather") or "").lower()
        cat_key = (entities.get("category") or "").lower()
        color_key = (entities.get("color") or "").lower()
        season_key = (entities.get("season") or "").lower()

        # Nhận diện giới tính
        gender = (entities.get("gender") or "").lower()
        if not gender:
            if any(w in msg_l for w in ["nam", "con trai", "bạn trai", "phái mạnh", "anh em", "chàng", "cho nam"]):
                gender = "nam"
            elif any(w in msg_l for w in ["nữ", "con gái", "bạn gái", "phái đẹp", "chị em", "nàng", "cho nữ"]):
                gender = "nữ"

        gender_dict = cls.STYLING_TIPS_MALE if gender == "nam" else (cls.STYLING_TIPS_FEMALE if gender == "nữ" else {})

        # 0. Ưu tiên xử lý đi concert / sơn tùng
        is_concert_tip = occasion_key == "concert" or any(w in msg_l for w in ["concert", "sơn tùng", "son tung", "liveshow", "quẩy"])
        if is_concert_tip:
            if gender == "nam":
                return "Đi concert quẩy hết mình thì ưu tiên số 1 là năng động và thoải mái: bạn nam hãy diện áo thun phông oversize graphic kết hợp cùng quần jeans ống suông hoặc jogger nỉ thể thao, khoác thêm áo khoác jeans/biker da và đôi sneaker êm chân để tha hồ bung xõa suốt đêm diễn nhé! 🔥"
            else:
                return "Đi concert của Sơn Tùng M-TP nàng cứ tự tin diện phong cách Y2K hoặc Streetwear cá tính: áo croptop hoặc áo thun oversize phối chân váy xếp ly/quần loe cạp cao, khoác thêm jacket denim/bomber và đôi sneaker đế êm để vừa quẩy tưng bừng vừa hack dáng cực đỉnh nhé! 🔥"

        # 0.1 Ưu tiên tư vấn theo số đo chiều cao & cân nặng nếu không có dịp cụ thể
        if entities.get("height") and entities.get("weight") and not occasion_key:
            h = entities.get("height")
            w = entities.get("weight")
            h_m = h / 100.0 if h > 3 else float(h)
            bmi = w / (h_m * h_m)
            if gender == "nam":
                if bmi < 19:
                    return f"Với bạn nam dáng người thanh mảnh (cao {h}cm, nặng {w}kg), bí quyết hack dáng là chọn áo phom suông nhẹ (regular fit) hoặc sơ vin vạt trước cùng quần jeans/khaki ống đứng cạp vừa để tạo cảm giác cơ thể đầy đặn, khỏe khoắn và đôi chân trông dài hơn."
                elif bmi <= 23.5:
                    return f"Với vóc dáng cân đối chuẩn phom (cao {h}cm, nặng {w}kg), bạn nam có thể thoải mái chọn áo phom suông hoặc regular phối cùng quần jeans ống suông/chinos để tôn trọn chiều cao và phong độ."
                else:
                    return f"Bạn nam nên ưu tiên áo phom suông tối màu kết hợp cùng quần ống đứng để tạo tỷ lệ cơ thể gọn gàng, thanh thoát và cao ráo hơn."
            elif gender == "nữ":
                if bmi < 19:
                    return f"Với vóc dáng mảnh mai (cao {h}cm, nặng {w}kg), nàng nên chọn áo có điểm nhấn như bèo nhún, tay phồng hoặc phối layer cùng chân váy chữ A, quần ống suông để tạo đường cong mềm mại."
                elif bmi <= 23.5:
                    return f"Với vóc dáng cân đối lý tưởng (cao {h}cm, nặng {w}kg), nàng có thể tự tin diện đầm midi chiết eo hoặc áo croptop phối cùng quần cạp cao để khoe trọn vòng eo và tỷ lệ cơ thể."
                else:
                    return f"Nàng nên ưu tiên các thiết kế đầm suông hoặc quần tây cạp cao tone màu trung tính để tạo hiệu ứng thon thả và thanh thoát."

        # 1. Khớp ưu tiên theo từ khóa xuất hiện trực tiếp trong câu người dùng
        # Nếu có gender, ưu tiên tìm trong gender_dict trước
        if gender_dict:
            sorted_gender_keys = sorted(gender_dict.keys(), key=len, reverse=True)
            for k in sorted_gender_keys:
                if k in msg_l:
                    return gender_dict[k]

        sorted_keys = sorted(cls.STYLING_TIPS.keys(), key=len, reverse=True)
        for k in sorted_keys:
            if k in msg_l:
                tip = cls.STYLING_TIPS[k]
                # Nếu khách là nam, ngăn chặn tuyệt đối các tip unisex lỡ chứa đầm/váy
                if gender == "nam" and any(bad in tip.lower() for bad in ["chân váy", "đầm", "váy"]):
                    if k in gender_dict:
                        return gender_dict[k]
                    if occasion_key and occasion_key in gender_dict:
                        return gender_dict[occasion_key]
                    if style_key and style_key in gender_dict:
                        return gender_dict[style_key]
                    return "Với nam giới, bạn nên ưu tiên sơ mi trơn hoặc polo dệt kim kết hợp cùng quần tây âu/chinos tối màu và giày sạch sẽ để tạo vẻ ngoài chỉn chu, đĩnh đạc."
                return tip

        # 2. Khớp theo dịp sử dụng (occasion)
        if occasion_key:
            if gender_dict and occasion_key in gender_dict:
                return gender_dict[occasion_key]
            if occasion_key in cls.STYLING_TIPS:
                tip = cls.STYLING_TIPS[occasion_key]
                if gender == "nam" and any(bad in tip.lower() for bad in ["chân váy", "đầm", "váy"]):
                    return "Buổi gặp gỡ hay sự kiện này, phái mạnh nên chọn trang phục gọn gàng, vừa vặn như áo sơ mi hoặc polo kết hợp cùng quần âu hoặc quần chinos tối màu."
                return tip

        # 3. Khớp theo phong cách (style)
        if style_key:
            if gender_dict and style_key in gender_dict:
                return gender_dict[style_key]
            if style_key in cls.STYLING_TIPS:
                tip = cls.STYLING_TIPS[style_key]
                if gender == "nam" and any(bad in tip.lower() for bad in ["chân váy", "đầm", "váy"]):
                    return "Phong cách này cho phái mạnh có thể phối áo sơ mi hoặc polo cùng quần âu, thắt lưng da và giày da hoặc sneaker tối giản."
                return tip

        # 4. Khớp theo thời tiết (weather)
        if weather_key and weather_key in cls.STYLING_TIPS:
            return cls.STYLING_TIPS[weather_key]

        # 4.1 Khớp theo mùa (season)
        if season_key:
            if gender_dict and season_key in gender_dict:
                return gender_dict[season_key]
            if season_key in cls.STYLING_TIPS:
                return cls.STYLING_TIPS[season_key]

        # 5. Khớp theo màu sắc (color)
        if color_key:
            color_match = f"màu {color_key}"
            if color_match in cls.STYLING_TIPS:
                return cls.STYLING_TIPS[color_match]

        # 6. Khớp theo danh mục sản phẩm hoặc tên sản phẩm gợi ý
        for p in products[:2]:
            p_name = (p.get("name") or "").lower()
            p_cat = (p.get("category") or "").lower()
            p_sub = (p.get("sub_category") or "").lower()
            if gender_dict:
                for k in sorted(gender_dict.keys(), key=len, reverse=True):
                    if k in p_name or k in p_sub or k in p_cat:
                        return gender_dict[k]
            for k in sorted_keys:
                if k in p_name or k in p_sub or k in p_cat:
                    tip = cls.STYLING_TIPS[k]
                    if gender == "nam" and any(bad in tip.lower() for bad in ["chân váy", "đầm", "váy"]):
                        continue
                    return tip

        if cat_key:
            if gender_dict and cat_key in gender_dict:
                return gender_dict[cat_key]
            if cat_key in cls.STYLING_TIPS:
                tip = cls.STYLING_TIPS[cat_key]
                if gender == "nam" and any(bad in tip.lower() for bad in ["chân váy", "đầm", "váy"]):
                    return "Mẫu sản phẩm này rất dễ phối cùng áo sơ mi hoặc quần âu để tạo nên tổng thể nam tính, đĩnh đạc."
                return tip

        if gender == "nam":
            return "Các item nam tính và lịch sự như áo sơ mi, polo dệt kim, quần âu hoặc jean tối màu rất dễ phối và giúp bạn luôn đĩnh đạc, tự tin trong mọi hoàn cảnh."
        elif gender == "nữ":
            return "Những item thanh lịch như đầm suông, sơ mi lụa, chân váy chữ A hoặc blazer rất dễ phối và tôn lên nét duyên dáng, nữ tính của bạn."

        return cls.STYLING_TIPS.get("basic", "Các item basic như áo thun, sơ mi, quần tây hoặc jean rất dễ phối và giúp bạn luôn chỉn chu trong mọi hoàn cảnh.")

    @classmethod
    def _compute_single_product_size(
        cls,
        p: Dict[str, Any],
        height: Optional[int],
        weight: Optional[int],
        hw_display: str
    ) -> Dict[str, Any]:
        """Tính toán size khuyến nghị và mẹo form dáng chi tiết cho một sản phẩm cụ thể."""
        p_name = p.get("name", "sản phẩm")
        p_code = p.get("code", "")
        code_str = f" (Mã: `{p_code}`)" if p_code else ""

        raw_sizes = p.get("sizes", [])
        if isinstance(raw_sizes, str):
            avail_sizes = [s.strip() for s in raw_sizes.split(",") if s.strip()]
        elif isinstance(raw_sizes, list):
            avail_sizes = list(raw_sizes)
        else:
            avail_sizes = []

        cat_full = ((p.get("category") or "") + " " + (p.get("sub_category") or "") + " " + p_name).lower()
        is_sleepwear = any(k in cat_full for k in ["ngủ", "pijama", "mặc nhà"])
        is_dress = any(k in cat_full for k in ["váy", "đầm", "dress", "skirt"])
        is_pants = any(k in cat_full for k in ["quần", "loe", "jean", "kaki", "tây", "short", "âu", "pant"])
        is_shoes = any(k in cat_full for k in ["giày", "giay", "sneaker", "loafer", "boot", "sandal", "oxford", "guốc", "cao gót"])
        is_accessory = any(k in cat_full for k in ["thắt lưng", "that lung", "dây nịt", "day nit", "ví", "cà vạt", "ca vat", "nón", "mũ", "kính", "túi"])
        has_letter = any(s.upper() in ["S", "M", "L", "XL", "2XL", "XXL", "3XL"] for s in avail_sizes)
        has_number = any(s.strip() in ["26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"] for s in avail_sizes)

        rec_size = "M"
        alt_note = ""
        item_icon = "👕"
        item_label = "Áo"

        if is_sleepwear or (is_dress and not is_pants):
            item_icon = "👗"
            item_label = "Váy / Đầm" if is_dress else "Đồ ngủ"
            if weight:
                if weight < 48:
                    rec_size = "S"
                    alt_note = "Size S ôm nhẹ nhàng thon thả, rủ mềm mại."
                elif 48 <= weight <= 53:
                    rec_size = "S"
                    alt_note = "Với vóc dáng thon thả của bạn, Size S sẽ ôm vừa vặn tôn trọn đường cong cơ thể; nếu thích mặc form suông rộng rãi thoải mái tối đa có thể chọn Size M nhé."
                elif 54 <= weight <= 60:
                    rec_size = "M"
                    alt_note = "Size M tôn dáng cân đối, nếu thích mặc rộng rãi có thể cân nhắc Size L."
                else:
                    rec_size = "L"
                    alt_note = "Size L hoặc XL giúp cử động thoải mái nhất."
            elif height:
                if height < 162:
                    rec_size = "S"
                elif height <= 168:
                    rec_size = "M"
                else:
                    rec_size = "L"
        elif is_pants:
            item_icon = "👖"
            item_label = "Quần"
            if has_letter and not has_number:
                if weight:
                    if weight < 47:
                        rec_size = "S"
                        alt_note = "Nếu bạn cao trên 1m62 và thích chiều dài ống phủ gót thoải mái thì có thể cân nhắc Size M nha."
                    elif 47 <= weight <= 53:
                        rec_size = "M"
                        alt_note = "Nếu bạn eo rất nhỏ (dưới 62cm) và thích mặc cạp ôm sát vòng eo thì có thể chọn Size S; còn Size M sẽ vừa vặn chuẩn chiều dài ống chạm gót hack dáng nhất."
                    elif 54 <= weight <= 60:
                        rec_size = "M hoặc L"
                        alt_note = "Với vóc dáng này, Size M sẽ vừa vặn cạp eo tôn dáng, còn Size L giúp phần mông và đùi cử động dễ chịu nhất khi ngồi hoặc di chuyển."
                    else:
                        rec_size = "XL"
                        alt_note = "Size XL đảm bảo form rộng rãi, thoải mái khi ngồi."
                elif height:
                    if height < 160:
                        rec_size = "S"
                    elif height <= 168:
                        rec_size = "M"
                    else:
                        rec_size = "L"
            else:
                # Quần size số (28, 29, 30, 31, 32...)
                if weight:
                    if weight < 52:
                        rec_size = "28 hoặc 29"
                        alt_note = "Vừa vặn vòng eo và ống quần gọn gàng."
                    elif 52 <= weight <= 60:
                        rec_size = "29 hoặc 30"
                        alt_note = "Với vóc dáng của bạn, Size 29 hoặc 30 là chuẩn đẹp nhất, vừa vặn cạp eo và chiều dài ống chạm mắt cá chân/phủ gót cực tôn dáng."
                    elif 61 <= weight <= 68:
                        rec_size = "31"
                        alt_note = "Cạp quần thoải mái, form suông đứng tôn dáng."
                    elif 69 <= weight <= 75:
                        rec_size = "32"
                        alt_note = "Đảm bảo thoải mái vòng bụng và đùi."
                    else:
                        rec_size = "33 - 34"
                        alt_note = "Form rộng rãi, không bị gò bó."
                elif height:
                    if height < 165:
                        rec_size = "29"
                    elif height <= 172:
                        rec_size = "30"
                    else:
                        rec_size = "31 - 32"
        elif is_shoes:
            item_icon = "👟"
            item_label = "Giày"
            if height:
                if height < 165:
                    rec_size = "39 hoặc 40"
                elif height <= 172:
                    rec_size = "40 hoặc 41"
                elif height <= 178:
                    rec_size = "41 hoặc 42"
                else:
                    rec_size = "42 hoặc 43"
            elif weight:
                if weight < 52:
                    rec_size = "39 hoặc 40"
                elif weight <= 63:
                    rec_size = "40 hoặc 41"
                elif weight <= 75:
                    rec_size = "41 hoặc 42"
                else:
                    rec_size = "42 hoặc 43"
            else:
                rec_size = "40 hoặc 41"
            alt_note = "Nên chọn đúng size vừa chân để di chuyển êm ái nhất; nếu mu bàn chân dày hoặc bề ngang to thì có thể cân nhắc tăng thêm 1 size nha."
        elif is_accessory:
            item_icon = "✨"
            item_label = "Phụ kiện"
            rec_size = "Freesize (Tiêu chuẩn)"
            alt_note = "Kích thước tiêu chuẩn dễ dàng tùy chỉnh hoặc điều chỉnh theo từng vóc dáng."
        else:
            # Áo sơ mi / polo / thun / khoác
            item_icon = "👕"
            item_label = "Áo"
            if weight:
                if weight < 53:
                    rec_size = "S"
                    alt_note = "Nếu bạn thích mặc phong cách rộng rãi hoặc oversize thì có thể chọn Size M nhé."
                elif 53 <= weight <= 62:
                    rec_size = "M"
                    alt_note = "Với vóc dáng của bạn, Size M sẽ ôm vừa vặn tôn bờ vai và ngực; nếu thích form rộng thoải mái/oversize thì tăng lên Size L nha."
                elif 63 <= weight <= 72:
                    rec_size = "L"
                    alt_note = "Size L tôn dáng cân đối, cử động thoải mái."
                elif 73 <= weight <= 82:
                    rec_size = "XL"
                    alt_note = "Size XL vừa vặn vòng ngực và bắp tay."
                else:
                    rec_size = "2XL"
                    alt_note = "Size 2XL hoặc 3XL giúp cử động thoải mái nhất."
            elif height:
                if height < 165:
                    rec_size = "S"
                elif height <= 172:
                    rec_size = "M"
                elif height <= 178:
                    rec_size = "L"
                else:
                    rec_size = "XL"

        avail_str = ", ".join(avail_sizes) if avail_sizes else "Đầy đủ size"
        return {
            "name": p_name,
            "code": p_code,
            "code_str": code_str,
            "icon": item_icon,
            "label": item_label,
            "rec_size": rec_size,
            "alt_note": alt_note,
            "avail_str": avail_str,
            "is_pants": is_pants,
            "is_dress": is_dress,
            "is_sleepwear": is_sleepwear,
            "is_shoes": is_shoes,
            "is_accessory": is_accessory
        }

    @classmethod
    def _generate_empty_response(
        cls,
        user_msg_lower: str,
        entities: Dict[str, Any],
        situation: str = "empty_product"
    ) -> str:
        cat = entities.get("category")
        mat = entities.get("material")
        col = entities.get("color")
        sz = entities.get("size")
        max_p = entities.get("max_price")
        kw_list = entities.get("keywords", [])
        kw_str = " ".join(kw_list) if kw_list else ""

        category_highlights = {
            "Áo khoác": (
                "• **Áo khoác Blazer:** Thiết kế may đo phom suông thanh lịch, tôn dáng chỉn chu đi làm hay dạo phố.\n"
                "• **Áo khoác Jeans đen chỉ nổi:** Phong cách Douyin/Streetwear trẻ trung, cá tính.\n"
                "• **Áo khoác Hoodie nỉ có mũ & Bomber thể thao:** Năng động, ấm áp và thoải mái.\n"
                "• **Áo măng tô mùa đông:** Phom dài sang trọng, cản gió giữ ấm cực tốt."
            ),
            "Áo sơ mi": (
                "• **Áo sơ mi công sở cao cấp:** Chống nhăn, phom đứng chuẩn chỉn chu.\n"
                "• **Áo sơ mi lụa dệt Jacquard:** Mềm mịn, thoáng mát và sang trọng.\n"
                "• **Áo sơ mi linen:** Nhẹ nhàng, phong trần và thoáng mát mùa hè."
            ),
            "Áo polo": (
                "• **Áo polo cotton dệt tổ ong:** Thoáng khí, co giãn 4 chiều, thấm hút mồ hôi.\n"
                "• **Áo polo dệt kim retro:** Thanh lịch, tôn vóc dáng nam tính và lịch lãm."
            ),
            "Áo thun": (
                "• **Áo thun basic cotton 100%:** Mềm mại, bền màu, dễ phối đồ hàng ngày.\n"
                "• **Áo thun oversize streetwear:** Rộng rãi, trẻ trung, đậm phong cách Douyin/Hàn Quốc."
            ),
            "Quần tây": (
                "• **Quần tây âu đứng phom:** Vải tuyết mưa mềm mại, chống nhăn, tôn chiều cao.\n"
                "• **Quần khaki / chinos & Quần short:** Năng động, thoáng mát, chuẩn smart-casual."
            ),
            "Quần jean": (
                "• **Quần jeans ống suông vintage:** Phom rộng thoải mái, hack dáng đôi chân.\n"
                "• **Quần jeans đen chỉ nổi & Jeans rách gối:** Cá tính, thời thượng."
            ),
            "Quần loe": (
                "• **Quần loe nhẹ phong cách Y2K:** Cạp cao ôm eo, loe nhẹ phần gấu giúp đôi chân thon dài miên man."
            ),
            "Váy & Đầm": (
                "• **Đầm dạ hội / Đầm tiệc cưới:** Lộng lẫy, kiêu sa, tôn đường cong quyến rũ.\n"
                "• **Chân váy chữ A & Chân váy xếp ly tennis:** Trẻ trung, dễ phối cùng sơ mi hay áo thun.\n"
                "• **Váy ngủ & Pijama lụa satin:** Mềm mượt, quý phái, êm ái khi mặc ở nhà."
            ),
            "Phụ kiện": (
                "• **Giày sneaker retro da thật & Giày tây Oxford:** Êm chân, bền bỉ, phong độ.\n"
                "• **Thắt lưng da bò nguyên tấm & Ví da nam:** Sang trọng, đẳng cấp.\n"
                "• **Cà vạt lụa dệt, Kính mát titanium:** Điểm nhấn tinh tế cho trang phục."
            )
        }

        # Làm sạch chuỗi đặc tả tránh rò rỉ từ đệm / từ nối / câu lệnh của người dùng
        spec = mat or kw_str
        if spec:
            garbage_words = [
                "tư vấn", "gợi ý", "chỉnh sửa", "thêm", "chọn", "tìm", "mua", "xem", "hỏi", "cho tôi", "cho em", "cho mình",
                "1 số", "một số", "vài", "chiếc", "cái", "mẫu", "số", "mặc", "vào",
                "mùa hè", "mùa đông", "mùa thu", "mùa xuân", "4 mùa", "bốn mùa", "hè", "đông", "thu", "xuân",
                "này", "kia", "đó", "nè", "nhé", "ạ", "ơi"
            ]
            for gw in garbage_words:
                spec = re.sub(rf"\b{re.escape(gw)}\b", "", spec, flags=re.IGNORECASE)
            spec = " ".join(spec.split()).strip()

        # Tình huống 1: Người dùng tìm chất liệu hoặc chi tiết cụ thể mà shop chưa có (VD: áo khoác lông cừu)
        if cat and spec:
            cat_hl = category_highlights.get(cat, "")
            hl_section = f"\n\nTuy nhiên, dòng **{cat}** của showroom hiện đang có sẵn các thiết kế cực kỳ thời thượng và được yêu thích:\n{cat_hl}" if cat_hl else ""
            return (
                f"Dạ rất tiếc hiện tại trong kho của Evern Fashion **chưa có mẫu {cat.lower()} {spec}** theo yêu cầu của bạn rồi ạ! 🥺{hl_section}\n\n"
                f"Bạn có muốn tham khảo các mẫu {cat.lower()} sẵn có này của shop không nè? Evern Stylist luôn sẵn sàng hỗ trợ bạn nhé! ❤️"
            )

        # Tình huống 1.5: Người dùng tìm theo mùa nhưng tạm chưa có sản phẩm khớp
        season_val = (entities.get("season") or "").lower()
        if not season_val:
            for s in ["mùa xuân", "mùa hè", "mùa thu", "mùa đông", "bốn mùa", "4 mùa"]:
                if s in user_msg_lower:
                    season_val = s
                    break

        if cat and season_val:
            cat_hl = category_highlights.get(cat, "")
            hl_section = f"\n\nTuy nhiên, dòng **{cat}** của showroom hiện đang có sẵn các thiết kế cực kỳ thời thượng:\n{cat_hl}" if cat_hl else ""
            return (
                f"Dạ rất tiếc hiện tại trong kho của Evern Fashion **chưa có mẫu {cat.lower()} dành cho {season_val}** theo yêu cầu của bạn rồi ạ! 🥺{hl_section}\n\n"
                f"Bạn có muốn tham khảo các mẫu {cat.lower()} sẵn có này của shop không nè? Evern Stylist luôn sẵn sàng hỗ trợ bạn nhé! ❤️"
            )

        # Tình huống 2: Người dùng tìm màu sắc chưa có trong kho
        if cat and col:
            return (
                f"Dạ rất tiếc hiện tại trong kho của Evern Fashion **chưa có mẫu {cat.lower()} màu {col}** rồi bạn ơi! 🥺\n\n"
                f"Bộ sưu tập **{cat}** của showroom hiện đang có sẵn các tone màu sang trọng, hiện đại và rất tôn da như: **Trắng ngọc, Đen huyền bí, Xanh navy, Be và Xám ghi**...\n\n"
                f"Bạn có muốn tham khảo bảng màu sẵn có của các mẫu {cat.lower()} tại showroom không nè? ✨"
            )

        # Tình huống 3: Không có sản phẩm trong mức ngân sách
        if situation == "empty_budget" or max_p:
            cat_str = f"mẫu {cat.lower()}" if cat else "sản phẩm"
            budget_str = f" với mức giá dưới {max_p:,}đ" if max_p else " trong khoảng giá này"
            return (
                f"Dạ rất tiếc hiện tại trong kho của Evern Fashion **chưa có {cat_str}{budget_str}** rồi bạn ơi! 🥺\n\n"
                f"Các thiết kế thời trang của Evern tập trung vào phân khúc chất lượng cao, bền đẹp và đứng phom chuẩn với mức giá ưu đãi từ 190,000đ - 650,000đ kèm nhiều quyền lợi tích điểm thành viên.\n\n"
                f"Bạn có muốn tham khảo những mẫu {cat.lower() if cat else 'thời trang'} đang có ưu đãi tốt nhất của showroom không nè? 💫"
            )

        # Tình huống 4: Không có kích cỡ yêu cầu
        if situation == "empty_size" or sz:
            cat_str = f"dòng {cat.lower()}" if cat else "sản phẩm"
            sz_str = f"size {sz}" if sz else "kích cỡ bạn yêu cầu"
            return (
                f"Dạ rất tiếc hiện tại {cat_str} của Evern Fashion **tạm thời chưa có sẵn {sz_str}** trong kho đợt này rồi bạn ơi! 🥺\n\n"
                f"Showroom hiện sẵn các size từ **S đến XL** (hoặc size quần **28 đến 34**) với phom dáng chuẩn mực và độ co giãn nhẹ. "
                f"Bạn có thể gửi cho mình số đo chiều cao và cân nặng để mình kiểm tra xem có mẫu nào phom suông mặc vừa vặn thoải mái không nhé! ❤️"
            )

        # Tình huống 5: Quà tặng
        if situation == "empty_gift":
            return (
                "Dạ rất tiếc hiện tại chưa tìm thấy mẫu đáp ứng đầy đủ yêu cầu làm quà tặng bạn vừa nêu ạ! 🥺\n\n"
                "Khi chọn mua làm quà tặng, các item basic cao cấp như áo polo dệt kim, sơ mi trắng công sở hoặc ví da/thắt lưng da bò tại Evern là những lựa chọn an toàn và tinh tế nhất vì rất dễ mặc và ít kén người dùng.\n\n"
                "Bạn có muốn mình gợi ý những set quà tặng thời trang được yêu thích nhất tại showroom không ạ? 🎁"
            )

        # Tình huống 6: Người lớn tuổi
        if situation == "empty_formal":
            return (
                "Dạ rất tiếc hiện tại showroom chưa có mẫu đúng hoàn toàn với tiêu chí này cho độ tuổi trung niên ạ! 🥺\n\n"
                "Cô/chú có thể tham khảo một số thiết kế áo polo dệt kim cổ bẻ, áo sơ mi cộc tay hoặc quần âu ống suông cạp cao tại showroom. Các mẫu này đều có chất vải mềm mát, co giãn nhẹ và phom đứng rất lịch thiệp ạ. ✨"
            )

        # Tình huống 7: Mặc định chung khi sản phẩm không có trong CSDL
        item_label = f"mẫu {cat.lower()}" if cat else "những sản phẩm này"
        return (
            f"Dạ rất tiếc hiện tại trong kho dữ liệu của Evern Fashion **chưa có {item_label}** theo yêu cầu của bạn rồi ạ! 🥺\n\n"
            f"Showroom của tụi mình hiện đang chuyên về các dòng thời trang thiết kế cao cấp cho cả nam và nữ:\n"
            f"👔 **1. Áo thời trang:** Áo sơ mi công sở/lụa, Áo polo dệt kim/cotton, Áo thun basic/oversize, Áo khoác blazer, bomber, măng tô, hoodie nỉ...\n"
            f"👖 **2. Các dòng quần:** Quần tây âu đứng phom, Quần jeans ống suông/loe/baggy, Quần khaki, Quần short...\n"
            f"👗 **3. Váy & Đầm thiết kế:** Đầm dạ hội, đầm tiệc cưới, chân váy chữ A/xếp ly, váy ngủ lụa satin...\n"
            f"👟 **4. Giày da & Phụ kiện:** Giày sneaker retro, Giày tây Oxford/Derby, Thắt lưng da bò, Ví da nam, Cà vạt lụa, Kính mát...\n\n"
            f"Bạn có muốn tham khảo các mẫu trang phục sẵn có tại shop không nè? Evern Stylist luôn sẵn sàng tư vấn cho bạn! ❤️"
        )


    @classmethod
    def generate(
        cls,
        intent: str,
        entities: Dict[str, Any],
        products: List[Dict[str, Any]],
        db_info: Optional[Dict[str, Any]] = None,
        default_dataset_reply: str = "",
        knowledge_context: str = "",
        user_message: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        db_info = db_info or {} # Đảm bảo biến thông tin phụ từ CSDL luôn là dict

        # Xử lý khi khách hỏi giá sản phẩm cụ thể
        if intent == "product_price":
            p = db_info.get("product") if db_info else None
            if not p and products:
                p = products[0]
            if p:
                name = p.get("name") or "Sản phẩm Evern"
                code = p.get("code") or "N/A"
                price = p.get("price") or 0
                old_price = p.get("old_price") or price
                discount_pct = p.get("discount_pct") or (int((old_price - price) / old_price * 100) if old_price and old_price > price else 0)
                material = p.get("material") or "Denim/Cotton cao cấp"
                fit = p.get("fit") or "Oversize / Form chuẩn tôn dáng"
                points = p.get("points") or int(price / 1000)
                sizes = p.get("sizes") or []
                sizes_str = ", ".join(sizes) if isinstance(sizes, list) else str(sizes or "S, M, L, XL")

                return (
                    f"Dạ mẫu **{name}** (Mã: `{code}`) hiện đang có giá ưu đãi cực tốt tại Evern nè: ✨\n\n"
                    f"• **Giá bán ưu đãi:** **{price:,}đ** (Giá gốc: {old_price:,}đ - Giảm {discount_pct}%)\n"
                    f"• **Chất liệu:** {material} | **Form dáng:** {fit}\n"
                    f"• **Tích lũy:** Mua sản phẩm này bạn được cộng ngay **{points:,} điểm** thành viên.\n\n"
                    f"Mẫu này hiện đang có các size: **{sizes_str}**. Bạn đang tìm size nào để mình kiểm tra giữ hàng cho bạn nhé? ❤️"
                )

        # Xử lý khi khách hỏi tình trạng còn hàng và size
        if intent == "product_stock":
            p = db_info.get("product") if db_info else None
            if not p and products:
                p = products[0]
            if p:
                name = p.get("name") or "Sản phẩm Evern"
                code = p.get("code") or "N/A"
                stock = p.get("stock") or 50
                stock_msg = db_info.get("stock_status") or f"Còn {stock} sản phẩm sẵn sàng giao ngay"
                color = p.get("color") or "Nhiều màu"
                sizes = p.get("sizes") or []
                sizes_str = ", ".join(sizes) if isinstance(sizes, list) else str(sizes or "S, M, L, XL")

                return (
                    f"Dạ shop vừa kiểm tra kho sản phẩm **{name}** (Mã: `{code}`) cho bạn rồi đây ạ! ✨\n\n"
                    f"• **Tình trạng:** {stock_msg}\n"
                    f"• **Màu sắc sẵn có:** {color}\n"
                    f"• **Bảng size:** **{sizes_str}**\n\n"
                    f"Sản phẩm đang bán rất chạy tại showroom. Bạn muốn mình hỗ trợ giữ size hoặc hướng dẫn đặt giao ngay không nè?"
                )

        # Xử lý khi khách yêu cầu tư vấn chi tiết về 1 sản phẩm cụ thể
        if intent == "product_detail":
            p = db_info.get("product") if db_info else None
            if not p and products:
                p = products[0]
            if p:
                name = p.get("name", "Sản phẩm Evern")
                code = p.get("code", "N/A")
                price = p.get("price", 0)
                old_price = p.get("old_price") or price
                discount_pct = p.get("discount_pct") or (int((old_price - price) / old_price * 100) if old_price > price else 0)
                material = p.get("material") or "Denim/Cotton cao cấp bền đẹp"
                fit = p.get("fit") or "Form dáng chuẩn tôn dáng"
                collar = p.get("collar")
                sleeve = p.get("sleeve")
                color = p.get("color") or "Nhiều màu"
                desc = (p.get("description") or "").strip()
                sizes = p.get("sizes", [])
                sizes_str = ", ".join(sizes) if isinstance(sizes, list) else str(sizes)
                stock = p.get("stock", 50)
                points = p.get("points") or int(price / 1000)

                cat_lower = (p.get("category") or "").lower()
                subcat_lower = (p.get("sub_category") or "").lower()
                name_lower = name.lower()

                # Stylist tip riêng cho danh mục sản phẩm
                stylist_tip = ""
                if "loe" in name_lower or "loe" in cat_lower or "douyin" in name_lower:
                    stylist_tip = "Thiết kế quần ống loe cạp thấp phong cách Y2K/Douyin này cực kỳ hack chân dài! Bạn có thể mix cùng áo baby tee ôm, áo croptop, hai dây hoặc blazer oversize và đi kèm sneaker đế bánh mì hoặc boots để hoàn thiện phong cách cá tính."
                else:
                    stylist_tip = cls.get_styling_tip(user_message=user_message, entities=entities, products=[p])

                is_pants = "quần" in cat_lower or "quần" in subcat_lower or "quần" in name_lower or "loe" in cat_lower or "loe" in name_lower
                is_footwear_acc = any(k in cat_lower or k in subcat_lower or k in name_lower for k in ["giày", "sneaker", "thắt lưng", "ví", "kính", "cà vạt", "phụ kiện"])

                lines = [
                    f"Dạ Evern Stylist xin gửi bạn thông tin tư vấn chi tiết về mẫu **{name}** (Mã: `{code}`) nhé! ✨\n",
                    f"💎 **Đặc điểm & Thiết kế nổi bật:**",
                    f"• **Chất liệu:** {material} - bề mặt mềm mịn, thoáng khí tối đa, hạn chế nhăn nhàu khi vận động cả ngày.",
                    f"• **Form dáng:** {fit} tôn vóc dáng thon gọn, thanh thoát nhưng vẫn đảm bảo cử động thoải mái."
                ]

                if is_pants:
                    if "loe" in name_lower or "loe" in cat_lower:
                        lines.append("• **Kiểu dáng & Chiều dài:** Dáng quần ống loe hack chân dài, cạp thời thượng chuẩn phong cách Y2K và Douyin hot trend.")
                    elif "short" in subcat_lower or "short" in name_lower:
                        lines.append("• **Kiểu dáng & Chiều dài:** Dáng quần short ngang gối năng động, thoáng mát.")
                    elif "jean" in subcat_lower or "jean" in name_lower:
                        lines.append("• **Kiểu dáng & Chiều dài:** Dáng quần jeans ống suông/đứng dài chuẩn phom hack dáng.")
                    else:
                        lines.append("• **Kiểu dáng & Chiều dài:** Dáng quần tây dài chuẩn mực, cạp tăng đơ thông minh ôm vừa vặn và tôn chiều cao.")
                elif not is_footwear_acc:
                    if collar and str(collar).strip().lower() not in ["không", "none", "n/a", ""]:
                        lines.append(f"• **Thiết kế cổ áo:** {collar}")
                    if sleeve and str(sleeve).strip().lower() not in ["không", "none", "n/a", ""]:
                        lines.append(f"• **Kiểu tay áo:** {sleeve}")

                lines.append(f"• **Màu sắc:** {color} trẻ trung, tôn tone da.")
                if desc:
                    lines.append(f"• **Mô tả chi tiết:** {desc}")

                lines.extend([
                    f"\n💰 **Giá bán & Ưu đãi thành viên:**",
                    f"• **Giá ưu đãi hôm nay:** **{price:,}đ** (Giá gốc: ~~{old_price:,}đ~~ - Giảm {discount_pct}%)",
                    f"• **Tích lũy:** Tặng ngay **+{points:,} điểm** thành viên Evern Club.",
                    f"\n📏 **Bảng size & Tình trạng kho:**",
                    f"• Hiện showroom sẵn các size: **{sizes_str}** (Còn {stock} sản phẩm sẵn sàng giao ngay).",
                    f"\n💡 **Gợi ý phối đồ chuẩn gu từ Stylist:**\n{stylist_tip}",
                    f"\n👉 Bạn cho mình xin **chiều cao & cân nặng** để mình chọn size vừa vặn và tôn dáng nhất cho bạn nhé! ❤️ Hoặc bạn có thể bấm **'Thêm vào giỏ'** ở khung sản phẩm bên dưới để giữ hàng nha."
                ])
                return "\n".join(lines)

        # Hướng dẫn đặt hàng và thanh toán nhanh chóng
        if intent == "order":
            lines = [
                "Dạ Evern xin hướng dẫn bạn đặt hàng và thanh toán nhanh chóng trên website nhé! ✨\n",
                "📦 **Các bước đặt hàng và thanh toán cực kỳ đơn giản:**",
                "1. Bạn chọn mẫu sản phẩm và size ưng ý ở danh sách bên dưới, bấm **'Thêm vào giỏ'** hoặc **'Xem chi tiết'**.",
                "2. Bấm vào biểu tượng **Giỏ hàng** ở góc trên bên phải màn hình.",
                "3. Nhấn **'Tiến hành thanh toán'**, điền thông tin địa chỉ và chọn hình thức thanh toán (COD khi nhận hàng hoặc chuyển khoản).",
                "4. Xác nhận đơn hàng là bên mình sẽ đóng gói gửi ngay cho bạn nha!\n"
            ]

            # Nếu có sản phẩm đi kèm, hiển thị nhanh danh sách để khách chọn
            if products:
                lines.append("🛍️ **Các sản phẩm bạn vừa yêu cầu đang có sẵn để bạn chọn size và đặt hàng:**")
                for idx, p in enumerate(products[:4], 1):
                    sizes_text = ", ".join(p.get('sizes', [])) if isinstance(p.get('sizes'), list) else str(p.get('sizes'))
                    lines.append(
                        f"{idx}. **{p['name']}** (Mã: {p.get('code', 'EV')}) - Giá: **{p['price']:,}đ** | Size: **{sizes_text}**"
                    )
                lines.append("\n💡 Mẹo từ Stylist: Nếu bạn muốn chọn size vừa vặn nhất cho áo và quần trước khi chốt đơn, cứ nhắn chiều cao và cân nặng để mình tư vấn nhé! ❤️")
            else:
                lines.append("💡 Mẹo nhỏ: Bạn có thể gửi thêm chiều cao và cân nặng để mình tư vấn size vừa chuẩn trước khi bạn chốt đơn nhé! ❤️")

            return "\n".join(lines)

        user_msg_lower = (user_message or "").lower()
        situation = cls.detect_situation(
            user_message=user_msg_lower,
            intent=intent,
            entities=entities,
            products=products
        )

        # Xử lý khi KHÔNG tìm thấy sản phẩm trong kho CSDL (hoặc khi intent == "empty_product")
        if not products and (intent == "empty_product" or situation.startswith("empty_")):
            return cls._generate_empty_response(user_msg_lower=user_msg_lower, entities=entities, situation=situation)

        # Nếu tình huống là thiếu thông tin / câu hỏi chung chung cần hỏi làm rõ
        if situation == "ask_clarification" and not products and intent not in ["order", "size_guide", "product_price", "product_stock", "goodbye"]:
            is_simple_greeting = any(w in user_msg_lower for w in ["xin chào", "chào bạn", "hello", "hi shop", "chào shop", "alo shop"]) and len(user_msg_lower.split()) <= 3
            if not is_simple_greeting:
                return cls.get_opener("ask_clarification")

        # Xử lý tìm kiếm sản phẩm hoặc gợi ý trang phục (ngoại trừ tư vấn size, chi tiết, đơn hàng...)
        if (intent in ["search_product", "search_by_price", "search_by_category", "recommendation", "style_young", "style_office", "men_fashion", "ask_clarification"] or products) and intent not in ["order", "size_guide", "product_price", "product_stock", "product_detail"]:

            if products:
                # Nhận diện dịp mặc đặc biệt từ câu hỏi
                occasion_kw = entities.get("occasion") or ""
                if not occasion_kw:
                    for occ in ["đám cưới", "tiệc cưới", "khách sạn 5 sao", "5 sao", "đi chơi", "dạo phố", "cafe", "hẹn hò", "đi làm", "công sở", "dự tiệc", "du lịch", "concert"]:
                        if occ in user_msg_lower:
                            occasion_kw = occ
                            break

                is_concert = occasion_kw == "concert" or any(w in user_msg_lower for w in ["concert", "sơn tùng", "son tung", "liveshow", "show ca nhạc", "festival âm nhạc", "quẩy"])

                # Tạo lời mở đầu phong cách Stylist tự nhiên bám sát tình huống hội thoại
                is_follow_up = False
                prev_prod = None
                if context and context.get("last_products"):
                    prev_prod = context["last_products"][0]
                    if any(w in user_msg_lower for w in ["thêm", "cả", "phối", "mix", "kèm", "cùng", "nữa", "áo nữa", "quần nữa"]):
                        is_follow_up = True

                season_val = (entities.get("season") or "").lower()
                is_four_seasons = season_val in ["bốn mùa", "4 mùa"] or any(w in user_msg_lower for w in ["4 mùa", "bốn mùa"]) or (all(s in user_msg_lower for s in ["xuân", "hè", "thu", "đông"]))

                if occasion_kw in ["đám cưới", "tiệc cưới", "khách sạn 5 sao", "5 sao"]:
                    if entities.get("gender") == "nam" or any(w in user_msg_lower for w in ["nam", "con trai", "bạn trai", "anh"]):
                        opener = "Dạ Evern xin chúc mừng bạn nha! ✨ Tham dự tiệc cưới trang trọng cần vẻ ngoài lịch lãm, phong độ và chỉn chu. Phái mạnh nên ưu tiên áo sơ mi cao cấp phối cùng quần tây âu đứng phom hoặc bộ suit/blazer sang trọng, đi giày da bóng hoặc loafer để vừa tôn trọng ngày vui vừa toát lên vẻ đĩnh đạc nhé:"
                    else:
                        opener = "Dạ Evern xin chúc mừng bạn và bạn thân nha! ✨ Tham dự tiệc cưới tại khách sạn 5 sao cần vẻ ngoài sang trọng, chỉn chu nhưng theo quy tắc dress code lịch thiệp: không mặc đầm trắng toàn thân (để nhường trọn sự nổi bật cho cô dâu) và tránh trang phục ngủ/quá hở hang. Dưới đây là các mẫu đầm dạ tiệc cao cấp cực kỳ thanh lịch và tôn dáng dành riêng cho bạn nè:"
                elif is_concert:
                    is_st = any(w in user_msg_lower for w in ["sơn tùng", "son tung", "m-tp", "sky"])
                    st_mention = " của Sếp Sơn Tùng M-TP" if is_st else ""
                    if entities.get("gender") == "nam" or any(w in user_msg_lower for w in ["nam", "con trai", "bạn trai", "anh"]):
                        opener = f"Chào bạn nhé! 🔥 Đi concert{st_mention} thì outfit nhất định phải thật 'cháy', đậm chất streetwear cá tính và thoải mái để quẩy nhiệt tình suốt đêm nhạc! Evern Stylist gợi ý ngay cho bạn set đồ cực chất và phong độ dưới đây nè: ✨"
                    else:
                        opener = f"Chào nàng nha! 🔥 Đi concert{st_mention} thì outfit phải cực kỳ 'cháy', vừa cá tính, nổi bật vừa thoải mái để tha hồ quẩy tưng bừng cùng thần tượng! Evern Stylist gợi ý ngay cho bạn set đồ trendy và hack dáng dưới đây nè: ✨"
                elif is_four_seasons:
                    opener = random.choice(cls.OPENERS["find_outfit_four_seasons"])
                elif season_val in ["mùa hè", "mùa đông", "mùa thu", "mùa xuân"]:
                    if season_val == "mùa hè":
                        opener = random.choice(cls.OPENERS["find_outfit_summer"])
                    elif season_val == "mùa đông":
                        opener = random.choice(cls.OPENERS["find_outfit_winter"])
                    elif season_val == "mùa thu":
                        opener = random.choice(cls.OPENERS["find_outfit_fall"])
                    elif season_val == "mùa xuân":
                        opener = random.choice(cls.OPENERS["find_outfit_spring"])
                elif is_follow_up and prev_prod:
                    prev_name = prev_prod.get("name", "sản phẩm")
                    if " - " in prev_name:
                        prev_name = prev_name.split(" - ")[0]
                    style_mention = f" phong cách {entities['style'].title()}" if entities.get("style") else ""
                    cat_mention = entities.get("category") or "áo"
                    opener = f"Dạ để phối cùng chiếc **{prev_name}** cực tôn dáng vừa rồi, Evern Stylist gợi ý ngay cho bạn những mẫu {cat_mention}{style_mention} chuẩn gu và thời thượng dưới đây nhé: ✨"
                elif not occasion_kw and (entities.get("height") or entities.get("weight") or entities.get("age")):
                    height_val = entities.get("height")
                    weight_val = entities.get("weight")
                    age_val = entities.get("age")
                    gender_val = entities.get("gender")

                    greeting_target = "bạn"
                    if gender_val == "nam":
                        greeting_target = f"bạn nam{' ' + str(age_val) + ' tuổi' if age_val else ''}"
                    elif gender_val == "nữ":
                        greeting_target = f"bạn nữ{' ' + str(age_val) + ' tuổi' if age_val else ''}"
                    elif age_val:
                        greeting_target = f"bạn {age_val} tuổi"

                    stats_desc = []
                    if height_val:
                        stats_desc.append(f"cao {height_val}cm" if height_val > 3 else f"cao {height_val}m")
                    if weight_val:
                        stats_desc.append(f"nặng {weight_val}kg")
                    stats_str = ", ".join(stats_desc)

                    body_fit_advice = ""
                    if height_val and weight_val:
                        h_m = height_val / 100.0 if height_val > 3 else float(height_val)
                        bmi = weight_val / (h_m * h_m)
                        if bmi < 19:
                            body_fit_advice = "Với vóc dáng tương đối thanh mảnh, Evern Stylist khuyên bạn nên ưu tiên những thiết kế form suông (regular fit) hoặc oversize nhẹ để vừa 'hack dáng' cao ráo, vừa giúp vóc dáng trông đầy đặn và khỏe khoắn hơn."
                        elif bmi <= 23.5:
                            body_fit_advice = "Tỷ lệ cơ thể của bạn rất cân đối và chuẩn dáng, cực kỳ dễ diện đồ từ phom vừa vặn (regular fit) đến form rộng hiện đại."
                        else:
                            body_fit_advice = "Với vóc dáng đậm người khỏe khoắn, bạn nên ưu tiên các thiết kế phom đứng hoặc suông nhẹ với tone màu trung tính để tạo cảm giác thon gọn và thanh thoát."

                    wants_top_bottom = "quần và áo" in user_msg_lower or "áo và quần" in user_msg_lower or (set(entities.get("categories") or []) == {"áo", "quần"})
                    item_desc = "set quần và áo cực chuẩn phom và tôn dáng" if wants_top_bottom else "set trang phục cực kỳ tôn dáng và phù hợp"

                    stats_part = f" Với số đo {stats_str}. " if stats_str else " "
                    advice_part = f"{body_fit_advice} " if body_fit_advice else ""
                    opener = f"Chào {greeting_target} nha! 👋{stats_part}{advice_part}Evern Stylist gợi ý ngay cho bạn {item_desc} dưới đây nhé: ✨"
                elif situation == "find_outfit" and not occasion_kw:
                    opener = cls.get_opener("find_outfit_general")
                else:
                    opener = cls.get_opener(situation, user_message=user_msg_lower, entities=entities)

                lines = [f"{opener}\n"]

                # Kiểm tra xem danh sách có phối nhiều thể loại (Áo + Quần + Giày/Phụ kiện) không
                def get_broad_category(item):
                    c = (item.get("category") or "").lower()
                    sc = (item.get("sub_category") or "").lower()
                    if any(w in c or w in sc for w in ["áo", "shirt", "polo", "blazer", "khoác"]):
                        return "top"
                    if any(w in c or w in sc for w in ["quần", "short", "jean", "âu", "kaki", "loe"]):
                        return "bottom"
                    if any(w in c or w in sc for w in ["váy", "đầm", "skirt", "dress"]):
                        return "dress"
                    if any(w in c or w in sc for w in ["giày", "sneaker"]):
                        return "footwear"
                    if any(w in c or w in sc for w in ["phụ kiện", "kính", "thắt lưng", "ví", "cà vạt"]):
                        return "accessory"
                    return c

                broad_categories = set(get_broad_category(p) for p in products[:4])
                has_multi_category = len(broad_categories) >= 2 and len(products[:4]) >= 2

                if is_four_seasons and len(products) >= 4:
                    season_headers = [
                        ("🌸", "1. Mùa Xuân (Tươi mới - Nhẹ nhàng - Thanh lịch)"),
                        ("☀️", "2. Mùa Hè (Mát mẻ - Thoáng khí - Năng động)"),
                        ("🍂", "3. Mùa Thu (Lãng mạn - Layer nhẹ - Trang nhã)"),
                        ("❄️", "4. Mùa Đông (Ấm áp - Sang trọng - Thời thượng)")
                    ]
                    for idx, p in enumerate(products[:4]):
                        s_icon, s_title = season_headers[idx]
                        sizes_text = ", ".join(p.get('sizes', [])) if isinstance(p.get('sizes'), list) else str(p.get('sizes'))
                        old_p = p.get('old_price') or p['price']
                        discount_pct = p.get('discount_pct') or (int((old_p - p['price']) / old_p * 100) if old_p > p['price'] else 0)
                        discount_text = f" (Giảm {discount_pct}%)" if discount_pct > 0 else ""
                        mat_val = p.get('material') or p.get('fit') or 'Chất liệu cao cấp'
                        desc_raw = (p.get('description') or '').strip().split('\n')[0].strip()
                        desc_snippet = f" - {desc_raw[:95]}..." if desc_raw else ""
                        lines.append(
                            f"{s_icon} **{s_title}:**\n"
                            f"   👉 **{p['name']}** (Mã: `{p.get('code', 'EV')}`)\n"
                            f"   • Giá ưu đãi: **{p['price']:,}đ**{discount_text}\n"
                            f"   • Size: **{sizes_text}**\n"
                            f"   • Đặc điểm: {mat_val}{desc_snippet}\n"
                        )
                else:
                    # Liệt kê danh sách sản phẩm gợi ý nổi bật theo vai trò outfit
                    for idx, p in enumerate(products[:4], 1):
                        sizes_text = ", ".join(p.get('sizes', [])) if isinstance(p.get('sizes'), list) else str(p.get('sizes'))
                        old_p = p.get('old_price') or p['price']
                        discount_pct = p.get('discount_pct') or (int((old_p - p['price']) / old_p * 100) if old_p > p['price'] else 0)
                        discount_text = f" (Giảm {discount_pct}%)" if discount_pct > 0 else ""

                        cat = (p.get('category') or '').lower()
                        sub_cat = (p.get('sub_category') or '').lower()
                        name_l = (p.get('name') or '').lower()
                        
                        icon = "👕"
                        role_label = "Áo"
                        if "quần" in cat or "quần" in sub_cat or "loe" in cat or "loe" in name_l:
                            icon = "👖"
                            role_label = "Quần"
                        elif "giày" in sub_cat or "sneaker" in sub_cat or "giày" in cat:
                            icon = "👟"
                            role_label = "Giày"
                        elif "khoác" in cat or "khoác" in sub_cat:
                            icon = "🧥"
                            role_label = "Khoác ngoài"
                        elif "kính" in sub_cat or "thắt lưng" in sub_cat or "ví" in sub_cat or "phụ kiện" in cat:
                            icon = "🕶️"
                            role_label = "Phụ kiện"
                        elif "đầm" in cat or "váy" in cat:
                            icon = "👗"
                            role_label = "Váy/Đầm"

                        label_str = f"{icon} {idx}. **{role_label}: {p['name']}**" if has_multi_category else f"{idx}. **{p['name']}**"
                        
                        mat_val = p.get('material') or p.get('fit') or 'Chất liệu cao cấp'
                        desc_raw = (p.get('description') or '').strip().split('\n')[0].strip()
                        desc_snippet = f" - {desc_raw[:95]}..." if desc_raw else ""
                        lines.append(
                            f"{label_str} (Mã: `{p.get('code', 'EV')}`)\n"
                            f"   • Giá ưu đãi: **{p['price']:,}đ**{discount_text}\n"
                            f"   • Size: **{sizes_text}**\n"
                            f"   • Điểm nhấn: {mat_val}{desc_snippet}"
                        )

                # Thêm mẹo phối đồ từ stylist theo phong cách / bối cảnh / phân loại
                if is_four_seasons:
                    stylist_tip = (
                        "• 🌸 **Mùa Xuân:** Ưu tiên sơ mi cổ tàu linen/đầm pastel nhẹ nhàng du xuân.\n"
                        "• ☀️ **Mùa Hè:** Áo thun 100% cotton organic hoặc polo Nano dệt tổ ong thấm hút mồ hôi phối short mát mẻ.\n"
                        "• 🍂 **Mùa Thu:** Phong cách smart-casual layering với cardigan dệt kim mỏng, sơ mi dài tay & áo khoác gió trượt nước.\n"
                        "• ❄️ **Mùa Đông:** Giữ ấm thời thượng bằng cách layer áo len cổ lọ bên trong, khoác ngoài măng tô dạ dáng dài hoặc áo khoác chần bông dày dặn."
                    )
                else:
                    stylist_tip = cls.get_styling_tip(user_message=user_msg_lower, entities=entities, products=products[:4])

                if stylist_tip:
                    lines.append(f"\n💡 *Gợi ý phối đồ 4 mùa từ Stylist:*\n{stylist_tip}" if is_four_seasons else f"\n💡 *Gợi ý phối đồ từ Stylist:* {stylist_tip}")

                if is_concert:
                    is_st = any(w in user_msg_lower for w in ["sơn tùng", "son tung", "m-tp", "sky"])
                    st_mention = " của Sếp Sơn Tùng M-TP" if is_st else ""
                    closing = f"Set đồ này diện đi quẩy concert{st_mention} đảm bảo bạn sẽ cực kỳ 'cháy', phong độ và thoải mái bung xõa suốt đêm nhạc luôn nha! 🔥 Bạn ưng ý nhất item nào trong set nè?"
                elif is_four_seasons:
                    closing = "Evern Fashion luôn sẵn sàng các bộ sưu tập thời trang cao cấp cho cả 4 mùa quanh năm. Bạn đang muốn lên đồ cho mùa nào cụ thể nhất hay cần mình tư vấn size cho mẫu nào ở trên nè? ✨"
                elif season_val in ["mùa hè", "mùa đông", "mùa thu", "mùa xuân"]:
                    closing = f"Các thiết kế dành cho {season_val} ở trên đều có chất liệu rất tôn dáng và hợp thời tiết. Bạn đang ưng ý mẫu nào nhất để mình hỗ trợ tư vấn size vừa vặn nhất nhé! ✨"
                elif not occasion_kw and entities.get("height") and entities.get("weight"):
                    h = entities.get("height")
                    w = entities.get("weight")
                    h_desc = f"{h}cm" if h > 3 else f"{h}m"
                    closing = f"Với số đo {h_desc} - {w}kg của bạn, các mẫu trên mặc size S hoặc form M suông nhẹ là cực kỳ vừa vặn và hack dáng luôn nha. Bạn ưng ý mẫu nào nhất để mình hỗ trợ tư vấn chi tiết hơn nè? ✨"
                elif occasion_kw:
                    closing = f"Set đồ này diện đi {occasion_kw} đảm bảo vừa đẹp chuẩn gu vừa nổi bật luôn nha! Bạn đang ưng ý mẫu nào nhất trong set này nè? ✨"
                else:
                    closing = cls.get_closing(situation)
                    if entities.get("height") and entities.get("weight") and any(w in closing.lower() for w in ["chiều cao", "cân nặng"]):
                        closing = "Bạn đang ưng ý mẫu nào nhất trong set đồ này? Cứ nhắn mình để mình hỗ trợ bạn chi tiết hơn nhé! ✨"

                lines.append(f"\n{closing}")
                return "\n".join(lines)
            else:
                return cls._generate_empty_response(user_msg_lower=user_msg_lower, entities=entities, situation=situation)

        # Tư vấn chọn size áo và quần theo chiều cao và cân nặng
        if intent == "size_guide":
            height = entities.get("height")
            weight = entities.get("weight")
            if height or weight:
                h_text = f"{height//100}m{height%100:02d}" if height else ""
                w_text = f"{weight}kg" if weight else ""

                hw_str = []
                if h_text:
                    hw_str.append(f"chiều cao **{h_text}**")
                if w_text:
                    hw_str.append(f"cân nặng **{w_text}**")
                hw_display = " và ".join(hw_str)

                u_lower = (user_message or "").lower()
                user_wants_both_or_set = (
                    len(products) >= 2 and (
                        entities.get("is_set_reference")
                        or any(w in u_lower for w in ["áo và quần", "quần và áo", "cả áo và quần", "cả áo lẫn quần", "mẫu áo và quần", "mẫu quần và áo", "set này", "bộ này", "cả set", "cả bộ", "trong set", "cả 2", "cả hai", "các mẫu này", "những mẫu này"])
                        or not any(w in u_lower for w in ["chỉ áo", "mỗi áo", "chỉ quần", "mỗi quần", "chỉ váy", "mỗi váy"])
                    )
                )

                # TRƯỜNG HỢP 1: TƯ VẤN SIZE CHO CẢ SET (Gồm cả Áo và Quần hoặc nhiều món trong set)
                if user_wants_both_or_set and len(products) >= 2:
                    items_advice = []
                    size_summary = []
                    for idx, prod in enumerate(products[:4], 1):
                        adv = cls._compute_single_product_size(prod, height, weight, hw_display)
                        detail_tip = f"\n  💡 *Mẹo chọn form dáng:* {adv['alt_note']}" if adv['alt_note'] else ""
                        item_text = (
                            f"{adv['icon']} {idx}. **{adv['label']}: {adv['name']}**{adv['code_str']}\n"
                            f"• **Size khuyến nghị phù hợp nhất:** **Size {adv['rec_size']}**\n"
                            f"  - Chuẩn thông số cho vóc dáng {hw_display}.{detail_tip}\n"
                            f"• **Bảng size sẵn có tại showroom:** **{adv['avail_str']}**"
                        )
                        items_advice.append(item_text)
                        size_summary.append(f"{adv['label']} chọn **Size {adv['rec_size']}**")

                    items_block = "\n\n".join(items_advice)
                    summary_text = " và ".join(size_summary)

                    style_tip = (
                        "\n\n💡 *Gợi ý diện set từ Stylist:*\n"
                        "• Set đồ này phối cùng một đôi **sneaker trắng tối giản** hoặc **giày loafer** là chuẩn bài để đi chơi, đi cafe cuối tuần cùng bạn bè rồi nhé! Bạn có thể sơ vin vạt trước hoặc khoác hờ áo để tạo hiệu ứng 'kéo dài chân' cực đỉnh."
                    )

                    intro_target = "cả áo và quần" if len(products) == 2 else "cả set đồ"
                    return (
                        f"Dạ với {hw_display}, vóc dáng của bạn rất thon gọn và cân đối! Evern Stylist tư vấn size chi tiết cho {intro_target} bạn đang quan tâm nhé: ✨\n\n"
                        f"🎯 **Tư vấn chọn size chuẩn xác cho từng món trong set:**\n\n"
                        f"{items_block}"
                        f"{style_tip}\n\n"
                        f"Tất cả sản phẩm trong set đều đang có sẵn trong kho với đầy đủ size. Bạn có thể bấm **'Thêm vào giỏ'** hoặc **'Xem'** ở khung sản phẩm bên dưới ({summary_text}) để đặt hàng giữ sản phẩm ngay nhé! ❤️"
                    )

                # TRƯỜNG HỢP 2: TƯ VẤN SIZE CHO 1 MẪU SẢN PHẨM CỤ THỂ
                target_p = None
                if db_info and db_info.get("product"):
                    target_p = db_info["product"]
                elif products and len(products) == 1:
                    target_p = products[0]
                elif products:
                    for p in products:
                        p_n = p.get("name", "").lower()
                        sub_c = (p.get("sub_category") or "").lower()
                        if any(w in u_lower for w in ["váy ngủ", "do ngu", "đồ ngủ", "pijama"]) and ("ngủ" in p_n or "ngủ" in sub_c or "mặc nhà" in sub_c):
                            target_p = p
                            break
                        elif any(w in u_lower for w in ["đầm", "váy", "chân váy"]) and ("váy" in p_n or "đầm" in p_n or "váy" in sub_c or "đầm" in sub_c):
                            target_p = p
                            break
                        elif any(w in u_lower for w in ["quần", "jean", "âu", "tây", "kaki", "short"]) and ("quần" in p_n or "quần" in sub_c):
                            target_p = p
                            break
                        elif any(w in u_lower for w in ["áo", "sơ mi", "polo", "thun", "khoác"]) and ("áo" in p_n or "áo" in sub_c):
                            target_p = p
                            break
                    if not target_p and len(products) > 0:
                        target_p = products[0]

                if target_p:
                    adv = cls._compute_single_product_size(target_p, height, weight, hw_display)
                    detail_tip = f"\n  💡 *Mẹo chọn size & form dáng:* {adv['alt_note']}" if adv['alt_note'] else ""
                    intro_prod = f"Dạ với chiếc **{adv['name']}** cực kỳ quyến rũ và mềm mại này, kết hợp cùng {hw_display} rất thon thả của bạn: ✨\n\n" if adv['is_sleepwear'] else f"Dạ với {hw_display}, vóc dáng của bạn rất thon gọn và chuẩn đẹp, diện mẫu này lên form cực kỳ tôn dáng luôn nè! ✨\n\n"

                    style_pairing_tip = ""
                    p_name_lower = adv['name'].lower()
                    if "loe" in p_name_lower or "douyin" in p_name_lower:
                        style_pairing_tip = (
                            "\n💡 **Gợi ý phối đồ chuẩn vibe Douyin / Soái ca từ Stylist:**\n"
                            "• Chiếc quần ống loe nhẹ này cực kỳ 'hack' chiều cao và tạo hiệu ứng chân dài miên man.\n"
                            "• **Phối áo:** Bạn có thể phối cùng **áo thun form rộng oversize** sơ vin vạt trước, hoặc khoác ngoài **áo khoác jeans đen chỉ nổi / bomber** để tạo tỷ lệ chuẩn soái ca nhé!\n"
                            "• **Phụ kiện:** Đi cùng một đôi **giày sneaker retro** là chuẩn tỷ lệ vàng cơ thể luôn nè. ✨"
                        )
                    elif adv['is_pants']:
                        style_pairing_tip = (
                            "\n💡 **Gợi ý phối đồ từ Stylist:**\n"
                            "• Mẫu quần này rất dễ phối cùng áo sơ mi công sở, áo polo hoặc áo thun basic đóng thùng để tôn vóc dáng cao ráo.\n"
                            "• Bạn có thể hỏi mình thêm: *'Gợi ý áo phối cùng quần này'* để mình lên trọn set cho bạn nhé!"
                        )

                    alt_products_str = ""
                    if len(products) > 1:
                        alt_lines = ["\n🛍️ **Một số mẫu cùng gu đang rất được ưa chuộng tại showroom:**"]
                        for idx_alt, alt_p in enumerate(products[1:3], 1):
                            alt_p_name = alt_p.get("name", "")
                            alt_lines.append(f"{idx_alt}. **{alt_p_name}** - Giá: **{alt_p.get('price', 0):,}đ**")
                        alt_products_str = "\n".join(alt_lines) + "\n"

                    return (
                        f"{intro_prod}"
                        f"🎯 **Tư vấn chọn size chuẩn xác cho mẫu:**\n"
                        f"👉 **{adv['name']}**{adv['code_str']}\n\n"
                        f"• **Size khuyến nghị phù hợp nhất:** **Size {adv['rec_size']}**\n"
                        f"  - Chuẩn thông số cho vóc dáng {hw_display}, đảm bảo ôm vừa vặn tôn trọn đường nét mà vẫn cử động cực kỳ thoải mái.{detail_tip}\n"
                        f"• **Bảng size sẵn có tại showroom:** **{adv['avail_str']}**\n"
                        f"{style_pairing_tip}\n"
                        f"{alt_products_str}\n"
                        f"Sản phẩm đang có sẵn trong kho. Bạn có thể bấm **'Thêm vào giỏ'** hoặc **'Xem'** ở khung sản phẩm bên dưới để chọn Size {adv['rec_size']} và đặt hàng giữ sản phẩm ngay nhé! ❤️"
                    )

                # Trường hợp 2: Chưa chọn sản phẩm cụ thể -> Gợi ý size toàn diện cho Áo, Quần và Váy/Đầm
                shirt_size = "M"
                shirt_alt = "L"
                pants_size = "29 - 30"
                dress_size = "M"
                dress_alt = "L"

                # Tính toán size dựa trên cân nặng
                if weight:
                    if weight < 53:
                        shirt_size = "S"
                        shirt_alt = "M (nếu thích mặc rộng/oversize)"
                        pants_size = "28 - 29"
                        dress_size = "S (ôm dáng chuẩn thon gọn)"
                        dress_alt = "M (thoải mái, mềm rủ)"
                    elif 53 <= weight <= 62:
                        shirt_size = "M"
                        shirt_alt = "L (nếu thích mặc form rộng thoải mái)"
                        pants_size = "29 - 30"
                        dress_size = "M"
                        dress_alt = "L"
                    elif 63 <= weight <= 72:
                        shirt_size = "L"
                        shirt_alt = "XL"
                        pants_size = "31 - 32"
                        dress_size = "L"
                        dress_alt = "XL"
                    elif 73 <= weight <= 82:
                        shirt_size = "XL"
                        shirt_alt = "2XL"
                        pants_size = "32 - 34"
                        dress_size = "XL"
                        dress_alt = "2XL"
                    else:
                        shirt_size = "2XL"
                        shirt_alt = "3XL"
                        pants_size = "34 - 36"
                        dress_size = "2XL"
                        dress_alt = "3XL"
                elif height:
                    if height < 165:
                        shirt_size = "S"
                        shirt_alt = "M"
                        pants_size = "28 - 29"
                        dress_size = "S"
                        dress_alt = "M"
                    elif 165 <= height <= 172:
                        shirt_size = "M"
                        shirt_alt = "L"
                        pants_size = "29 - 30"
                        dress_size = "M"
                        dress_alt = "L"
                    elif 173 <= height <= 178:
                        shirt_size = "L"
                        shirt_alt = "XL"
                        pants_size = "31 - 32"
                        dress_size = "L"
                        dress_alt = "XL"
                    else:
                        shirt_size = "XL"
                        shirt_alt = "2XL"
                        pants_size = "33 - 34"
                        dress_size = "XL"
                        dress_alt = "2XL"

                if products:
                    prod_names = ", ".join([f"**{p.get('name', '')}**" for p in products[:2]])
                    prod_line = f"Dưới đây mình đã chọn sẵn các mẫu trang phục ({prod_names}...) cực kỳ tôn dáng và vừa vặn cho vóc dáng của bạn. Bạn tham khảo các mẫu bên dưới nhé! ❤️"
                else:
                    prod_line = "Bạn đang muốn chốt size cho mẫu nào để mình kiểm tra số lượng và giữ hàng giúp bạn nhé? ❤️"

                return (
                    f"Dạ với {hw_display}, số đo của bạn rất chuẩn và cực kỳ dễ lên đồ luôn nè! ✨\n\n"
                    f"🎯 **Gợi ý chọn size phù hợp nhất cho bạn:**\n"
                    f"• **Váy & Đầm Nữ (Đầm tiệc / Đầm lụa / Váy ngủ):**\n"
                    f"  - **Size {dress_size}:** Vừa vặn tôn trọn vòng eo và đường cong thướt tha.\n"
                    f"  - **Size {dress_alt}:** Nếu bạn thích mặc phong cách suông rộng nhẹ nhàng, thoải mái khi ngủ hoặc vận động.\n"
                    f"• **Áo (Sơ mi / Polo / Áo thun / Áo khoác):**\n"
                    f"  - **Size {shirt_size}:** Mặc vừa vặn, chuẩn phom, tôn dáng chỉn chu.\n"
                    f"  - **Size {shirt_alt}:** Nếu bạn thích mặc phong cách suông rộng hoặc oversize trẻ trung theo kiểu Hàn Quốc.\n"
                    f"• **Quần (Quần tây / Quần jean / Quần short):** Chuẩn **Size {pants_size}** nha!\n\n"
                    f"{prod_line}"
                )

        # Phản hồi về các chính sách cửa hàng (đổi trả, thanh toán, giao hàng)
        if intent in ["shipping_return", "size_guide", "discount", "payment_method", "care_instruction", "store_location"]:
            prefix_styles = [
                "Dạ về vấn đề này bạn hoàn toàn yên tâm nhé! ✨ ",
                "Evern xin chia sẻ thông tin chi tiết với bạn ngay đây ạ: 😊 ",
                "Dạ đây là quy định và chính sách hỗ trợ khách hàng chu đáo tại shop nè: "
            ]
            chosen_prefix = random.choice(prefix_styles)
            body = default_dataset_reply or "Shop hỗ trợ đổi trả trong 7 ngày và giao hàng toàn quốc nhanh chóng."
            return f"{chosen_prefix}\n\n{body}\n\nNếu cần hỗ trợ thêm thông tin gì bạn cứ thoải mái nhắn shop nha! ❤️"

        # Phản hồi lời chào và giới thiệu về thương hiệu shop
        if intent in ["greeting", "other"]:
            msg_lower = (user_message or "").lower()
            if any(w in msg_lower for w in ["shop tên", "tên shop", "cửa hàng tên", "thương hiệu", "shop mình tên", "bạn là bot của shop", "đây là shop nào", "bạn là ai"]):
                return "Dạ chào bạn! Cửa hàng của chúng mình là thương hiệu thời trang Evern ✨ Còn mình là Evern AI Stylist – chuyên viên tư vấn phong cách thông minh của shop. Hôm nay bạn đang muốn tìm đồ đi làm, đi chơi hay cần mình gợi ý set đồ nào không nè? ❤️"

            greetings = [
                "Dạ xin chào bạn! 👋 Mình là Evern AI Stylist của thương hiệu thời trang Evern. Bạn đang muốn tìm đồ cho dịp nào (đi làm, dạo phố, đi tiệc) để mình tư vấn outfit thật chuẩn gu nhé?",
                "Chào bạn nha! ✨ Rất vui được đón tiếp bạn tại Evern Store. Hôm nay bạn đang muốn xem áo thun, polo, sơ mi, quần jean hay cần mình phối trọn bộ outfit?",
                "Hello bạn! Cứ chia sẻ nhu cầu, từ tìm sản phẩm đến chọn size hay phối đồ, Evern AI Stylist đều sẵn sàng hỗ trợ nè! 😊"
            ]
            return random.choice(greetings)

        # Phản hồi lời tạm biệt
        if intent == "goodbye":
            goodbyes = [
                "Tạm biệt bạn nha! Chúc bạn một ngày thật vui vẻ và mặc đẹp mỗi ngày. Khi nào cần phối đồ cứ quay lại gọi mình nhé! ✨",
                "Rất vui được hỗ trợ bạn hôm nay. Chúc bạn tìm được outfit thật ưng ý và hẹn gặp lại bạn sớm nhé! ❤️",
                "Okie bạn nè! Cần thêm gợi ý gì cứ nhắn Evern bất cứ lúc nào nha. Tạm biệt bạn! 👋"
            ]
            return random.choice(goodbyes)

        # Câu trả lời mặc định khi không rơi vào trường hợp cụ thể
        return default_dataset_reply or "Dạ mình có thể giúp bạn tìm kiếm trang phục, kiểm tra giá và tồn kho hoặc tư vấn phối đồ phong cách thời trang phù hợp nhất!"
