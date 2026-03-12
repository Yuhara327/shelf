# 画像・バーコード関連
from PIL import Image
from pillow_heif import register_heif_opener
from pyzbar.pyzbar import decode
import asyncio
import os
import cv2

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

# 利用可能なカメラのリストを取得する関数を追加
def list_available_cameras(max_to_test=3):
    """
    接続されているカメラを愚直に走査してリストを返す
    """
    available_indices = []
    for i in range(max_to_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_indices.append(i)
            cap.release()
    return available_indices
async def read_barcode_from_camera(camera_index=0, resolution=(640, 480)):
    # 1. シンプルな接続試行（リトライなし）
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        yield {"status": "CAMERA_UNAVAILABLE", "frame": None, "new_isbns": []}
        return
    
    # 2. 解像度の設定
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    detected_isbns = set()

    try:
        while True:
            # 3. シンプルなフレーム取得（ウォームアップの待機ループを削除）
            ret, frame = cap.read()
            if not ret:
                # フレームが取得できなくなったらエラーとしてループを抜ける
                yield {"status": "READ_ERROR", "frame": None, "new_isbns": []}
                break

            # 4. 画像処理とバーコード解析
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            barcodes = decode(gray_frame)
            
            # 5. 鏡像反転の処理（内蔵カメラは反転、それ以外はそのまま）
            display_frame = cv2.flip(frame, 1) if camera_index == 0 else frame
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # GUIスレッドをブロックしないための非同期スリープ（CPU負荷の軽減）
            await asyncio.sleep(0.01)

            new_detected_isbns = []

            # 6. ISBNの抽出ロジック
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                is_isbn13 = (len(barcode_data) == 13 and 
                             barcode_data.startswith("97") and 
                             barcode_data.isdigit())
                is_isbn10 = (len(barcode_data) == 10 and 
                             barcode_data[:-1].isdigit() and 
                             (barcode_data[-1].isdigit() or barcode_data[-1] == "X"))
                
                if is_isbn13 or is_isbn10:
                    if barcode_data not in detected_isbns:
                        detected_isbns.add(barcode_data)
                        new_detected_isbns.append(barcode_data)
            
            # 7. 結果の返却
            yield {
                "status": "SUCCESS",
                "frame" : frame_rgb,
                "new_isbns": new_detected_isbns
            }
    finally:
        # エラー発生時や、外部からジェネレータが閉じられた際に確実にリソースを解放する
        cap.release()