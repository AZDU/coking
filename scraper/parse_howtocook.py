import os
import re
import json
import glob
import signal

# 当输出被管道（例如 head）提前关闭时，避免 BrokenPipeError 让程序崩溃
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

SOURCE_DIR = '/tmp/how-to-cook/dishes'
OUTPUT_FILE = 'recipes_clean.json'

SECTION_TITLE_RE = re.compile(r'^##\s+(.+?)\s*$', re.MULTILINE)

TASTE_KEYWORDS = [
    ('辣', ['辣', '麻辣', '香辣', '辣椒', '剁椒']),
    ('麻', ['麻', '藤椒', '花椒', '椒麻']),
    ('甜', ['甜', '蜂蜜', '糖', '焦糖', '炼乳']),
    ('酸', ['酸', '醋', '柠檬', '番茄', '酸辣', '酸甜']),
    ('咸鲜', ['咸鲜', '酱油', '生抽', '老抽', '蚝油', '鱼露']),
    ('蒜香', ['蒜', '蒜香', '蒜末']),
    ('孜然', ['孜然']),
    ('咖喱', ['咖喱']),
]


def split_sections(markdown: str) -> dict:
    """按二级标题(##)切分章节，返回 {title: content}（content 不含标题行）"""
    matches = list(SECTION_TITLE_RE.finditer(markdown))
    sections = {}
    for idx, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        sections[title] = markdown[start:end].strip('\n')
    return sections


def extract_name(markdown: str, file_path: str) -> str:
    m = re.search(r'^#\s+(.+?)\s*的做法\s*$', markdown, re.MULTILINE)
    if not m:
        m = re.search(r'^#\s+(.+?)\s*$', markdown, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # fallback
    base = os.path.basename(file_path)
    return os.path.splitext(base)[0]


def extract_difficulty(markdown: str) -> int:
    m = re.search(r'预估烹饪难度：\s*(★+)', markdown)
    return len(m.group(1)) if m else 0


def extract_cooking_time_minutes(markdown: str) -> int | None:
    # 常见格式：预计制作制作时长 **200 分钟**。
    m = re.search(r'预计.*?时长\s*\*\*(\d+)\s*分钟\*\*', markdown)
    if m:
        return int(m.group(1))
    return None


def clean_inline_markup(s: str) -> str:
    s = re.sub(r'!\[[^\]]*]\([^)]*\)', '', s)  # remove images
    s = re.sub(r'<[^>]+>', '', s)  # remove html tags
    s = s.replace('**', '')
    s = s.replace('*', '')
    return s.strip()


def parse_ingredient_line(line: str) -> dict | None:
    """解析 `- 名称 数量`，并尽量拆分 name/quantity。"""
    line = clean_inline_markup(line)
    if not line:
        return None
    # 去掉前缀 - 或 *
    line = re.sub(r'^[\-\*]\s*', '', line).strip()
    if not line:
        return None

    # 常见：黑鳕鱼，带皮，2 片，450g（...）
    # 常见：盐 3g
    # 常见：食用油 10-15ml
    # 常见：土豆 2 个（...）
    parts = line.split()
    if len(parts) == 1:
        # 只有名字，没有数量
        return {'name': parts[0].strip(), 'quantity': ''}

    name = parts[0].strip()
    quantity = ' '.join(parts[1:]).strip()
    return {'name': name, 'quantity': quantity}


def extract_ingredients(sections: dict) -> list:
    """优先使用 `计算` 章节里的用量列表；没有则回退到 `必备原料和工具` 章节里的列表（数量可能缺失）。"""
    ingredients = []

    if '计算' in sections:
        block = sections['计算']
        lines = [l for l in block.splitlines() if re.match(r'^\s*[\-\*]\s+', l)]
        for l in lines:
            ing = parse_ingredient_line(l)
            if ing:
                ingredients.append(ing)
        if ingredients:
            return ingredients

    if '必备原料和工具' in sections:
        block = sections['必备原料和工具']
        lines = [l for l in block.splitlines() if re.match(r'^\s*[\-\*]\s+', l)]
        for l in lines:
            ing = parse_ingredient_line(l)
            if ing:
                ingredients.append(ing)

    return ingredients


def extract_steps(sections: dict) -> list:
    """只从 `操作` 章节提取步骤，避免把 `计算` 混进来。"""
    if '操作' not in sections:
        return []

    block = sections['操作']
    # 列表项：- xxx 或 * xxx
    lines = [l for l in block.splitlines() if re.match(r'^\s*[\-\*]\s+', l)]
    steps = []
    for l in lines:
        l = clean_inline_markup(l)
        l = re.sub(r'^[\-\*]\s*', '', l).strip()
        if l:
            steps.append(l)
    return steps


def extract_taste(markdown: str) -> list:
    text = clean_inline_markup(markdown)
    tags = []
    for tag, kws in TASTE_KEYWORDS:
        if any(k in text for k in kws):
            tags.append(tag)
    return tags


def parse_markdown(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    recipe = {
        'name': '',
        'category': '',
        'ingredients': [],
        'steps': [],
        'cooking_time': None,
        'taste': [],
        'difficulty': 0,
        'source': 'HowToCook',
        'source_path': os.path.relpath(file_path, '/tmp/how-to-cook')
    }

    recipe['name'] = extract_name(content, file_path)

    relative_path = os.path.relpath(file_path, SOURCE_DIR)
    parts = relative_path.split(os.sep)
    recipe['category'] = parts[0] if len(parts) > 1 else ''

    recipe['difficulty'] = extract_difficulty(content)
    recipe['cooking_time'] = extract_cooking_time_minutes(content)

    sections = split_sections(content)
    recipe['ingredients'] = extract_ingredients(sections)
    recipe['steps'] = extract_steps(sections)
    recipe['taste'] = extract_taste(content)

    return recipe


def main():
    all_recipes = []
    markdown_files = glob.glob(f"{SOURCE_DIR}/**/*.md", recursive=True)

    print(f"找到 {len(markdown_files)} 个菜谱文件，开始解析...")

    for i, file_path in enumerate(markdown_files):
        try:
            recipe_data = parse_markdown(file_path)
            # 过滤掉模板/异常：至少要有 name + steps + ingredients
            if recipe_data.get('name') and recipe_data.get('steps') and recipe_data.get('ingredients'):
                all_recipes.append(recipe_data)
            else:
                pass

            if (i + 1) % 50 == 0:
                print(f"已处理 {i + 1}/{len(markdown_files)}")
        except Exception as e:
            print(f"处理 {file_path} 时发生错误: {e}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=2)

    print(f"解析完成！共 {len(all_recipes)} 个菜谱已保存到 {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
