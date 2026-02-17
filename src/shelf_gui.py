import json
import urllib.error
import xmltodict
import urllib.request
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QHBoxLayout,
    QWidgetAction,
)
from PySide6.QtCore import Qt, Slot
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from pyzbar.pyzbar import decode
from PIL import Image
from pillow_heif import register_heif_opener
import asyncio
import sqlite3
from create_db import createdb

# SQLiteデータベースがあるかどうか。なければ作成
createdb()

# PILにHEICサポートを追加
register_heif_opener()


# APIを叩いて文字列を返す
def getdata(isbn):
    global bookdata
    url = f"http://iss.ndl.go.jp/api/opensearch?isbn={isbn}"
    try:
        urlopen = urllib.request.urlopen(url)
        bookdata = xmltodict.parse(urlopen.read().decode("utf-8"))
        return bookdata
    except urllib.error.URLError as e:
        mainwindow.show_error(f"データ取得中に接続エラーが発生しました: {str(e)}")
        return
    except Exception as e:
        mainwindow.show_error(f"予期しないエラーが発生しました1: {str(e)}")
        return


# Bookクラス
class Book:
    def __init__(
        self, isbn, title, creator, publisher, issued, classification="", readed=False
    ):
        self.isbn = isbn
        self.title = title
        self.creator = creator
        self.publisher = publisher
        self.issued = issued
        self.classification = classification  # classificationをデフォルトでNoneに設定
        self.readed = readed

    def __repr__(self):
        return f"Book(ISBN={self.isbn}, Title={self.title}, Creator={self.creator}, Publisher={self.publisher}, Issued={self.issued}, Classification={self.classification}, readed={self.readed})"

    # # JSONに保存できる形式に変換(SQL化に伴い不要に)
    # def to_dict(self):
    #     return {
    #         "isbn": self.isbn,
    #         "title": self.title,
    #         "creator": self.creator,
    #         "publisher": self.publisher,
    #         "issued": self.issued,
    #         "classification": self.classification,
    #         "readed": self.readed,
    #     }

    # # JSONからオブジェクトを作成
    # @staticmethod
    # def from_dict(data):
    #     return Book(
    #         isbn=data["isbn"],
    #         title=data["title"],
    #         creator=data["creator"],
    #         publisher=data["publisher"],
    #         issued=data["issued"],
    #         classification=data.get("classification"),  # classificationはオプション
    #         readed=data.get("readed"),
    #     )


# インスタンス作成。API叩きから文字列を受け取ってbookクラスを返す関数。
def create_book_from_data(isbn, bookdata):
    isbn = f"{isbn}"
    items = bookdata.get("rss", {}).get("channel", {}).get("item", [])
    # apiが何も返さなかったら、データがないことを示した上で、isbnのみのデータを作成。
    if not items:
        mainwindow.apierror.append(isbn)
        return Book(isbn, "", "", "", "")

    # itemがリストの場合、最初のエントリを使用
    if isinstance(items, list):
        item = items[0]
    else:
        item = items
    title1 = item.get("dc:title")
    title2 = item.get("dcndl:volume", "")
    title = f"{title1} {title2}"
    creator = item.get("dc:creator")
    company = item.get("dc:publisher")
    series = item.get("dcndl:seriesTitle", "")
    publisher = f"{company}, {series}"
    issued = item.get("dcterms:issued")

    # Bookインスタンスを生成
    return Book(isbn, title, creator, publisher, issued)


# データベースに本を保存
def save_to_book_db(books):
    conn = sqlite3.connect("books.db")
    cursor = conn.cursor()
    insert_query = """
        INSERT OR REPLACE INTO books (isbn, title, creator, publisher, issued, classification, readed)
        VALUES ( ?, ?, ?, ?, ?, ?, ?)
    """
    for book in books:
        cursor.execute(
            insert_query,
            (
                book.isbn,
                book.title,
                book.creator,
                book.publisher,
                book.issued,
                book.classification if book.classification is not None else "",
                int(book.readed),
            ),
        )

    conn.commit()
    conn.close()


# # ファイルに保存(SQL化のため不要)
# def save_library_to_file(library, filename="library.json"):
#     # ユーザーのホームディレクトリを取得
#     home_directory = os.path.expanduser("~")
#     # 'Documents/Shelf/'ディレクトリに結合してフルパスを作成
#     library_dir = os.path.join(home_directory, "Documents", "Shelf")
#     library_path = os.path.join(library_dir, filename)

#     # 'Documents/Shelf' ディレクトリが存在しない場合、作成する
#     if not os.path.exists(library_dir):
#         os.makedirs(library_dir)

#     # 'library.json' が存在しない場合、空のファイルを作成
#     if not os.path.exists(library_path):
#         with open(library_path, "w", encoding="utf-8") as f:
#             json.dump([], f)  # 空のリストをJSONとして保存

#     with open(library_path, "w", encoding="utf-8") as f:
#         json.dump(
#             [book.to_dict() for book in library], f, ensure_ascii=False, indent=4
#         )  # Bookインスタンスから辞書に変換して保存


# # ファイル読み込み(jsonを読んでbookを返す(不要))
# def load_library_from_file(filename="library.json"):
#     # ユーザーのホームディレクトリを取得
#     home_directory = os.path.expanduser("~")
#     # 'Documents/Shelf/'ディレクトリに結合してフルパスを作成
#     library_dir = os.path.join(home_directory, "Documents", "Shelf")
#     library_path = os.path.join(library_dir, filename)
#     # 例外処理
#     ## 'Documents/Shelf' ディレクトリが存在しない場合、作成する
#     if not os.path.exists(library_dir):
#         os.makedirs(library_dir)
#     ## 'library.json' が存在しない場合、空のファイルを作成
#     if not os.path.exists(library_path):
#         with open(library_path, "w", encoding="utf-8") as f:
#             json.dump([], f)  # 空のリストをJSONとして保存
#             mainwindow.show_info("library.jsonが書類/Shelfに作成されています。")
#     # ファイルを読み込み
#     try:
#         with open(library_path, "r", encoding="utf-8") as f:
#             books_lib = json.load(f)
#             return [
#                 Book.from_dict(data) for data in books_lib
#             ]  # 辞書からBookインスタンスに変換
#     except json.JSONDecodeError:
#         mainwindow.show_error(
#             "library.jsonが破損しています。データを空として読み込みます。"
#         )
#         return []  # データが壊れている場合、空のリストを返す


# 削除(bookから消してファイルに保存する(要修正))
# def remove_book(isbn):
#     if not isbn:
#         return

#     library = load_library_from_file()

#     book_to_remove = next((book for book in library if book.isbn == str(isbn)), None)

#     if book_to_remove:
#         library.remove(book_to_remove)
#         save_library_to_file(library)
#         mainwindow.show_info(f"ISBN: {isbn} の本は削除されました。")
#     else:
#         mainwindow.show_error(f"ISBN: {isbn} はライブラリに存在しません。")
#         return


# 本を削除
def remove_book(isbn):
    conn = sqlite3.connect("books.db")
    cursor = conn.cursor()
    # 存在するか確認
    select_query = "SELECT * FROM books WHERE isbn=?"
    cursor.execute(select_query, (isbn,))
    book = cursor.fetchone()
    if not book:
        mainwindow.nobook.append()
        conn.commit()
        conn.close()
        return
    # 存在すれば削除
    delete_query = "DELETE FROM books WHERE isbn=?"
    cursor.execute(delete_query, (isbn,))
    conn.commit()
    conn.close()
    mainwindow.removed.append(isbn)


# 追加(api叩き、bookインスタンス作成し、libraryに追加)
def addlibrary(isbn):
    if not isbn:
        return
    # 存在するか確認
    conn = sqlite3.connect("books.db")
    cursor = conn.cursor()
    select_query = "SELECT * FROM books WHERE isbn=?"
    cursor.execute(select_query, (isbn,))
    book = cursor.fetchone()
    if not book:
        bookdata = getdata(isbn)
        book = create_book_from_data(isbn, bookdata)
        save_to_book_db(book)
        conn.commit()
        conn.close()
        mainwindow.added.append(isbn)
        return
    else:
        mainwindow.already.append(isbn)
        conn.commit()
        conn.close()
        return


# 画像のリサイズとデコード
async def process_image(image_path):
    loop = asyncio.get_event_loop()
    # run in executorを使ってimage.openをバックグラウンド
    img = await loop.run_in_executor(None, Image.open, image_path)
    img = img.convert("RGB")
    img = img.resize((640, 480))
    return img


# バーコードからisbnを取得するぞ
async def read_barcode(image_path):
    img = await process_image(image_path)
    # でこーど
    barcodes = decode(img)

    if not barcodes:
        mainwindow.nobarcode.append(os.path.basename(image_path))
        return None

    for barcode in barcodes:
        # データ取得
        barcode_data = barcode.data.decode("utf-8")
        # isbn13
        if (
            len(barcode_data) == 13
            and barcode_data.isdigit()
            and barcode_data.startswith("97")
        ):
            return barcode_data  # ISBN13が見つかれば返す
        if len(barcode_data) == 10 and (
            barcode_data[:-1].isdigit()
            and (barcode_data[-1].isdigit() or barcode_data[-1] == "X")
        ):
            return barcode_data  # ISBN10が見つかれば返す

    mainwindow.noisbn.append(os.path.basename(image_path))
    return None  # どれも一致しなければNoneを返す


# GUI
class Window(QWidget):
    def __init__(self):
        self.info_msg = None
        # ウィンドウの設定
        super().__init__()
        self.setWindowTitle("Shelf")
        self.setGeometry(100, 100, 1300, 900)
        vertical_layout = QVBoxLayout()
        self.setLayout(vertical_layout)
        # widgetsの用意
        self.line_edit1 = QLineEdit(self, placeholderText="追加する本のISBNコード")
        self.line_edit2 = QLineEdit(self, placeholderText="削除する本のISBNコード")
        self.label1 = QLabel("追加")
        self.label2 = QLabel("削除")
        self.button = QPushButton("保存(変更後、必ず押してください！)")
        self.button.setDefault(True)
        self.button.setShortcut(
            Qt.KeyboardModifier.ControlModifier | Qt.Key_S
        )  # Ctrl+S
        self.button.clicked.connect(self.add_delete)
        self.line_edit1.returnPressed.connect(self.button.click)
        self.line_edit2.returnPressed.connect(self.button.click)
        self.filebutton = QPushButton("バーコードの画像ファイルから追加")
        self.filebutton.clicked.connect(self.choose_folder)
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("検索")
        self.search_box.textChanged.connect(self.search_table)
        self.search_box.setFixedWidth(300)  # 検索ボックスの幅を固定（適度なサイズ)
        # QActionを作成してショートカットを設定
        focus_action = QWidgetAction(self)
        focus_action.setShortcut("Ctrl+F")
        focus_action.triggered.connect(self.focus_search_box)
        # ショートカットをウィンドウ全体で有効にする
        self.addAction(focus_action)
        search_layout = QHBoxLayout()
        search_layout.addStretch()  # 左側に余白を確保
        ## 表の作成
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(8)  # 列数の設定
        self.tableWidget.setSortingEnabled(True)
        loadButton = QPushButton("再読み込み")
        loadButton.setShortcut(Qt.KeyboardModifier.ControlModifier | Qt.Key_R)  # Ctrl+R
        loadButton.clicked.connect(self.load_db)
        # layoutに配置
        search_layout.addWidget(self.search_box)
        vertical_layout.addLayout(search_layout)
        vertical_layout.addWidget(self.tableWidget)
        vertical_layout.addWidget(loadButton)
        sublayout = QGridLayout()
        sublayout.addWidget(self.label1, 0, 0)
        sublayout.addWidget(self.line_edit1, 0, 1)
        sublayout.addWidget(self.label2, 0, 2)
        sublayout.addWidget(self.line_edit2, 0, 3)
        vertical_layout.addLayout(sublayout)
        vertical_layout.addWidget(self.button)
        vertical_layout.addWidget(self.filebutton)

        self.added = []
        self.apierror = []
        self.already = []
        self.nobarcode = []
        self.noisbn = []
        self.nobook = []
        self.removed = []

    # 表を読む関数
    def load_db(self):
        # 初期化
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)  # 行数をリセット
        self.tableWidget.setHorizontalHeaderLabels(
            [
                "ISBN",
                "Title",
                "Creator",
                "Publisher",
                "Issued",
                "Classification",
                "Readed",
                "Delete",
            ]
        )
        # ソートを一時的に無効化
        self.tableWidget.setSortingEnabled(False)
        # db読み込み
        # データベースから読み込み
        conn = sqlite3.connect("books.db")
        cursor = conn.cursor()
        select_query = "SELECT * FROM books"
        cursor.execute(select_query)
        rows = cursor.fetchall()
        library = [
            Book(
                isbn=row[0],
                title=row[1],
                creator=row[2],
                publisher=row[3],
                issued=row[4],
                classification=row[5] if row[5] else "",
                readed=bool(row[6]),
            )
            for row in rows
        ]
        # 行数の設定
        self.tableWidget.setRowCount(len(library))

        # テーブルに表示
        for row, item in enumerate(library):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(item.isbn))
            self.tableWidget.setItem(
                row,
                1,
                QTableWidgetItem(
                    ", ".join(item.title)
                    if isinstance(item.title, list)
                    else item.title or "No Title"
                ),
            )
            self.tableWidget.setItem(
                row,
                2,
                QTableWidgetItem(
                    ", ".join(item.creator)
                    if isinstance(item.creator, list)
                    else item.creator or "No Creator"
                ),
            )
            self.tableWidget.setItem(
                row,
                3,
                QTableWidgetItem(
                    ", ".join(item.publisher)
                    if isinstance(item.publisher, list)
                    else item.publisher or "No Publisher"
                ),
            )
            self.tableWidget.setItem(row, 4, QTableWidgetItem(item.issued))
            self.tableWidget.setItem(
                row, 5, QTableWidgetItem(item.classification)
            )  # Classificationを表示
            # 既読チェックボックス
            # 既読チェックボックスをQTableWidgetItemとして設定
            readed_item = QTableWidgetItem()
            readed_item.setFlags(
                Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            )  # チェック可能にする
            readed_item.setCheckState(
                Qt.Checked if item.readed else Qt.Unchecked
            )  # 初期状態をitem.readedで設定
            self.tableWidget.setItem(
                row, 6, readed_item
            )  # setCellWidgetではなくsetItemを使用
            # 削除ようチェックボックス
            checkbox = QCheckBox()
            self.tableWidget.setCellWidget(row, 7, checkbox)

        # 列幅指定
        # 列の幅を設定 (例えば、列ごとに幅を指定)
        self.tableWidget.setColumnWidth(0, 150)  # ISBN列の幅を150に設定
        self.tableWidget.setColumnWidth(1, 300)  # Title列の幅を200に設定
        self.tableWidget.setColumnWidth(2, 150)  # Creator列の幅を150に設定
        self.tableWidget.setColumnWidth(3, 300)  # Publisher列の幅を150に設定
        self.tableWidget.setColumnWidth(4, 100)  # Issued列の幅を120に設定
        self.tableWidget.setColumnWidth(5, 100)
        self.tableWidget.setColumnWidth(6, 50)
        self.tableWidget.setColumnWidth(7, 42)

        # ソートを有効化
        self.tableWidget.setSortingEnabled(True)
        conn.commit()
        conn.close()
        self.show_info("データベースファイルがリロードされました。")

    # OKボタン
    def add_delete(self):
        self.apierror = []
        self.already = []
        self.added = []
        self.nobarcode = []
        self.noisbn = []
        self.nobook = []
        self.removed = []
        isbn1 = self.line_edit1.text()
        if isbn1:
            try:
                isbn1 = int(isbn1)
                addlibrary(isbn1)
            except ValueError:
                self.show_error("入力欄には整数を入力してください。")
            except Exception as e:
                self.show_error(f"予期しないエラーが発生しました2: {str(e)}")
            if self.added:
                self.show_info(f"ISBN{self.added} の本が追加されました。")
            if self.apierror:
                self.show_error(
                    f"ISBN{self.apierror}の本は、国会図書館APIにデータが存在しませんでした。"
                )
            if self.already:
                self.show_error(f"ISBN{self.already}の本は、すでに登録されています。")
            if self.noisbn:
                self.show_info(
                    f"{self.noisbn}内のバーコードは、ISBNと認識できませんでした。"
                )
            if self.nobarcode:
                self.show_info(
                    f"{self.nobarcode}内に、バーコードを認識できませんでした。"
                )
        # 削除対象のISBNを収集するリスト
        isbn_to_be_removed = set()
        # ユーザー入力により削除する本をリストに追加
        isbn2 = self.line_edit2.text()
        if isbn2:
            try:
                isbn_to_be_removed.add(isbn2)
            except ValueError:
                self.show_error("入力欄には整数を入力してください。")
            except Exception as e:
                self.show_error(f"予期しないエラーが発生しました3: {str(e)}")

        # チェックボックスで選ばれた本をリストに追加
        for row in range(self.tableWidget.rowCount()):
            checkbox_item = self.tableWidget.cellWidget(
                row, 7
            )  # チェックボックス列（7列目）のアイテム
            if checkbox_item and checkbox_item.isChecked():  # チェックされている場合
                isbn_to_be_removed.add(
                    self.tableWidget.item(row, 0).text()
                )  # ISBN列（1列目）の値を取得
        for isbn in isbn_to_be_removed:
            remove_book(isbn)

        if self.nobook:
            self.show_error(f"iSBN{self.nobook}の本は存在しないため削除できません。")
        if self.removed:
            self.show_info(f"iSBN{self.removed}の本は削除されました。")

        # 以下、全ての更新を一度に行う。
        self.load_db()  # ライブラリの情報を一回読み込む
        # isbnをキーとした辞書型に変換
        bookdic = {book.isbn: book for book in library}
        # テーブル上の値を取得し、変更があるかどうか整合*全ての行繰り返す
        for row in range(self.tableWidget.rowCount()):
            isbn = self.tableWidget.item(row, 0).text()  # ISBN（1列目）の値を取得
            title = self.tableWidget.item(row, 1).text()  # Title（2列目）の値を取得
            creator = self.tableWidget.item(row, 2).text()  # Creator（3列目）の値を取得
            publisher = self.tableWidget.item(
                row, 3
            ).text()  # Publisher（4列目）の値を取得
            issued = self.tableWidget.item(row, 4).text()  # Issued（5列目）の値を取得
            classification = self.tableWidget.item(
                row, 5
            ).text()  # Classification列（6列目）の値を取得
            readed_item = self.tableWidget.item(row, 6)  # 既読チェックボックス（7列目）

            book_to_update = bookdic.get(
                isbn
            )  # isbnをキーにして辞書からBookオブジェクトを取得
            if book_to_update:  # 辞書にあるなら、(まああるんだけど)
                # 以下、データとGUIの入力が異なるなら上書き。
                # title ~ issuedに関しては、空文字の場合は無視する。
                if title and book_to_update.title != title:
                    book_to_update.title = title
                if creator and book_to_update.creator != creator:
                    book_to_update.creator = creator
                if publisher and book_to_update.publisher != publisher:
                    book_to_update.publisher = publisher
                if issued and book_to_update.issued != issued:
                    book_to_update.issued = issued
                if book_to_update.classification != classification:
                    book_to_update.classification = classification
                isChecked = readed_item.checkState() == Qt.Checked
                if book_to_update.readed != isChecked:
                    book_to_update.readed = isChecked

        # (さっきデータを辞書に格納→classification と readed を更新したので、その中から、)削除対象以外の本を保存
        book_to_save = [
            book for isbn, book in bookdic.items() if isbn not in isbn_to_be_removed
        ]
        # 保存
        save_to_book_db(book_to_save)

        self.line_edit1.clear()
        self.line_edit2.clear()

        self.load_db()

    # 画像ファイルから追加ボタンで呼ばれる
    def choose_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if folder_path:
            self.images_in_folder(folder_path)

    # 画像ファイルを選別して追加
    def images_in_folder(self, path):
        supported_formats = (".jpg", ".jpeg", ".png", ".heic")
        image_files = [
            os.path.join(path, filename)
            for filename in os.listdir(path)
            if filename.lower().endswith(supported_formats)
        ]
        # ThreadPoolExecutorを使って並列処理
        with ThreadPoolExecutor(
            max_workers=os.cpu_count()
        ) as executor:  # スレッド数は調整可能
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                asyncio.gather(
                    *[read_barcode(image_path) for image_path in image_files]
                )
            )
        for isbn in results:
            if isbn:
                try:
                    addlibrary(isbn)
                except ValueError as e:
                    self.show_error(e)
        if self.added:
            self.show_info(f"ISBN{self.added} の本が追加されました。")
        if self.apierror:
            self.show_error(
                f"ISBN{self.apierror}の本は、国会図書館APIにデータが存在しませんでした。"
            )
        if self.already:
            self.show_error(f"ISBN{self.already}の本は、すでに登録されています。")
        if self.noisbn:
            self.show_info(
                f"{self.noisbn}内のバーコードは、ISBNと認識できませんでした。"
            )
        if self.nobarcode:
            self.show_info(f"{self.nobarcode}内に、バーコードを認識できませんでした。")
        self.load_db()

    # 検索関数
    def search_table(self):
        keyword = self.search_box.text().lower()
        for row in range(self.tableWidget.rowCount()):
            match = False
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, col)
                if item and keyword in item.text().lower():
                    match = True
                    break
            self.tableWidget.setRowHidden(row, not match)  # 該当しない行を非表示

    def focus_search_box(self):
        """検索ボックスにフォーカスを移動"""
        self.search_box.setFocus()
        self.search_box.selectAll()  # オプションでテキストを全選択

    @Slot(str)
    def show_error(self, message: str):
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)  # アイコンをエラーに設定
        error_msg.setText(message)  # メッセージを設定
        error_msg.setWindowTitle("エラー")  # タイトルを設定
        error_msg.exec()  # ダイアログを表示

    @Slot(str)
    def show_info(self, message: str):
        info_msg = QMessageBox()
        info_msg.setIcon(QMessageBox.Icon.Information)  # アイコンを情報に設定
        info_msg.setText(message)  # メッセージを設定
        info_msg.setWindowTitle("情報")  # タイトルを設定
        info_msg.exec()  # ダイアログを表示


# 表示
qAp = QApplication(sys.argv)
mainwindow = Window()
mainwindow.show()
qAp.exec()
