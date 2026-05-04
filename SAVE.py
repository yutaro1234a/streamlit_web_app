import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

SAVE_DIR = "downloaded_images"

MODAL_CANDIDATES = [
    "[role='dialog']",
    ".modal",
    ".dialog",
    ".popup",
    ".drawer",
    ".MuiDialog-root",
    ".MuiDialog-paper",
    ".ant-modal-wrap",
    ".ant-modal-body",
    ".ReactModal__Content",
]

# =========================
# JS: 画像抽出（強化版）
# =========================
FIND_IMAGES_SCRIPT = r"""
function unique(values) {
    return [...new Set(values.filter(Boolean))];
}

function toAbsolute(url) {
    try { return new URL(url, window.location.href).href; }
    catch (e) { return url; }
}

function pickBestFromSrcset(srcset) {
    if (!srcset) return null;
    const parts = srcset.split(',').map(v => v.trim()).filter(Boolean);
    if (!parts.length) return null;
    return parts[parts.length - 1].split(/\s+/)[0];
}

function extractBackgroundImages(styleValue) {
    if (!styleValue || styleValue === 'none') return [];
    const results = [];
    const regex = /url\((['"]?)(.*?)\1\)/g;
    let match;
    while ((match = regex.exec(styleValue)) !== null) {
        if (match[2]) results.push(match[2]);
    }
    return results;
}

function extractAll(root) {
    const scope = root || document;
    const urls = [];

    scope.querySelectorAll('img').forEach(el => {
        urls.push(
            el.currentSrc,
            el.src,
            el.getAttribute('data-src'),
            el.getAttribute('data-original'),
            pickBestFromSrcset(el.getAttribute('srcset')),
            pickBestFromSrcset(el.getAttribute('data-srcset'))
        );
    });

    scope.querySelectorAll('source').forEach(el => {
        urls.push(pickBestFromSrcset(el.getAttribute('srcset')));
    });

    scope.querySelectorAll('a').forEach(el => {
        const href = el.href;
        if (href && href.match(/\.(jpg|jpeg|png|gif|webp|svg|avif)/i)) {
            urls.push(href);
        }
    });

    scope.querySelectorAll('*').forEach(el => {
        const style = window.getComputedStyle(el);
        const list = extractBackgroundImages(style.backgroundImage);
        urls.push(...list);
    });

    return unique(urls.map(toAbsolute));
}

return extractAll(arguments[0]);
"""

# =========================
# ユーティリティ
# =========================
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]+', "_", name)

def get_filename_from_url(url):
    path = urlparse(url).path
    filename = os.path.basename(path)
    return unquote(filename)

def make_unique_filename(save_dir, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(save_dir, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1

    return new_filename

def get_extension(response, url):
    ct = (response.headers.get("Content-Type") or "").lower()

    if "jpeg" in ct: return ".jpg"
    if "png" in ct: return ".png"
    if "webp" in ct: return ".webp"
    if "gif" in ct: return ".gif"
    if "svg" in ct: return ".svg"
    if "avif" in ct: return ".avif"

    # fallback: URLから
    path = urlparse(url).path.lower()
    m = re.search(r"\.(jpg|jpeg|png|gif|webp|svg|avif)", path)
    if m:
        return "." + m.group(1)

    return ".bin"

# =========================
# モーダル検出
# =========================
def find_scrollable_modal(driver):
    for selector in MODAL_CANDIDATES:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for elem in elements:
            try:
                info = driver.execute_script("""
                    const el = arguments[0];
                    const s = window.getComputedStyle(el);
                    return {
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight,
                        overflowY: s.overflowY
                    };
                """, elem)

                if info["scrollHeight"] > info["clientHeight"]:
                    print(f"✅ モーダル検出: {selector}")
                    return elem
            except:
                pass
    return None

# =========================
# スクロール＆収集
# =========================
def auto_scroll_collect(driver, modal, pause=2, max_no_change=5):
    seen = set()
    no_change = 0
    last = 0

    while True:
        urls = driver.execute_script(FIND_IMAGES_SCRIPT, modal)
        seen.update(urls)

        print(f"画像候補数: {len(seen)}")

        before = driver.execute_script("return arguments[0].scrollTop;", modal)
        driver.execute_script("""
            arguments[0].scrollTop += arguments[0].clientHeight * 0.7;
        """, modal)

        time.sleep(pause)

        urls = driver.execute_script(FIND_IMAGES_SCRIPT, modal)
        seen.update(urls)

        if len(seen) == last:
            no_change += 1
        else:
            no_change = 0

        last = len(seen)
        after = driver.execute_script("return arguments[0].scrollTop;", modal)

        if before == after and no_change >= max_no_change:
            break

    return sorted(seen)

# =========================
# ダウンロード
# =========================
def download_images(session, urls):
    os.makedirs(SAVE_DIR, exist_ok=True)

    for i, url in enumerate(urls, 1):
        try:
            if not url or url.startswith("data:"):
                continue

            res = session.get(url, timeout=30)
            res.raise_for_status()

            ext = get_extension(res, url)

            filename = get_filename_from_url(url)
            if not filename:
                filename = f"image_{i:03d}{ext}"

            if "." not in filename:
                filename += ext

            filename = sanitize_filename(filename)
            filename = make_unique_filename(SAVE_DIR, filename)

            path = os.path.join(SAVE_DIR, filename)

            with open(path, "wb") as f:
                f.write(res.content)

            print(f"✅ 保存: {filename}")

        except Exception as e:
            print(f"❌ 失敗: {url} / {e}")

# =========================
# メイン
# =========================
def main():
    url = input("👉 URL入力: ").strip()
    if not url:
        return

    if not url.startswith("http"):
        url = "https://" + url

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        input("👉 ログイン＆モーダル表示後 Enter:")

        modal = find_scrollable_modal(driver)

        if modal:
            urls = auto_scroll_collect(driver, modal)
        else:
            urls = driver.execute_script(FIND_IMAGES_SCRIPT, None)

        print(f"最終画像数: {len(urls)}")

        session = requests.Session()
        for c in driver.get_cookies():
            session.cookies.set(c["name"], c["value"])

        download_images(session, urls)

        print("🎉 完了")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()