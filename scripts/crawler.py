# scripts/crawler.py
import sys
import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 動態添加專案根目錄到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from apps.crud.models import RawArticle, db

def load_sites_config(config_path='sites_config.json'):
    """載入網站配置文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_full_path = os.path.join(script_dir, config_path)
    
    if not os.path.exists(config_full_path):
        print(f"Configuration file not found at {config_full_path}")
        sys.exit(1)
    
    with open(config_full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def scrape_site(site_name, config):
    """根據配置爬取單個網站的文章"""
    url = config['base_url']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/58.0.3029.110 Safari/537.3'
    }

    print(f"[{site_name}] Scraping URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 檢查請求是否成功
    except requests.exceptions.RequestException as e:
        print(f"[{site_name}] Failed to retrieve the page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select(config['article_selector'])
    print(f"[{site_name}] Found {len(articles)} articles.")

    if not articles:
        print(f"[{site_name}] No articles found. Please check the HTML structure or the selectors.")
        return

    for article in articles:
        title_tag = article.select_one(config['title_selector'])
        content_tag = article.select_one(config['content_selector'])
        link_tag = article.select_one(config['link_selector'])

        if not title_tag or not content_tag or not link_tag:
            print(f"[{site_name}] Missing title, content, or link in one of the articles.")
            continue

        title = title_tag.get_text(strip=True)
        content = content_tag.get_text(strip=True)
        article_url = link_tag.get('href')

        if not article_url.startswith('http'):
            # 如果 URL 是相對路徑，轉換為絕對路徑
            article_url = urljoin(config['url_prefix'], article_url)

        # 檢查文章是否已存在
        if not RawArticle.query.filter_by(url=article_url).first():
            new_article = RawArticle(title=title, content=content, url=article_url)
            db.session.add(new_article)
            print(f"[{site_name}] Added new article: {title}")
        else:
            print(f"[{site_name}] Article already exists: {title}")

    db.session.commit()
    print(f"[{site_name}] Scraping completed and changes committed to the database.\n")

def scrape_all_sites(config_path='sites_config.json'):
    """爬取所有配置中的網站"""
    sites_config = load_sites_config(config_path)
    for site_name, config in sites_config.items():
        scrape_site(site_name, config)

if __name__ == "__main__":
    from apps.app import create_app  # 確保路徑正確
    app = create_app("local")    # 替換為您的配置名稱
    with app.app_context():
        scrape_all_sites()