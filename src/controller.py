# UIとデータロジックの調整を担う。
from src import models
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog
from src import models, utils
import asyncio
import os


def handle_add_delete(window):
    """
    追加・削除・更新のメインロジック。
    View(window)から入力を受け取り、Model(models)を操作する。modelsの、update_book_if_changedと繋がっている。
    """
    # 1. 追加処理 (ISBN1)
    isbn_add = window.line_edit1.text()
    if isbn_add:
        try:
            # 入力バリデーション
            isbn_add_int = int(isbn_add)
            result = models.addlibrary(isbn_add_int)
            
            if result == "ADD_SUCCEED":
                window.show_info(f"ISBN「{isbn_add}」の本が追加されました。")
            elif result == "ADD_BUT_NO_DATA":
                window.show_error(f"ISBN「{isbn_add}」はAPIにデータがありませんでした。空データを作成しました。")
            elif result == "ALREADY_EXIST":
                window.show_error(f"ISBN「{isbn_add}」は既に登録されています。")
        except ValueError:
            window.show_error("追加ISBNには数字を入力してください。")
        except Exception as e:
            window.show_error(f"追加エラー: {str(e)}")

    # 2. 削除処理の準備
    isbn_to_be_removed = set()
    
    # テキスト入力からの削除 (ISBN2)
    isbn_del_input = window.line_edit2.text()
    if isbn_del_input:
        isbn_to_be_removed.add(isbn_del_input)

    # チェックボックスからの削除
    for row in range(window.tableWidget.rowCount()):
        checkbox_item = window.tableWidget.cellWidget(row, 7)
        if checkbox_item and checkbox_item.isChecked():
            isbn_to_be_removed.add(window.tableWidget.item(row, 0).text())

    # 3. 削除の実行
    for isbn in isbn_to_be_removed:
        result = models.remove_book(isbn)
        if result == "NOT_EXIST":
            window.show_error(f"ISBN「{isbn}」は存在しないため削除できません。")
        elif result == "DELETE_SUCCEED":
            window.show_info(f"ISBN「{isbn}」を削除しました。")

    # 4. テーブル内の変更（既読状態など）を検出してDBを更新
    # ここも本来はmodelsに「一括更新」関数を作るのがソリッドですが、一旦ロジックを移します
    for row in range(window.tableWidget.rowCount()):
        isbn = window.tableWidget.item(row, 0).text()
        # View上の現在の値を取得
        current_data = {
            "title": window.tableWidget.item(row, 1).text(),
            "creator": window.tableWidget.item(row, 2).text(),
            "publisher": window.tableWidget.item(row, 3).text(),
            "issued": window.tableWidget.item(row, 4).text(),
            "classification": window.tableWidget.item(row, 5).text(),
            "readed": int(window.tableWidget.item(row, 6).checkState() == Qt.Checked)
        }
        
        # models側の更新関数を呼び出す（後でmodels.pyにupdate_book_statusなどを作るとより良い）
        models.update_book_if_changed(isbn, current_data)

    # 5. 後処理
    window.line_edit1.clear()
    window.line_edit2.clear()
    window.load_db() # Viewの更新

# フォルダを選択させ、中の画像をバッチ処理する。modelのaddlibraryを呼ぶ。
def handle_batch_images(window):
    # 1. フォルダ選択（Viewの機能を利用）
    folder_path = QFileDialog.getExistingDirectory(window, "フォルダを選択")
    if not folder_path:
        return

    # 2. 対象ファイルの選別
    supported_formats = (".jpg", ".jpeg", ".png", ".heic")
    image_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(supported_formats)
    ]

    if not image_files:
        window.show_info("対象となる画像ファイルが見つかりませんでした。")
        return

    # 3. 非同期処理の実行（utilsの機能を呼び出し）
    async def run_tasks():
        return await asyncio.gather(*[utils.read_barcode(path) for path in image_files])

    # asyncio.run で非同期処理を開始
    results = asyncio.run(run_tasks())

    # 4. 結果の集計とModelへの登録
    added, apierror, already, nobarcode, noisbn = [], [], [], [], []

    for status, value in results:
        if status == "SUCCESS":
            isbn = value
            try:
                # Modelのロジックを呼び出し
                res = models.addlibrary(isbn)
                if res == "ADD_SUCCEED": added.append(isbn)
                elif res == "ADD_BUT_NO_DATA": apierror.append(isbn)
                elif res == "ALREADY_EXIST": already.append(isbn)
            except Exception as e:
                window.show_error(f"ISBN {isbn} の処理中にエラー: {str(e)}")
        elif status == "NOT_BARCODES":
            nobarcode.append(value)
        elif status == "ISBN_NOT_FOUND":
            noisbn.append(value)

    # 5. Viewへの結果通知
    if added: window.show_info(f"追加成功: {added}")
    if apierror: window.show_error(f"データなし（空作成）: {apierror}")
    if already: window.show_error(f"既に存在: {already}")
    if noisbn: window.show_info(f"ISBN未検出: {noisbn}")
    if nobarcode: window.show_info(f"バーコードなし: {nobarcode}")

    # 6. Viewの更新
    window.load_db()