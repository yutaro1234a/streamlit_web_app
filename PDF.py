from PIL import Image
import os
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# ===== 自然順ソート用 =====
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

# ===== 対象拡張子 =====
target_exts = (".webp", ".jpg", ".jpeg", ".png")

# ===== フォルダ選択 =====
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

folder = filedialog.askdirectory(title="画像フォルダを選択してください")

if not folder:
    raise Exception("フォルダが選択されませんでした")

# ===== 出力PDF名入力 =====
pdf_name = simpledialog.askstring(
    "PDFファイル名入力",
    "出力するPDFファイル名を入力してください（拡張子 .pdf は不要）",
    initialvalue="output",
    parent=root
)

if not pdf_name:
    raise Exception("PDFファイル名が入力されませんでした")

if not pdf_name.lower().endswith(".pdf"):
    pdf_name += ".pdf"

output_pdf = os.path.join(folder, pdf_name)

# ===== 画像ファイル取得（大文字対応）=====
files = [f for f in os.listdir(folder) if f.lower().endswith(target_exts)]
files = sorted(files, key=natural_sort_key)

if not files:
    raise Exception("WebP / JPG / JPEG ファイルが見つかりません")

images = []

for f in files:
    path = os.path.join(folder, f)
    try:
        img = Image.open(path)

        # ===== 透過対応（白背景）=====
        if img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")

        images.append(img)
        print(f"✅ 読み込み成功: {f}")

    except Exception as e:
        print(f"⚠️ スキップ（読み込み失敗）: {f} - {e}")

if not images:
    raise Exception("有効な画像がありません")

# ===== PDF保存 =====
images[0].save(
    output_pdf,
    save_all=True,
    append_images=images[1:]
)

print(f"\n🎉 PDF作成完了: {output_pdf}")
messagebox.showinfo("完了", f"PDF作成完了\n{output_pdf}")