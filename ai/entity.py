import re
from typing import Dict, Any, Optional, List

class EntityExtractor:
    CATEGORIES = {
        # Áo khoác chuyên biệt
        "áo khoác jeans": [
            "áo khoác jeans", "ao khoac jeans", "áo khoác jean", "ao khoac jean",
            "khoác jeans", "khoác jean", "denim jacket", "jean jacket", "denim coat", "áo denim"
        ],
        "áo khoác da": [
            "áo khoác da", "ao khoac da", "khoác da", "leather jacket", "biker jacket",
            "da biker", "áo da", "jacket da", "motorcycle jacket"
        ],
        "áo khoác gió": [
            "áo khoác gió", "ao khoac gio", "áo gió", "ao gio", "windbreaker",
            "wind breaker", "wind jacket", "áo chống gió"
        ],
        "áo khoác bomber": [
            "áo khoác bomber", "ao khoac bomber", "áo bomber", "ao bomber",
            "bomber", "bomber jacket", "flight jacket"
        ],
        "áo khoác hoodie": [
            "áo khoác hoodie", "ao khoac hoodie", "hoodie jacket", "zip hoodie", "hoodie khóa kéo"
        ],
        "áo khoác trench": [
            "trench coat", "trench", "áo trench", "áo khoác trench",
            "trench coat nữ", "trench coat nam", "măng tô", "áo măng tô"
        ],
        "áo khoác puffer": [
            "puffer", "puffer jacket", "áo puffer", "áo phao", "áo khoác phao",
            "down jacket", "quilted jacket"
        ],
        "áo khoác varsity": [
            "varsity", "varsity jacket", "áo varsity", "áo khoác varsity",
            "college jacket", "letterman jacket"
        ],
        "áo khoác kaki": [
            "áo khoác kaki", "kaki jacket", "khaki jacket", "áo jacket kaki"
        ],
        "áo blazer": [
            "blazer", "áo blazer", "blazer nam", "blazer nữ", "blazer oversize",
            "oversized blazer", "blazer công sở", "blazer casual"
        ],
        "áo cardigan": [
            "cardigan", "áo cardigan", "áo len cardigan", "cardigan len",
            "cardigan mỏng", "cardigan oversize"
        ],
        "áo hoodie": [
            "áo hoodie", "ao hoodie", "hoodie", "hooded sweatshirt",
            "hoodie oversize", "hoodie zip", "hoodie form rộng"
        ],
        "áo sweater": [
            "sweater", "sweatshirt", "áo sweater", "áo nỉ", "áo nỉ cổ tròn",
            "crewneck", "crew neck", "oversized sweatshirt"
        ],
        "áo len": [
            "áo len", "ao len", "knitwear", "knit", "knitted sweater",
            "áo len cổ tròn", "áo len cổ lọ", "áo len oversize"
        ],
        "áo khoác": [
            "áo khoác", "ao khoac", "jacket", "outerwear", "áo khoác ngoài",
            "áo khoác nam", "áo khoác nữ", "áo khoác unisex"
        ],

        # Áo
        "áo sơ mi": [
            "áo sơ mi", "ao so mi", "sơ mi", "so mi", "shirt", "dress shirt",
            "button shirt", "button-up", "button up", "oxford", "oxford shirt",
            "áo sơ mi nam", "áo sơ mi nữ", "sơ mi công sở", "sơ mi đi làm",
            "sơ mi oversize", "sơ mi form rộng", "sơ mi tay dài", "sơ mi tay ngắn",
            "sơ mi trắng", "sơ mi linen"
        ],
        "áo polo": [
            "áo polo", "ao polo", "polo", "áo có cổ", "ao co co", "áo thun có cổ",
            "áo cổ bẻ", "polo shirt", "polo tee", "polo nam", "polo nữ",
            "polo basic", "polo oversize"
        ],
        "áo tank top": [
            "tank top", "tanktop", "áo tank top", "áo ba lỗ", "ba lỗ",
            "áo sát nách", "áo không tay", "sleeveless", "sleeveless top"
        ],
        "áo croptop": [
            "croptop", "crop top", "crop-top", "áo croptop", "áo crop", "áo ngắn", "cropped top"
        ],
        "áo hai dây": [
            "áo hai dây", "ao hai day", "hai dây", "áo dây", "spaghetti top",
            "camisole", "cami", "tank camisole"
        ],
        "áo thể thao": [
            "áo thể thao", "sports shirt", "sports top", "training shirt", "running shirt", "gym shirt"
        ],
        "áo thun": [
            "áo thun", "ao thun", "áo phông", "ao phong", "áo tshirt", "tshirt",
            "t-shirt", "tee", "graphic tee", "basic tee", "oversized tee",
            "oversize tee", "áo thun basic", "áo thun oversize", "áo thun form rộng",
            "áo thun cổ tròn", "áo thun tay dài", "áo thun tay ngắn"
        ],

        # Quần chuyên biệt
        "quần jean skinny": [
            "skinny jeans", "skinny jean", "quần skinny", "jean skinny", "quần jean bó", "jean bó"
        ],
        "quần jean straight": [
            "straight jeans", "straight jean", "quần jean ống đứng", "jean ống đứng", "straight leg"
        ],
        "quần jean baggy": [
            "baggy jeans", "baggy jean", "quần baggy jean", "jean baggy"
        ],
        "quần jean mom": [
            "mom jeans", "mom jean", "quần mom", "jean mom"
        ],
        "quần jean cargo": [
            "cargo jeans", "cargo jean", "jean cargo", "quần jean cargo"
        ],
        "quần jean": [
            "quần jean", "quan jean", "quần bò", "quan bo", "jeans", "jean",
            "denim pants", "denim", "jean pants", "quần denim"
        ],
        "quần loe": [
            "quần loe", "quan loe", "ống loe", "ong loe", "quần ống loe", "quan ong loe",
            "loe", "flare", "flared", "flare pants", "bell bottom", "bell bottoms"
        ],
        "quần ống rộng": [
            "quần ống rộng", "quan ong rong", "ống rộng", "ong rong", "wide leg",
            "wide-leg", "wide leg pants", "palazzo", "quần wide leg"
        ],
        "quần ống suông": [
            "quần ống suông", "quan ong suong", "ống suông", "ong suong",
            "straight pants", "straight leg pants"
        ],
        "quần baggy": [
            "quần baggy", "quan baggy", "baggy", "baggy pants", "baggy trousers"
        ],
        "quần cargo": [
            "quần cargo", "quan cargo", "cargo pants", "cargo", "quần túi hộp", "túi hộp", "cargo trousers"
        ],
        "quần jogger": [
            "quần jogger", "jogger", "jogger pants", "joggers", "quần thể thao jogger"
        ],
        "quần short": [
            "quần short", "quan short", "short", "shorts", "quần ngắn", "short pants", "bermuda", "bermuda shorts"
        ],
        "quần kaki": [
            "quần kaki", "quan kaki", "khaki pants", "khaki trousers", "kaki", "quần khaki"
        ],
        "quần legging": [
            "legging", "leggings", "quần legging", "yoga pants", "tights"
        ],
        "quần thể thao": [
            "quần thể thao", "sports pants", "athletic pants", "training pants", "quần gym", "quần tập"
        ],
        "quần tây": [
            "quần tây", "quan tay", "quần âu", "quan au", "trousers", "dress pants",
            "suit pants", "slacks", "quần công sở"
        ],

        # Váy & Đầm chuyên biệt
        "đầm dạ hội": [
            "đầm dạ hội", "đầm dạ tiệc", "đầm đi tiệc", "đầm tiệc", "đầm cưới",
            "đầm đám cưới", "váy đám cưới", "váy dự tiệc", "đầm sang trọng",
            "evening dress", "gown", "evening gown", "formal dress"
        ],
        "đầm maxi": [
            "đầm maxi", "váy maxi", "maxi dress", "maxi", "váy dài", "đầm dài"
        ],
        "đầm midi": [
            "đầm midi", "váy midi", "midi dress", "midi skirt"
        ],
        "đầm body": [
            "đầm body", "váy body", "bodycon", "bodycon dress", "body dress"
        ],
        "đầm chữ A": [
            "đầm chữ a", "váy chữ a", "a-line dress", "aline dress", "a line skirt"
        ],
        "chân váy": [
            "chân váy", "chan vay", "skirt", "mini skirt", "midi skirt", "maxi skirt", "váy ngắn"
        ],
        "váy ngủ": [
            "váy ngủ", "vay ngu", "đồ ngủ", "do ngu", "pijama", "pyjama", "pajamas",
            "pjs", "đồ mặc nhà", "do mac nha", "váy ngủ lụa", "sleepwear", "nightwear",
            "nightdress", "night gown"
        ],
        "váy & đầm": [
            "váy", "vay", "đầm", "dam", "dress", "women dress", "womens dress"
        ],

        # Đồ bộ / thể thao / trẻ em / đôi
        "đồ thể thao": [
            "đồ thể thao", "do the thao", "sportswear", "activewear", "gym wear",
            "gymwear", "workout clothes", "đồ gym", "đồ tập", "đồ chạy bộ",
            "running clothes", "training wear"
        ],
        "quần áo trẻ em": [
            "quần áo trẻ em", "đồ trẻ em", "đồ trẻ con", "đồ cho bé", "kids clothes",
            "kidswear", "children clothes", "children's clothing", "kids fashion"
        ],
        "đồ bé trai": [
            "đồ bé trai", "quần áo bé trai", "boy clothes", "boys clothes", "boys fashion"
        ],
        "đồ bé gái": [
            "đồ bé gái", "quần áo bé gái", "girl clothes", "girls clothes", "girls fashion"
        ],
        "đồ đôi": [
            "đồ đôi", "do doi", "áo đôi", "quần áo đôi", "couple outfit",
            "couple clothes", "matching outfit", "matching clothes"
        ],
        "unisex": [
            "unisex", "unisex clothing", "đồ unisex", "áo unisex", "quần unisex", "cho cả nam và nữ"
        ],

        # Phụ kiện
        "phụ kiện": [
            "phụ kiện", "phu kien", "accessories", "fashion accessories", "thắt lưng",
            "that lung", "belt", "dây lưng", "dây nịt", "ví", "ví da", "wallet", "card holder", "giày",
            "giay", "shoes", "sneaker", "sneakers", "giày thể thao", "giày tây", "oxford", "derby", "loafers",
            "kính", "kính mát", "kinh mat", "sunglasses",
            "cà vạt", "ca vat", "tie", "nơ", "bow tie",
            "kẹp tóc", "kep toc", "càng cua", "kẹp càng cua", "set 2 kẹp tóc", "set kẹp tóc",
            "cột tóc", "buộc tóc", "chun buộc tóc", "dây buộc tóc", "quần tất", "quan tat",
            "tất", "vớ", "đôi tất", "dù", "ô cầm tay", "dù che mưa"
        ]
    }

    GENDERS = {
        "nam": [
            "nam", "male", "man", "men", "mens", "men's", "đàn ông", "dan ong",
            "con trai", "con trai nam", "anh", "anh ấy", "bố", "ba", "cha",
            "bác trai", "chú", "cậu", "ông", "chàng", "boy", "boys", "nam giới", "phái nam"
        ],
        "nữ": [
            "nữ", "nu", "female", "woman", "women", "womens", "women's",
            "phụ nữ", "phu nu", "con gái", "con gai", "chị", "chị gái",
            "em gái", "cô", "bác gái", "mẹ", "má", "mẹ tôi", "bà", "nàng",
            "girl", "girls", "ladies", "lady", "nữ giới", "phái nữ"
        ],
        "unisex": [
            "unisex", "cho nam nữ", "cho cả nam và nữ", "cả nam lẫn nữ",
            "nam nữ đều mặc", "ai mặc cũng được", "gender neutral", "gender-neutral"
        ],
        "trẻ em": [
            "trẻ em", "trẻ con", "em bé", "bé", "con nít", "nhóc",
            "kid", "kids", "child", "children", "bé trai", "bé gái"
        ],
        "người lớn tuổi": [
            "người già", "người lớn tuổi", "ông bà", "người cao tuổi", "elderly", "senior", "senior citizen"
        ]
    }

    COLORS = [
        "trắng", "đen", "đỏ", "xanh", "vàng", "cam", "tím", "hồng", "nâu", "xám", "be", "kem",
        "xanh navy", "navy", "xanh biển", "xanh dương", "xanh da trời", "sky blue", "xanh baby",
        "baby blue", "xanh pastel", "xanh mint", "mint", "xanh lá", "xanh lá cây", "xanh rêu",
        "rêu", "olive", "xanh olive", "xanh quân đội", "xanh cổ vịt", "teal", "xanh ngọc",
        "turquoise", "xanh denim", "đỏ đô", "đỏ rượu", "đỏ burgundy", "burgundy", "đỏ cherry",
        "đỏ tươi", "wine", "hồng phấn", "hồng baby", "hồng pastel", "hồng đào", "hồng đất",
        "dusty pink", "hot pink", "magenta", "tím pastel", "tím lavender", "lavender", "tím lilac",
        "lilac", "tím mộng mơ", "nâu đất", "nâu bò", "nâu chocolate", "chocolate", "nâu caramel",
        "camel", "nâu be", "trắng ngà", "trắng kem", "trắng sữa", "trắng tuyết", "trắng ngọc",
        "off white", "off-white", "ivory", "cream", "đen tuyền", "đen jet", "jet black",
        "xám tro", "xám nhạt", "xám đậm", "charcoal", "light gray", "dark gray", "caro",
        "kẻ sọc", "sọc", "kẻ ngang", "kẻ dọc", "tie dye", "loang màu", "multicolor", "nhiều màu",
        "color block", "white", "black", "red", "blue", "green", "yellow", "orange", "purple",
        "pink", "brown", "gray", "grey", "beige", "pastel", "maroon"
    ]

    SIZES = [
        "XXXS", "3XS", "XXS", "2XS", "XS", "S", "small", "M", "medium", "L", "large",
        "XL", "extra large", "XXL", "2XL", "XXXL", "3XL", "4XL", "5XL",
        "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38",
        "39", "40", "41", "42", "43", "44", "45", "46",
        "size nhỏ", "size vừa", "size lớn", "size đại", "free size", "freesize", "one size",
        "oversize", "form rộng", "form vừa", "form ôm",
        "US", "UK", "EU", "size US", "size UK", "size EU", "asian size", "asia size"
    ]

    MATERIALS = [
        "cotton", "100 cotton", "organic cotton", "sợi tre", "bamboo", "linen", "flax",
        "lụa", "silk", "lụa tơ tằm", "len", "wool", "cashmere", "polyester", "poly",
        "nylon", "spandex", "elastane", "acrylic", "rayon", "viscose", "satin", "lụa satin",
        "nano", "kaki", "khaki", "denim", "jean", "da thật", "da bò", "leather",
        "genuine leather", "synthetic leather", "da PU", "PU leather", "nỉ", "fleece",
        "fleece fabric", "chiffon", "voan", "oxford", "ren", "lace", "thun", "jersey",
        "canvas", "tweed", "vải dạ", "dạ tweed", "dạ ép", "felt", "mesh", "vải dù", "vải gió", "vải chống nước",
        "lông cừu", "lông vũ", "lông thỏ", "nhung", "nhung tăm", "corduroy", "vải nhung", "da lộn", "suede"
    ]

    OCCASIONS = [
        "hàng ngày", "hằng ngày", "thường ngày", "đi chơi", "dạo phố", "đi cà phê", "cà phê",
        "đi ăn", "đi ăn tối", "đi xem phim", "đi mua sắm", "đi gặp bạn", "gặp bạn bè", "đi chill",
        "đi chơi cuối tuần", "chủ nhật", "cuối tuần", "chụp ảnh", "sống ảo",
        "đi học", "đại học", "cao đẳng", "đến trường", "school", "college", "university", "campus",
        "đi làm", "công sở", "văn phòng", "office", "work", "workwear", "business", "business casual",
        "gặp khách hàng", "gặp đối tác", "họp", "meeting", "phỏng vấn", "phỏng vấn xin việc",
        "ngân hàng", "job interview", "interview", "thuyết trình", "presentation",
        "hẹn hò", "đi date", "date", "gặp crush", "đi chơi với người yêu", "đi với người yêu",
        "first date", "romantic dinner", "dinner date", "buổi hẹn",
        "tiệc", "party", "sinh nhật", "tiệc sinh nhật", "birthday", "birthday party", "bữa tiệc",
        "đám cưới", "tiệc cưới", "dự cưới", "wedding", "wedding guest", "wedding party", "khách sạn 5 sao",
        "dạ hội", "dạ tiệc", "prom", "prom night", "homecoming", "gala", "gala dinner",
        "cocktail party", "tiệc tối", "dinner party", "dự tiệc", "đi tiệc",
        "concert", "đi concert", "concert sơn tùng", "sơn tùng", "sơn tùng m-tp", "liveshow", "show diễn", "quẩy concert", "âm nhạc", "music festival", "festival", "lễ hội", "sự kiện", "event",
        "triển lãm", "exhibition", "fashion event", "red carpet", "quẩy", "bar",
        "du lịch", "du lịch trong nước", "đi biển", "đi núi", "đi phượt", "dã ngoại", "camping",
        "đi camping", "đà lạt", "đà nẵng", "nha trang", "phú quốc", "hạ long", "hội an", "sa pa",
        "sapa", "mộc châu", "tam đảo", "vũng tàu", "cần thơ", "hà nội", "sài gòn", "tphcm", "hồ chí minh",
        "du lịch nước ngoài", "international travel", "travel", "vacation", "holiday",
        "hàn quốc", "korea", "korean", "seoul", "busan", "nhật bản", "japan", "japanese", "tokyo",
        "osaka", "kyoto", "trung quốc", "china", "chinese", "thượng hải", "shanghai", "bắc kinh", "beijing",
        "đài loan", "du lịch đài loan", "taiwan", "taipei", "thái lan", "thailand", "bangkok", "phuket",
        "singapore", "singapore trip", "nước mỹ", "du lịch mỹ", "hoa kỳ", "usa", "united states", "new york", "los angeles",
        "nước anh", "du lịch anh", "uk", "london", "nước pháp", "du lịch pháp", "france", "paris", "nước ý", "du lịch ý", "italy", "italia", "rome", "milan",
        "nước đức", "du lịch đức", "germany", "berlin", "canada", "nước úc", "du lịch úc", "australia",
        "tết", "tết nguyên đán", "quần áo tết", "đồ tết", "du xuân", "chúc tết", "đi chùa", "lì xì",
        "trung thu", "tết trung thu", "valentine", "valentine's day", "14/2", "8/3", "20/10",
        "halloween", "christmas", "noel", "xmas", "new year", "new year's eve", "năm mới",
        "thanksgiving", "black friday", "graduation", "graduation party", "tốt nghiệp",
        "chạy bộ", "running", "gym", "fitness", "workout", "yoga", "pilates", "đạp xe",
        "cycling", "tennis", "cầu lông", "badminton", "bóng đá", "football", "soccer", "basketball", "thể thao",
        "ở nhà", "mặc nhà", "đồ mặc nhà", "đồ ngủ", "váy ngủ", "sleepwear", "loungewear", "pajama", "pajamas"
    ]

    SEASONS = {
        "bốn mùa": [
            "4 mùa", "4 mua", "bốn mùa", "bon mua", "cả 4 mùa", "ca 4 mua",
            "quanh năm", "xuân hạ thu đông", "xuân hè thu đông"
        ],
        "mùa xuân": [
            "mùa xuân", "mua xuan", "tiết xuân", "ngày xuân", "du xuân", "xuân", "xuan", "spring"
        ],
        "mùa hè": [
            "mùa hè", "mua he", "mùa hạ", "mua ha", "ngày hè", "ngay he", "hè", "he", "hạ", "summer"
        ],
        "mùa thu": [
            "mùa thu", "mua thu", "ngày thu", "trời thu", "tiết thu", "thu", "autumn", "fall"
        ],
        "mùa đông": [
            "mùa đông", "mua dong", "ngày đông", "trời đông", "tiết đông", "đông", "dong", "winter"
        ],
        "thu đông": [
            "thu đông", "thu dong", "thu-đông", "autumn winter", "fall winter"
        ],
        "xuân hè": [
            "xuân hè", "xuan he", "xuân-hè", "spring summer"
        ]
    }

    WEATHER = [
        "trời nóng", "nóng", "nóng bức", "oi bức", "nắng", "nắng nóng", "trời nắng",
        "trời lạnh", "lạnh", "se lạnh", "gió lạnh", "rét", "rét đậm", "rét buốt",
        "trời mưa", "mưa", "mưa phùn", "mưa lớn", "mưa rào", "ẩm", "ẩm ướt", "nồm", "thời tiết nồm",
        "mát", "mát mẻ", "ấm áp", "hot weather", "warm weather", "cold weather", "cool weather",
        "rainy", "rainy weather", "snow", "snowy", "snowing", "winter weather", "summer weather",
        "humid", "dry", "windy", "strong wind"
    ]

    STYLES = {
        "douyin": [
            "douyin", "douying", "phong cách douyin", "phong cáh douyin", "style douyin", "gu douyin",
            "douyin trung quốc", "trung quốc", "chinese style", "tỷ tỷ", "soái ca", "vibe trung", "style trung"
        ],
        "korean": [
            "hàn quốc", "korean", "korea", "seoul style", "oppa", "ulzzang", "k-fashion", "korean fashion"
        ],
        "japanese": [
            "nhật", "nhật bản", "japanese", "japan", "j-fashion", "harajuku", "japanese streetwear"
        ],
        "streetwear": [
            "streetwear", "street style", "đường phố", "cool ngầu", "biker", "hiphop", "urban", "urban style", "skater", "skate style"
        ],
        "y2k": [
            "y2k", "2000s", "style 2000", "mcbling", "retro y2k"
        ],
        "vintage": [
            "vintage", "retro", "cổ điển", "old school", "classic vintage"
        ],
        "minimal": [
            "minimal", "minimalist", "tối giản", "đơn giản", "clean", "clean look", "clean fit", "clean girl", "clean boy"
        ],
        "basic": [
            "basic", "basic style", "đồ basic", "đơn giản", "dễ mặc", "dễ phối"
        ],
        "casual": [
            "casual", "casual style", "hàng ngày", "thường ngày", "everyday outfit"
        ],
        "smart casual": [
            "smart casual", "smart-casual", "smartcasual"
        ],
        "office": [
            "công sở", "đi làm", "văn phòng", "office", "office wear", "workwear", "business casual", "business casual outfit"
        ],
        "thanh lịch": [
            "thanh lịch", "trang nhã", "lịch sự", "elegant", "elegance", "sang", "sang trọng", "classy"
        ],
        "trưởng thành": [
            "trưởng thành", "mature", "chững chạc", "đứng đắn", "chín chắn", "quý ông", "đĩnh đạc"
        ],
        "năng động": [
            "năng động", "thể thao", "thoải mái", "sporty", "active", "activewear"
        ],
        "sexy": [
            "sexy", "quyến rũ", "gợi cảm", "glam", "glamorous"
        ],
        "feminine": [
            "nữ tính", "feminine", "bánh bèo", "girly", "tiểu thư"
        ],
        "masculine": [
            "nam tính", "masculine", "men style", "manly"
        ],
        "preppy": [
            "preppy", "preppy style", "học đường", "school style", "ivy style"
        ],
        "old money": [
            "old money", "old-money", "quiet luxury", "luxury", "quý tộc", "sang chảnh"
        ],
        "boho": [
            "boho", "bohemian", "boho chic"
        ],
        "coquette": [
            "coquette", "coquette style", "bánh bèo", "nữ tính"
        ],
        "athleisure": [
            "athleisure", "sport fashion", "sporty casual"
        ]
    }

    @classmethod
    def extract(cls, text: str) -> Dict[str, Any]:
        text_lower = text.lower().strip()
        extracted = {
            "category": None,
            "categories": [],
            "sub_category": None,
            "gender": None,
            "color": None,
            "size": None,
            "min_price": None,
            "max_price": None,
            "material": None,
            "occasion": None,
            "season": None,
            "weather": None,
            "style": None,
            "product_code": None,
            "is_outfit_query": False,
            "is_budget_friendly": False,
            "keywords": [],
            "height": None,
            "weight": None,
            "age": None
        }

        # Trích xuất mã sản phẩm cụ thể nếu có (VD: EV0001, AR258043...)
        code_match = re.search(r"\b([A-Z]{2}\d{4,8}[A-Z0-9]*)\b", text, re.IGNORECASE)
        if code_match:
            extracted["product_code"] = code_match.group(1).upper()

        # Kiểm tra cụm từ chỉ trang phục / outfit chung chung hoặc yêu cầu combo nhiều món (áo + quần)
        has_combo = bool(re.search(
            r"\b(?:1\s*(?:chiếc|cái)?\s*(?:quần|áo)\s*(?:và|với|cùng)\s*1\s*(?:chiếc|cái)?\s*(?:áo|quần)|quần.*áo|áo.*quần|combo|quần và áo|áo và quần)\b",
            text_lower
        ))
        has_general_clothing = bool(re.search(
            r"\b(?:quần áo|quan ao|trang phục|trang phuc|lên đồ|len do|phối đồ|mix đồ|set đồ|outfit|mặc gì|mac gi|chọn đồ|chon do|tìm đồ|tim do|bộ đồ|bo do|1 bộ|một bộ|bộ phù hợp|bộ nào|đồ đi date|đồ date|đồ tết|quần áo tết|đồ du xuân|mặc với gì|không biết mặc gì|gợi ý đồ|tư vấn đồ|đồ mùa|đồ hè|đồ đông|đồ thu|đồ xuân|đồ 4 mùa|đồ bốn mùa|4 mùa|bốn mùa)\b",
            text_lower
        ))
        if has_general_clothing or has_combo:
            extracted["is_outfit_query"] = True

        # Trích xuất loại sản phẩm / danh mục thời trang (ưu tiên danh mục cụ thể trước)
        found_categories = []
        for cat_name, synonyms in cls.CATEGORIES.items():
            for syn in sorted(synonyms, key=len, reverse=True):
                if re.search(r"\b" + re.escape(syn.lower()) + r"\b", text_lower):
                    if cat_name not in found_categories:
                        found_categories.append(cat_name)
                    if not extracted["sub_category"]:
                        extracted["sub_category"] = syn
                    break

        # Nếu người dùng chỉ nói chung chung là "áo" hoặc "quần" (và không phải cụm "quần áo")
        if not found_categories and not has_general_clothing:
            if re.search(r"\báo\b|\bao\b", text_lower):
                found_categories.append("áo")
            if re.search(r"\bquần\b|\bquan\b", text_lower):
                found_categories.append("quần")

        # Ánh xạ chuẩn sang CSDL (Database category và sub_category)
        if has_general_clothing and not extracted.get("sub_category"):
            found_categories = []
            extracted["category"] = None
            extracted["sub_category"] = None
        else:
            extracted["categories"] = found_categories
            if found_categories:
                primary_cat = found_categories[0]
                if primary_cat.startswith("áo khoác ") or primary_cat in [
                    "áo blazer", "áo cardigan", "áo hoodie", "áo sweater", "áo len", "áo khoác"
                ]:
                    extracted["category"] = "Áo khoác"
                    extracted["sub_category"] = primary_cat
                elif primary_cat.startswith("quần jean") or primary_cat == "quần bò":
                    extracted["category"] = "Quần jean"
                    extracted["sub_category"] = primary_cat
                elif primary_cat in [
                    "quần tây", "quần âu", "quần kaki", "quần short", "quần baggy",
                    "quần ống rộng", "quần ống suông", "quần cargo", "quần jogger", "quần thể thao"
                ]:
                    extracted["category"] = "Quần tây"
                    extracted["sub_category"] = primary_cat
                elif primary_cat == "quần loe":
                    extracted["category"] = "Quần loe"
                    extracted["sub_category"] = primary_cat
                elif primary_cat in [
                    "đầm dạ hội", "đầm maxi", "đầm midi", "đầm body", "đầm chữ A", "chân váy", "váy & đầm"
                ]:
                    extracted["category"] = "Váy & Đầm"
                    extracted["sub_category"] = primary_cat
                elif primary_cat == "váy ngủ":
                    extracted["category"] = "Váy & Đầm"
                    extracted["sub_category"] = "váy ngủ / đồ mặc nhà"
                elif primary_cat in ["áo thun", "áo tank top", "áo croptop", "áo hai dây", "áo thể thao"]:
                    extracted["category"] = "Áo thun"
                    extracted["sub_category"] = primary_cat
                elif primary_cat == "áo polo":
                    extracted["category"] = "Áo polo"
                    extracted["sub_category"] = primary_cat
                elif primary_cat == "áo sơ mi":
                    extracted["category"] = "Áo sơ mi"
                    extracted["sub_category"] = primary_cat
                elif primary_cat in ["phụ kiện", "quần legging"]:
                    extracted["category"] = "Phụ kiện"
                    extracted["sub_category"] = primary_cat
                else:
                    extracted["category"] = primary_cat
            else:
                extracted["category"] = None

        # Trích xuất phong cách thời trang
        for s_key, s_syns in cls.STYLES.items():
            for s_syn in sorted(s_syns, key=len, reverse=True):
                if re.search(r"\b" + re.escape(s_syn.lower()) + r"\b", text_lower):
                    extracted["style"] = s_key
                    break
            if extracted["style"]:
                break

        # Trích xuất giới tính
        for g_name, g_synonyms in cls.GENDERS.items():
            for syn in sorted(g_synonyms, key=len, reverse=True):
                if re.search(r"\b" + re.escape(syn.lower()) + r"\b", text_lower):
                    extracted["gender"] = g_name
                    break
            if extracted["gender"]:
                break

        # Trích xuất màu sắc (ưu tiên màu ghép dài trước)
        sorted_colors = sorted(set(cls.COLORS), key=len, reverse=True)
        for col in sorted_colors:
            if re.search(r"\b" + re.escape(col.lower()) + r"\b", text_lower):
                extracted["color"] = col.lower()
                break

        # Trích xuất kích cỡ
        size_prefix_match = re.search(r"\bsize\s*([a-zA-Z0-9]+)\b", text_lower)
        if size_prefix_match:
            extracted["size"] = size_prefix_match.group(1).upper()
        else:
            sorted_sizes = sorted(set(cls.SIZES), key=len, reverse=True)
            for s in sorted_sizes:
                if re.search(r"\b" + re.escape(s.lower()) + r"\b", text_lower):
                    extracted["size"] = s.upper()
                    break

        # Trích xuất khoảng giá hoặc mức giá tối đa / tối thiểu
        range_match = re.search(r"(?:từ\s*)?(\d+)\s*(?:k|nghìn|tr)?\s*(?:đến|-|tới)\s*(\d+)\s*(?:k|nghìn|tr)?", text_lower)
        if range_match:
            v1_raw, v2_raw = range_match.group(1), range_match.group(2)
            unit_mult = 1000
            if "tr" in text_lower or "triệu" in text_lower:
                unit_mult = 1000000
            extracted["min_price"] = int(v1_raw) * unit_mult
            extracted["max_price"] = int(v2_raw) * unit_mult
        else:
            # Giá tối đa (dưới 300k, < 500k, tầm 300k...)
            max_k = re.search(r"(?:dưới|<|khoảng|tầm|nhỏ hơn|tối đa)\s*(\d+)\s*(?:k|nghìn|nghin)\b", text_lower)
            max_tr = re.search(r"(?:dưới|<|khoảng|tầm|nhỏ hơn|tối đa)\s*(\d+(?:[.,]\d+)?)\s*(?:tr|triệu|trieu)\b", text_lower)
            max_num = re.search(r"(?:dưới|<|khoảng|tầm|nhỏ hơn|tối đa)\s*(\d{5,8})\b", text_lower)

            if max_k:
                extracted["max_price"] = int(max_k.group(1)) * 1000
            elif max_tr:
                val = float(max_tr.group(1).replace(",", "."))
                extracted["max_price"] = int(val * 1000000)
            elif max_num:
                extracted["max_price"] = int(max_num.group(1))

            # Giá tối thiểu (trên 200k, > 300k...)
            min_k = re.search(r"(?:trên|>|từ|lớn hơn|tối thiểu)\s*(\d+)\s*(?:k|nghìn|nghin)\b", text_lower)
            if min_k and not extracted["min_price"]:
                extracted["min_price"] = int(min_k.group(1)) * 1000

        # Nhận diện yêu cầu giá tiết kiệm / sinh viên / vừa túi tiền
        if any(kw in text_lower for kw in [
            "không có nhiều tiền", "khong co nhieu tien", "hợp túi tiền", "hop tui tien",
            "vừa túi tiền", "vua tui tien", "hợp với túi tiền", "hop voi tui tien",
            "giá sinh viên", "gia sinh vien", "sinh viên", "sinh vien", "giá rẻ", "gia re",
            "tiết kiệm", "tiet kiem", "bình dân", "binh dan", "hạt dẻ", "hat de", "ít tiền"
        ]):
            extracted["is_budget_friendly"] = True

        # Trích xuất chất liệu vải
        sorted_materials = sorted(set(cls.MATERIALS), key=len, reverse=True)
        for mat in sorted_materials:
            if re.search(r"\b" + re.escape(mat.lower()) + r"\b", text_lower):
                extracted["material"] = mat.lower()
                break

        # Trích xuất dịp sử dụng
        sorted_occasions = sorted(set(cls.OCCASIONS), key=len, reverse=True)
        for occ in sorted_occasions:
            if re.search(r"\b" + re.escape(occ.lower()) + r"\b", text_lower):
                extracted["occasion"] = occ.lower()
                break

        # Trích xuất mùa trong năm
        # Kiểm tra nếu người dùng nhắc đến cả 4 mùa hoặc '4 mùa' / 'bốn mùa'
        has_all_4 = (
            any(w in text_lower for w in ["xuân", "xuan"])
            and any(w in text_lower for w in ["hè", "he", "hạ"])
            and any(w in text_lower for w in ["thu", "autumn"])
            and any(w in text_lower for w in ["đông", "dong", "winter"])
        )
        if has_all_4 or any(w in text_lower for w in ["4 mùa", "4 mua", "bốn mùa", "bon mua", "quanh năm"]):
            extracted["season"] = "bốn mùa"
            extracted["is_outfit_query"] = True
        else:
            for canonical_season, syns in cls.SEASONS.items():
                found_s = False
                for s in sorted(syns, key=len, reverse=True):
                    if re.search(r"\b" + re.escape(s.lower()) + r"\b", text_lower):
                        extracted["season"] = canonical_season
                        found_s = True
                        break
                if found_s:
                    break

        # Trích xuất thời tiết
        sorted_weather = sorted(set(cls.WEATHER), key=len, reverse=True)
        for w in sorted_weather:
            if re.search(r"\b" + re.escape(w.lower()) + r"\b", text_lower):
                extracted["weather"] = w.lower()
                break

        # Trích xuất chiều cao (VD: 1m70, 165cm...)
        h_match = re.search(r'(?:cao\s*)?(\d)\s*[mM]\s*(\d{1,2})\b|(?:cao\s*)(\d{2,3})\s*(?:cm)?\b', text_lower)
        if h_match:
            if h_match.group(1) and h_match.group(2):
                cm = int(h_match.group(1)) * 100 + int(h_match.group(2))
                if 120 <= cm <= 220:
                    extracted["height"] = cm
            elif h_match.group(3):
                cm = int(h_match.group(3))
                if 120 <= cm <= 220:
                    extracted["height"] = cm

        # Trích xuất cân nặng (VD: 60kg, 55 ký...)
        w_match = re.search(r'(?:nặng\s*)?(\d{2,3})\s*(?:kg|kí|ký)\b|(?:nặng\s*)(\d{2,3})\b', text_lower)
        if w_match:
            weight_val = int(w_match.group(1) or w_match.group(2))
            if 30 <= weight_val <= 150:
                extracted["weight"] = weight_val

        # Trích xuất độ tuổi (VD: 21 tuổi, năm nay 21 tuổi, 25t...)
        age_match = re.search(r'\b(?:năm nay\s*)?(\d{1,2})\s*(?:tuổi|t)\b', text_lower)
        if age_match:
            a_val = int(age_match.group(1))
            if 10 <= a_val <= 90:
                extracted["age"] = a_val

        # Trích xuất từ khóa mô tả sản phẩm chi tiết (VD: 'lông cừu', 'hoa cúc', 'cổ tàu', 'họa tiết rồng'...)
        stop_words = {
            "shop", "cửa hàng", "cho", "mình", "em", "anh", "bạn", "tôi", "hỏi", "có", "không", "ko", "k", "hông",
            "bán", "tìm", "cần", "mua", "xem", "mẫu", "chiếc", "cái", "nào", "nhỉ", "ạ", "ơi", "với", "và", "ở",
            "của", "tại", "này", "được", "rồi", "nữa", "các", "những", "thì", "là", "đang", "muốn", "thời trang",
            "đẹp", "mới", "hot", "về", "giúp", "nhé", "nha", "chăng", "bao nhiêu", "nhiêu", "giá", "tiền",
            "tư vấn", "tu van", "gợi ý", "goi y", "chỉ cho", "tư vấn cho", "gợi ý cho",
            "chỉnh sửa", "chỉnh", "sửa", "thêm", "bổ sung", "cập nhật", "hướng dẫn",
            "1 số", "một số", "vài", "mấy", "số", "chút", "ít", "đôi", "món", "cặp", "set", "bộ",
            "mặc", "diện", "phối", "mix", "lên đồ", "chọn", "thử",
            "vào", "trong", "để", "hãy", "hộ", "dùm",
            "mùa", "tiết", "trời", "thời", "ngày", "buổi",
            "xuân", "hè", "thu", "đông", "hạ", "xuan", "he", "dong", "winter", "summer", "spring", "autumn", "fall",
            "4 mùa", "bốn mùa", "thời tiết", "tiết trời",
            "chuẩn", "hợp", "thích hợp", "phù hợp",
            "thế nào", "sao", "ra sao", "như thế nào", "gì", "đâu"
        }
        words_to_strip = list(stop_words)
        if extracted.get("category"):
            words_to_strip.extend(extracted["category"].lower().split())
        if extracted.get("sub_category"):
            words_to_strip.extend(extracted["sub_category"].lower().split())
        if extracted.get("color"):
            words_to_strip.extend(extracted["color"].lower().split())
        if extracted.get("size"):
            words_to_strip.append(extracted["size"].lower())
        if extracted.get("gender"):
            words_to_strip.append(extracted["gender"].lower())
        if extracted.get("style"):
            words_to_strip.append(extracted["style"].lower())
        if extracted.get("occasion"):
            words_to_strip.extend(extracted["occasion"].lower().split())
        if extracted.get("season"):
            words_to_strip.extend(extracted["season"].lower().split())
        if extracted.get("weather"):
            words_to_strip.extend(extracted["weather"].lower().split())
        for syn_list in cls.SEASONS.values():
            for s in syn_list:
                words_to_strip.extend(s.lower().split())
        words_to_strip.extend(["áo", "quần", "váy", "đầm", "set", "bộ", "đồ"])

        temp_kw_text = text_lower
        for wts in sorted(set(words_to_strip), key=len, reverse=True):
            if wts and len(wts) >= 2:
                temp_kw_text = re.sub(r"\b" + re.escape(wts) + r"\b", " ", temp_kw_text)
        
        remaining_kw = [w.strip() for w in temp_kw_text.split() if len(w.strip()) >= 2 and not w.strip().isdigit() and w.strip() not in stop_words]
        if remaining_kw:
            extracted["keywords"] = remaining_kw

        return extracted

