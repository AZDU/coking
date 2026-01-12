import json
import os

# --- 配置 ---

# 输入文件
HOWTOCOOK_FILE = 'recipes_clean.json'  # 我们现有的数据 (来自 HowToCook)
NEW_SOURCE_FILE = 'new_data_source.json'  # 新的、更大的数据源

# 输出文件
OUTPUT_FILE = 'recipes_clean.json'  # 直接覆盖

# 目标菜谱数量
TARGET_COUNT = 2000

# 食材同义词（可按需扩充）
SYNONYMS = {
    '番茄': '西红柿',
    '土豆': '马铃薯',
    '山药豆': '山药',
    '葱': '小葱',
    '大葱': '小葱',
    '姜': '生姜',
    '蒜': '大蒜',
    '蒜瓣': '大蒜',
    '猪肉': '猪里脊',
    '瘦肉': '猪里脊',
    '鸡肉': '鸡胸肉',
    '鸡腿肉': '鸡腿',
    '牛肉末': '牛肉',
    '牛肉丝': '牛肉',
    '虾仁': '虾',
}

# 饮用型酒精关键词（烹调用料酒/黄酒允许，饮用型一律剔除）
ALCOHOL_KEYWORDS = [
    '金酒', '伏特加', '朗姆', '威士忌', '龙舌兰', '白兰地',
    '鸡尾酒', '莫吉托', 'Mojito', '金汤力', '长岛冰茶', 'B52',
    '马天尼', '曼哈顿', '白酒鸡尾酒', '红酒鸡尾酒', '香槟鸡尾酒'
]

# --- 脚本 ---

def normalize_ingredient(name):
    name = name.strip()
    return SYNONYMS.get(name, name)

def is_alcoholic_drink(recipe):
    text_to_check = recipe.get('name', '') + ' ' + recipe.get('category', '')
    for keyword in ALCOHOL_KEYWORDS:
        if keyword in text_to_check:
            return True
    for ing in recipe.get('ingredients', []):
        ing_name = ing.get('name', '')
        if any(k in ing_name for k in ALCOHOL_KEYWORDS):
            return True
    return False


def normalize_taste(val):
    """将 taste 统一为列表[str]"""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x) for x in val]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []

def convert_new_source_format(item):
    name = item.get('title') or item.get('name', '')
    category = item.get('category', '') or item.get('source_category', '')
    cooking_time = item.get('cooking_time')
    difficulty = item.get('difficulty', 0)
    taste = normalize_taste(item.get('taste') or item.get('tags'))
    return {
        'name': name,
        'category': category,
        'ingredients': item.get('ingredients', []),
        'steps': item.get('steps', []),
        'cooking_time': cooking_time,
        'taste': taste,
        'difficulty': difficulty,
        'source': 'NewSource',
        'source_path': item.get('source_path', '')
    }

def main():
    all_recipes = []
    seen_names = set()

    # 1. 加载 HowToCook 数据
    if os.path.exists(HOWTOCOOK_FILE):
        with open(HOWTOCOOK_FILE, 'r', encoding='utf-8') as f:
            howtocook_data = json.load(f)
            for recipe in howtocook_data:
                if not is_alcoholic_drink(recipe):
                    for ing in recipe.get('ingredients', []):
                        ing['name'] = normalize_ingredient(ing['name'])
                    all_recipes.append(recipe)
                    seen_names.add(recipe.get('name', ''))
    print(f"从 HowToCook 加载了 {len(all_recipes)} 道菜谱。")

    # 2. 加载新数据源
    if os.path.exists(NEW_SOURCE_FILE):
        with open(NEW_SOURCE_FILE, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            for item in new_data:
                recipe = convert_new_source_format(item)
                if recipe.get('name') and recipe['name'] not in seen_names and not is_alcoholic_drink(recipe):
                    for ing in recipe.get('ingredients', []):
                        ing['name'] = normalize_ingredient(ing.get('name', ''))
                    all_recipes.append(recipe)
                    seen_names.add(recipe['name'])
    print(f"合并新数据源后，总计 {len(all_recipes)} 道不重复的菜谱。")

    # 3. 截断到目标数量
    final_recipes = all_recipes[:TARGET_COUNT]

    # 4. 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_recipes, f, ensure_ascii=False, indent=2)

    print(f"处理完成！共 {len(final_recipes)} 道菜谱已保存到 {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
