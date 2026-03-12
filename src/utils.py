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
    available_indices = []
    for i in range(max_to_test):
        cap = cv2.VideoCapture(i)
        # 0番（内蔵）以外は、少し接続を待ってみる
        if i > 0:
            import time
            time.sleep(0.5) 
        if cap.isOpened():
            available_indices.append(i)
            cap.release()
    
    # iPhoneが自動認識されない場合への対応：
    # 0番しか見つからなくても、連携カメラの可能性を考えて 1 も選択肢に入れる
    if 0 in available_indices and 1 not in available_indices:
        available_indices.append(1) 
        
    return available_indices
async def read_barcode_from_camera(camera_index=0, resolution=(640, 480)):
    cap = None
    retry_limit = 15
    for attempt in range(retry_limit):
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            # 接続成功！
            break
        
        # 失敗したらリソースを解放して、1秒待機
        cap.release()
        print(f"DEBUG: カメラ {camera_index} の接続を試行中... ({attempt + 1}/{retry_limit})")
        await asyncio.sleep(1.0) # ここで非同期に待機
    
    # 15秒待っても開けなかった場合のみ UNAVAILABLE を返す
    if not cap or not cap.isOpened():
        yield {"status": "CAMERA_UNAVAILABLE", "frame": None, "new_isbns": []}
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    detected_isbns = set()

    try:
        # --- 追加：ネットワークカメラ用のウォームアップ待機機構 ---
        failed_reads = 0
        max_failures = 30 # 最大約3秒間（0.1秒 × 30回）フレームの到着を待つ

        while True:
            ret, frame = cap.read()
            if not ret:
                failed_reads += 1
                if failed_reads > max_failures:
                    # 3秒待っても来なければ本当にエラーとして扱う
                    yield {"status": "READ_ERROR", "frame": None, "new_isbns": []}
                    break
                # フレームが届くまで少し待機してループの先頭に戻る
                await asyncio.sleep(0.1)
                continue
            
            # フレームが正常に取得できたらエラーカウンタをリセット
            failed_reads = 0
            # ------------------------------------------------

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            barcodes = decode(gray_frame)
            if camera_index ==0:
                display_frame = cv2.flip(frame, 1)
            else:
                display_frame = frame
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            await asyncio.sleep(0.01)

            new_detected_isbns = []

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
            yield {
                "status": "SUCCESS",
                "frame" : frame_rgb,
                "new_isbns": new_detected_isbns # キーを複数形に統一
            }
    finally:
        cap.release()