import requests
from bs4 import BeautifulSoup
import json

# 目标URL：下厨房的家常菜分类页面
BASE_URL = "https://www.xiachufang.com"
CATEGORY_URL = f"{BASE_URL}/category/40076/"

# HTTP请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def parse_recipe_detail(recipe_url):
    """解析单个菜谱页面的详细信息 (待实现)"""
    # TODO: 在这里实现详细页面的解析逻辑
    print(f"准备解析: {recipe_url}")
    return None

def main():
    """主函数，用于获取并处理菜谱列表"""
    print(f"正在从 {CATEGORY_URL} 获取菜谱列表...")
    
    try:
        # 发送HTTP GET请求
        response = requests.get(CATEGORY_URL, headers=HEADERS, timeout=10)  # 增加10秒超时
        response.raise_for_status()  # 如果请求失败则抛出异常

        # 使用BeautifulSoup解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找所有包含菜谱链接的<a>标签
        recipe_links = []
        recipe_list_ul = soup.find('ul', class_='list')
        if recipe_list_ul:
            all_links = recipe_list_ul.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                # 确保是菜谱详情页的链接，通常以 /recipe/ 开头
                if href and href.startswith('/recipe/'):
                    full_url = f"{BASE_URL}{href}"
                    if full_url not in recipe_links:
                        recipe_links.append(full_url)
        
        if not recipe_links:
            print("错误：未能找到任何菜谱链接，可能是页面结构已改变。")
            return

        print(f"成功找到 {len(recipe_links)} 个菜谱链接。")

        # 遍历链接并调用解析函数（当前只打印）
        for url in recipe_links:
            parse_recipe_detail(url)

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    main()