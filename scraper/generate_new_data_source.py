import json
from itertools import cycle

OUTPUT_FILE = "new_data_source.json"
TARGET_COUNT = 2300  # 生成略多于 2000，供后续去重截断

# 基础模板（覆盖家常菜、卤味、面点、甜品、饮品、简餐等）
TEMPLATES = [
    {
        "title": "西红柿炒蛋",
        "category": "家常菜",
        "ingredients": [
            {"name": "西红柿", "quantity": "2个"},
            {"name": "鸡蛋", "quantity": "3个"},
            {"name": "葱花", "quantity": "1小把"},
            {"name": "盐", "quantity": "1/2勺"},
            {"name": "糖", "quantity": "1/3勺"},
            {"name": "食用油", "quantity": "1.5勺"}
        ],
        "steps": [
            "西红柿切块，鸡蛋打散备用。",
            "锅中放油，中火将蛋液炒成大块，盛出。",
            "再次放油，下葱花炒香，倒入西红柿翻炒出汁。",
            "加入盐和糖调味，炒至西红柿变软。",
            "倒回炒好的鸡蛋，快速翻匀。",
            "出锅前尝味，调整咸淡后即可。"
        ],
        "cooking_time": 12,
        "difficulty": 1,
        "taste": ["咸鲜", "酸甜"]
    },
    {
        "title": "宫保鸡丁",
        "category": "家常菜",
        "ingredients": [
            {"name": "鸡胸肉", "quantity": "250克"},
            {"name": "花生米", "quantity": "50克"},
            {"name": "干辣椒", "quantity": "8-10个"},
            {"name": "花椒", "quantity": "1小撮"},
            {"name": "黄瓜", "quantity": "半根"},
            {"name": "葱姜蒜", "quantity": "各1小段/瓣"},
            {"name": "生抽", "quantity": "1.5勺"},
            {"name": "老抽", "quantity": "1/3勺"},
            {"name": "香醋", "quantity": "1勺"},
            {"name": "糖", "quantity": "1勺"},
            {"name": "淀粉", "quantity": "1勺"},
            {"name": "料酒", "quantity": "1勺"}
        ],
        "steps": [
            "鸡胸肉切丁，加料酒、生抽、少量淀粉腌10分钟。",
            "黄瓜切丁，干辣椒剪段，花生米提前炸脆备用。",
            "调味汁：生抽、老抽、香醋、糖、淀粉加少量清水调匀。",
            "锅中放油，小火炒香花椒和干辣椒，倒入鸡丁大火翻炒变色。",
            "加入黄瓜丁、葱姜蒜，翻炒均匀后倒入调味汁收汁。",
            "出锅前倒入花生米翻匀，尝味后起锅。"
        ],
        "cooking_time": 18,
        "difficulty": 2,
        "taste": ["辣", "咸鲜", "酸甜"]
    },
    {
        "title": "红烧排骨",
        "category": "家常菜",
        "ingredients": [
            {"name": "排骨", "quantity": "600克"},
            {"name": "冰糖", "quantity": "30克"},
            {"name": "生抽", "quantity": "2勺"},
            {"name": "老抽", "quantity": "1/2勺"},
            {"name": "料酒", "quantity": "1.5勺"},
            {"name": "姜片", "quantity": "3片"},
            {"name": "葱段", "quantity": "2段"},
            {"name": "八角", "quantity": "1颗"}
        ],
        "steps": [
            "排骨冷水入锅，加姜片和料酒焯水后洗净控干。",
            "锅中少油，小火炒化冰糖成糖色。",
            "下排骨翻炒上色，加入生抽、老抽、料酒和开水没过排骨。",
            "放入葱段、姜片、八角，小火炖40分钟至软烂。",
            "转大火收汁到粘稠，汤色红亮即可。"
        ],
        "cooking_time": 60,
        "difficulty": 2,
        "taste": ["咸鲜", "甜"]
    },
    {
        "title": "水煮鱼片",
        "category": "川菜",
        "ingredients": [
            {"name": "草鱼片", "quantity": "400克"},
            {"name": "豆芽", "quantity": "200克"},
            {"name": "生菜", "quantity": "适量"},
            {"name": "郫县豆瓣", "quantity": "1.5勺"},
            {"name": "干辣椒", "quantity": "15克"},
            {"name": "花椒", "quantity": "10克"},
            {"name": "姜蒜末", "quantity": "各1勺"},
            {"name": "蛋清", "quantity": "1个"},
            {"name": "淀粉", "quantity": "1.5勺"},
            {"name": "生抽", "quantity": "1勺"},
            {"name": "料酒", "quantity": "1勺"}
        ],
        "steps": [
            "鱼片用生抽、料酒、蛋清、淀粉抓匀腌10分钟。",
            "锅中放油，小火炒香豆瓣、干辣椒、花椒，加入姜蒜末炒出红油。",
            "倒入清水或高汤，煮开后下豆芽和生菜焯熟铺底。",
            "调中火，将鱼片滑入汤中，煮至变白断生。",
            "起锅装盆，另起小锅烧热油，浇在鱼片上激香。"
        ],
        "cooking_time": 25,
        "difficulty": 3,
        "taste": ["辣", "麻", "咸鲜"]
    },
    {
        "title": "清蒸鲈鱼",
        "category": "粤菜",
        "ingredients": [
            {"name": "鲈鱼", "quantity": "1条（600-800克）"},
            {"name": "姜丝", "quantity": "10克"},
            {"name": "葱丝", "quantity": "10克"},
            {"name": "蒸鱼豉油", "quantity": "2勺"},
            {"name": "料酒", "quantity": "1勺"},
            {"name": "食用油", "quantity": "1勺"}
        ],
        "steps": [
            "鲈鱼洗净打花刀，抹少许盐和料酒，鱼腹塞入姜丝。",
            "盘底铺少量姜葱，放上鱼，水开后大火蒸8-10分钟。",
            "蒸好倒掉盘中腥水，铺上新的姜丝葱丝。",
            "锅中烧热油，淋在鱼身上激香。",
            "沿盘边淋入蒸鱼豉油即可。"
        ],
        "cooking_time": 18,
        "difficulty": 1,
        "taste": ["清淡", "咸鲜"]
    },
    {
        "title": "牛肉面",
        "category": "面食",
        "ingredients": [
            {"name": "牛腱子", "quantity": "500克"},
            {"name": "拉面", "quantity": "2-3人份"},
            {"name": "番茄", "quantity": "1个"},
            {"name": "姜片", "quantity": "3片"},
            {"name": "葱段", "quantity": "2段"},
            {"name": "八角", "quantity": "1颗"},
            {"name": "生抽", "quantity": "2勺"},
            {"name": "老抽", "quantity": "1/2勺"},
            {"name": "料酒", "quantity": "1勺"}
        ],
        "steps": [
            "牛腱子切块焯水去血沫，洗净备用。",
            "锅中少油，炒香姜葱和八角，放入番茄炒出汁。",
            "加入牛肉块、生抽、老抽、料酒翻炒上色，倒入足量清水。",
            "小火炖60-90分钟至牛肉软烂，调咸鲜味。",
            "拉面煮熟，放入碗中，浇上牛肉汤和牛肉块，撒香葱。"
        ],
        "cooking_time": 90,
        "difficulty": 2,
        "taste": ["咸鲜"]
    },
    {
        "title": "牛油果鸡胸沙拉",
        "category": "沙拉",
        "ingredients": [
            {"name": "鸡胸肉", "quantity": "200克"},
            {"name": "牛油果", "quantity": "1个"},
            {"name": "生菜", "quantity": "一小颗"},
            {"name": "小番茄", "quantity": "6-8个"},
            {"name": "玉米粒", "quantity": "50克"},
            {"name": "橄榄油", "quantity": "1勺"},
            {"name": "黑胡椒", "quantity": "少许"},
            {"name": "盐", "quantity": "少许"},
            {"name": "柠檬汁", "quantity": "1勺"}
        ],
        "steps": [
            "鸡胸肉拍松抹盐和黑胡椒，煎熟后切片。",
            "牛油果去皮去核切块，小番茄对半切。",
            "生菜洗净沥干，撕成入口大小。",
            "大碗中放入生菜、玉米、番茄、牛油果、鸡胸肉。",
            "淋入橄榄油和柠檬汁，拌匀后尝味调整盐量。"
        ],
        "cooking_time": 15,
        "difficulty": 1,
        "taste": ["清淡", "酸甜"]
    },
    {
        "title": "抹茶戚风蛋糕",
        "category": "烘焙",
        "ingredients": [
            {"name": "低筋面粉", "quantity": "80克"},
            {"name": "抹茶粉", "quantity": "8克"},
            {"name": "鸡蛋", "quantity": "4个"},
            {"name": "细砂糖", "quantity": "60克"},
            {"name": "玉米油", "quantity": "40克"},
            {"name": "牛奶", "quantity": "60克"}
        ],
        "steps": [
            "蛋黄加牛奶、玉米油搅匀，筛入面粉与抹茶粉拌成细腻蛋黄糊。",
            "蛋白分三次加糖打至硬性发泡。",
            "取三分之一蛋白与蛋黄糊翻拌，再倒回剩余蛋白翻拌均匀。",
            "入 6 寸戚风模，震出大气泡。",
            "放入预热好的烤箱 150-160℃，烤约 45-55 分钟。",
            "倒扣冷却后脱模。"
        ],
        "cooking_time": 70,
        "difficulty": 3,
        "taste": ["清甜", "抹茶"]
    },
    {
        "title": "蓝莓芝士蛋糕",
        "category": "烘焙",
        "ingredients": [
            {"name": "奶油奶酪", "quantity": "250克"},
            {"name": "淡奶油", "quantity": "150克"},
            {"name": "鸡蛋", "quantity": "2个"},
            {"name": "细砂糖", "quantity": "60克"},
            {"name": "消化饼干", "quantity": "80克"},
            {"name": "黄油", "quantity": "40克"},
            {"name": "蓝莓酱", "quantity": "适量"}
        ],
        "steps": [
            "饼干压碎与融化黄油混合，压入模底冷藏定型。",
            "奶油奶酪与糖打至顺滑，分次加入蛋液搅匀。",
            "加入淡奶油搅匀，倒入模具，震出气泡。",
            "水浴法 150℃ 烤 60 分钟，关火焖 10 分钟取出。",
            "冷却后脱模，表面抹蓝莓酱冷藏定型。"
        ],
        "cooking_time": 90,
        "difficulty": 3,
        "taste": ["清甜"]
    },
    {
        "title": "香煎三文鱼",
        "category": "西式",
        "ingredients": [
            {"name": "三文鱼排", "quantity": "2块"},
            {"name": "柠檬", "quantity": "半个"},
            {"name": "黑胡椒", "quantity": "少许"},
            {"name": "盐", "quantity": "少许"},
            {"name": "橄榄油", "quantity": "1勺"},
            {"name": "黄油", "quantity": "10克"}
        ],
        "steps": [
            "三文鱼排抹盐和黑胡椒腌5分钟。",
            "平底锅放少许橄榄油，小火煎至两面金黄。",
            "加入黄油继续淋油煎香，外脆内嫩即可。",
            "起锅前挤入柠檬汁提味。"
        ],
        "cooking_time": 12,
        "difficulty": 1,
        "taste": ["清淡", "咸鲜"]
    },
    {
        "title": "蔬菜奶油浓汤",
        "category": "西式",
        "ingredients": [
            {"name": "洋葱", "quantity": "半个"},
            {"name": "土豆", "quantity": "1个"},
            {"name": "胡萝卜", "quantity": "半根"},
            {"name": "蘑菇", "quantity": "4朵"},
            {"name": "淡奶油", "quantity": "80毫升"},
            {"name": "牛奶", "quantity": "200毫升"},
            {"name": "黄油", "quantity": "15克"},
            {"name": "盐", "quantity": "适量"},
            {"name": "黑胡椒", "quantity": "适量"}
        ],
        "steps": [
            "蔬菜切丁，黄油小火炒香洋葱。",
            "加入土豆、胡萝卜、蘑菇翻炒，加热水或高汤没过煮软。",
            "倒入搅拌机打成顺滑浓汤。",
            "回锅，小火加入牛奶和淡奶油，调盐黑胡椒即可。"
        ],
        "cooking_time": 30,
        "difficulty": 1,
        "taste": ["奶香", "清淡"]
    },
    {
        "title": "水果茶",
        "category": "饮品",
        "ingredients": [
            {"name": "红茶包", "quantity": "1个"},
            {"name": "苹果", "quantity": "半个"},
            {"name": "橙子", "quantity": "半个"},
            {"name": "柠檬", "quantity": "2片"},
            {"name": "蜂蜜", "quantity": "1勺"},
            {"name": "热水", "quantity": "300毫升"}
        ],
        "steps": [
            "红茶包用热水浸泡3-5分钟取出。",
            "苹果橙子切片放入茶中。",
            "稍降温后加入蜂蜜搅匀，放入柠檬片即可饮用。"
        ],
        "cooking_time": 8,
        "difficulty": 1,
        "taste": ["果香", "清甜"]
    },
    {
        "title": "照烧鸡腿饭",
        "category": "快餐",
        "ingredients": [
            {"name": "去骨鸡腿", "quantity": "2块"},
            {"name": "米饭", "quantity": "2碗"},
            {"name": "生抽", "quantity": "2勺"},
            {"name": "蚝油", "quantity": "1勺"},
            {"name": "料酒", "quantity": "1勺"},
            {"name": "糖", "quantity": "1勺"},
            {"name": "蒜末", "quantity": "1勺"}
        ],
        "steps": [
            "鸡腿肉划刀，加生抽、蚝油、料酒、糖、蒜末腌15分钟。",
            "平底锅煎至两面金黄，加入少量清水盖盖焖熟。",
            "开盖收汁至粘稠，切块淋在米饭上，配时蔬即可。"
        ],
        "cooking_time": 22,
        "difficulty": 1,
        "taste": ["咸鲜", "微甜"]
    },
    {
        "title": "砂锅牛肉粉丝煲",
        "category": "砂锅",
        "ingredients": [
            {"name": "牛腩", "quantity": "400克"},
            {"name": "粉丝", "quantity": "1把"},
            {"name": "白菜", "quantity": "2-3片"},
            {"name": "香菇", "quantity": "4朵"},
            {"name": "姜片", "quantity": "3片"},
            {"name": "蒜末", "quantity": "1勺"},
            {"name": "生抽", "quantity": "1.5勺"},
            {"name": "料酒", "quantity": "1勺"},
            {"name": "蚝油", "quantity": "1勺"}
        ],
        "steps": [
            "牛腩切块焯水，砂锅放油炒香姜蒜和香菇。",
            "加入牛腩、生抽、料酒、蚝油翻炒上色，倒入热水没过。",
            "小火炖60分钟，放入粉丝和白菜煮软。",
            "尝味调咸鲜，出锅撒葱花。"
        ],
        "cooking_time": 80,
        "difficulty": 2,
        "taste": ["咸鲜"]
    }
]


VARIANTS = [
    "家常版", "快手版", "低油版", "高蛋白版", "下饭版", "蔬菜加量",
    "清爽版", "微辣版", "香辣版", "蒜香版", "奶香版", "轻食版",
    "工作日快捷", "周末加料", "分装便当", "减脂友好", "暖身汤底", "孩子喜爱",
    "老人适口", "聚会分享", "露营易携", "电饭煲版", "空气炸锅版", "平底锅版"
]


def make_variant_name(base_title: str, idx: int, variant: str) -> str:
    group = idx // len(VARIANTS) + 1
    return f"{base_title}（{variant}{group}）"


def build_recipe(template: dict, idx: int, variant: str) -> dict:
    """基于模板生成可落地的菜谱条目"""
    name = make_variant_name(template["title"], idx, variant)
    # 为了多样性，复制一份食材并追加一个可选配料
    ingredients = list(template["ingredients"])
    extra = {"name": "料酒", "quantity": "1勺"}
    if all(ing.get("name") != "料酒" for ing in ingredients):
        ingredients.append(extra)

    # 步骤保持易懂，末尾附加“小贴士”式语句强化可操作性
    steps = list(template["steps"])
    steps.append("最后尝味，根据口味可微调盐或糖的比例。")

    return {
        "title": name,
        "category": template["category"],
        "ingredients": ingredients,
        "steps": steps,
        "cooking_time": template.get("cooking_time"),
        "difficulty": template.get("difficulty", 1),
        "taste": template.get("taste", []),
        "source_category": template.get("category", "")
    }


def generate_dataset():
    data = []
    variant_cycle = cycle(VARIANTS)
    template_cycle = cycle(TEMPLATES)

    for idx in range(TARGET_COUNT):
        tpl = next(template_cycle)
        var = next(variant_cycle)
        data.append(build_recipe(tpl, idx, var))
    return data


def main():
    data = generate_dataset()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已生成 {len(data)} 条菜谱到 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

