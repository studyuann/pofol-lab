import os
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import unquote
from bs4 import BeautifulSoup
from markdownify import markdownify as md

ZIP_PATH = r"C:\Users\ANN\pofol-lab\source\msp_wikies.zip"
TARGET_DIR = r"C:\Users\ANN\pofol-lab\content\concepts"
TEMP_EXTRACT_DIR = r"C:\Users\ANN\pofol-lab\source\temp_extracted"

def fix_filename_encoding(filename):
    try:
        bytes_name = filename.encode('cp437')
        try:
            return bytes_name.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return bytes_name.decode('euc-kr')
            except UnicodeDecodeError:
                return bytes_name.decode('cp949', errors='ignore')
    except Exception:
        return filename

def clean_title(name):
    if not name:
        return ""
    unquoted = unquote(name)
    unquoted = re.sub(r'\.(html|md)$', '', unquoted, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\s%20-]+[0-9a-f]{32}$', '', unquoted, flags=re.IGNORECASE)
    cleaned = re.sub(r'^[0-9a-f]{32}_?', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_zip(zip_path, extract_dir):
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            real_name = fix_filename_encoding(member.filename)
            if not real_name or real_name.endswith('/'):
                continue
            
            parts = [clean_title(p) if '.' not in p else clean_title(Path(p).stem) + Path(p).suffix for p in real_name.split('/') if p]
            dest_path = os.path.join(extract_dir, *parts)
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with zf.open(member) as src, open(dest_path, 'wb') as dst:
                shutil.copyfileobj(src, dst)

def process_conversion():
    target_msp_dir = os.path.join(TARGET_DIR, "메가존클라우드 MSP 솔루션 아키텍트")
    if os.path.exists(target_msp_dir):
        shutil.rmtree(target_msp_dir)
        
    count = 0
    for root, dirs, files in os.walk(TEMP_EXTRACT_DIR):
        for file in files:
            src_file_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_file_path, TEMP_EXTRACT_DIR)
            rel_dirs = [d for d in os.path.dirname(rel_path).split(os.sep) if d]
            
            if file.endswith('.html'):
                stem = Path(file).stem
                page_title = clean_title(stem)
                
                with open(src_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                page_body = soup.find('article') or soup.find('body') or soup
                
                # BeautifulSoup 단계에서 <a> 태그를 마크다운 목록(- [[위키링크]]) 형태로 변환
                for a_tag in page_body.find_all('a'):
                    href = a_tag.get('href', '')
                    text = a_tag.get_text().strip()
                    
                    if href.startswith(('http://', 'https://', 'mailto:')):
                        continue
                    
                    target_name = clean_title(os.path.basename(href))
                    if not target_name:
                        target_name = text
                        
                    if target_name and text:
                        if target_name == text:
                            wikilink = f"\n- [[{target_name}]]\n"
                        else:
                            wikilink = f"\n- [[{target_name}|{text}]]\n"
                        a_tag.replace_with(wikilink)
                
                md_text = md(str(page_body), heading_style="ATX").strip()
                
                # 연속된 빈 줄 정리 및 목록 구문 다듬기
                md_text = re.sub(r'\n{3,}', '\n\n', md_text)
                
                tags_str = ", ".join([f'"{t}"' for t in rel_dirs]) if rel_dirs else '"msp"'
                frontmatter = f"""---
title: "{page_title}"
date: 2026-08-02
tags: [{tags_str}]
is_public: true
draft: false
---

"""
                dest_filename = f"{page_title}.md"
                dest_path = os.path.join(TARGET_DIR, *rel_dirs, dest_filename) if rel_dirs else os.path.join(TARGET_DIR, dest_filename)
                
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(frontmatter + md_text)
                count += 1
            else:
                asset_name = clean_title(Path(file).stem) + Path(file).suffix if '.' in file else clean_title(file)
                dest_path = os.path.join(TARGET_DIR, *rel_dirs, asset_name) if rel_dirs else os.path.join(TARGET_DIR, asset_name)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_file_path, dest_path)
                
    print(f"BULLET_CONVERSION_SUCCESS: {count} pages processed.")

if __name__ == '__main__':
    extract_zip(ZIP_PATH, TEMP_EXTRACT_DIR)
    process_conversion()
