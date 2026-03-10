# 画像・バーコード関連
from PIL import Image
from pillow_heif import register_heif_opener
from pyzbar.pyzbar import decode
import asyncio
import os

# PILにHEICサポートを追加
register_heif_opener()

# 画像のリサイズとデコード
async def process_image(image_path):
    loop = asyncio.get_event_loop()
    # run in executorを使ってimage.openをバックグラウンド
    img = await loop.run_in_executor(None, Image.open, image_path)
    img = img.convert("RGB")
    img = img.resize((640, 480))
    return img

# バーコードからisbnを取得する。
async def read_barcode(image_path):
    img = await process_image(image_path)
    file_name = os.path.basename(image_path)
    # でこーど
    barcodes = decode(img)

    if not barcodes:
        return "NOT_BARCODES" , file_name

    for barcode in barcodes:
        # データ取得
        barcode_data = barcode.data.decode("utf-8")
        # isbn13
        if (
            len(barcode_data) == 13
            and barcode_data.isdigit()
            and barcode_data.startswith("97")
        ):
            return "SUCCESS", barcode_data  # ISBN13が見つかれば返す
        if len(barcode_data) == 10 and (
            barcode_data[:-1].isdigit()
            and (barcode_data[-1].isdigit() or barcode_data[-1] == "X")
        ):
            return "SUCCESS", barcode_data  # ISBN10が見つかれば返す

    return "ISBN_NOT_FOUND", file_name