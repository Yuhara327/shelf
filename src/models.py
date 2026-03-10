# データの操作を担う
import os
import urllib.error
import urllib.request
import xmltodict
from src.book import Book
import sqlite3


# データベースファイルの完全パスを作る。
# ユーザーのホームディレクトリを取得
home_directory = os.path.expanduser("~")
# 'Documents/Shelf/'ディレクトリに結合してフルパスを作成
library_dir = os.path.join(home_directory, "Documents", "Shelf")
db_path = os.path.join(library_dir, "library.db")

# APIから文字列データ(xml)を取得する。
def getdata(isbn):
    global bookdata
    url = f"http://iss.ndl.go.jp/api/opensearch?isbn={isbn}"
    try:
        urlopen = urllib.request.urlopen(url)
        bookdata = xmltodict.parse(urlopen.read().decode("utf-8"))
        return bookdata
    except urllib.error.URLError as e:
        raise Exception(f"データ取得中に接続エラーが発生しました: {str(e)}")
    except Exception as e:
        raise Exception(f"予期しないエラーが発生しました1: {str(e)}")
    
# getdataから受け取った文字列をbook型にして返す。
def create_book_from_data(isbn, bookdata):
    isbn = f"{isbn}"
    items = bookdata.get("rss", {}).get("channel", {}).get("item", [])
    # apiが何も返さなかったら、データがないことを示した上で、isbnのみのデータを作成。
    if not items:
        return Book(isbn, "", "", "", ""), "API_NOT_FOUND"

    # itemがリストの場合、最初のエントリを使用
    if isinstance(items, list):
        item = items[0]
    else:
        item = items
    title1 = item.get("dc:title")
    title2 = item.get("dcndl:volume", "")
    title = f"{title1} {title2}"
    # creator がリスト型の場合、カンマ区切りの文字列に変換
    creator = item.get("dc:creator")
    if isinstance(creator, list):
        creator = ", ".join(creator)
    else:
        creator = creator
    company = item.get("dc:publisher")
    series = item.get("dcndl:seriesTitle", "")
    publisher = f"{company}, {series}"
    issued = item.get("dcterms:issued")

    # Bookインスタンスを生成
    return Book(isbn, title, creator, publisher, issued), "SUCCESS"

# bookを受け取って、dbに保存する。
def save_to_book_db(books):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    insert_query = """
        INSERT OR REPLACE INTO books (isbn, title, creator, publisher, issued, classification, readed)
        VALUES ( ?, ?, ?, ?, ?, ?, ?)
    """
    if isinstance(books, Book):  # 単一のBookオブジェクトの場合
        books = [books]  # リストに変換
    
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

# isbnを受け取って、本を削除する。
def remove_book(isbn):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 存在するか確認
    select_query = "SELECT * FROM books WHERE isbn=?"
    cursor.execute(select_query, (isbn,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        return "NOT_EXIST"
    # 存在すれば削除
    delete_query = "DELETE FROM books WHERE isbn=?"
    cursor.execute(delete_query, (isbn,))
    conn.commit()
    conn.close()
    return "DELETE_SUCCEED"

# isbnを受け取ってgetdata、create_book_from_data、save_to_book_dbを順番に実行、本を追加。
def addlibrary(isbn):
    if not isbn:
        return
    # 存在するか確認
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    select_query = "SELECT * FROM books WHERE isbn=?"
    cursor.execute(select_query, (isbn,))
    book = cursor.fetchone()
    if not book:
        bookdata = getdata(isbn)
        book_obj, status = create_book_from_data(isbn, bookdata)
        save_to_book_db(book_obj)
        conn.commit()
        conn.close()
        if status == "API_NOT_FOUND":
            return "ADD_BUT_NO_DATA"
        return "ADD_SUCCEED"
    else:
        conn.commit()
        conn.close()
        return "ALREADY_EXIST"
    
# DBから全データ取得し、bookオブジェクトのリストを返す。viewsのload_dbと繋がっている。
def get_all_books():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    conn.close()

    return [
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

# viewから送られてきたデータを見て、差分があれば更新。controllerのhandle_add_deleteと繋がっている
def update_book_if_changed(isbn, new_data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM books WHERE isbn = ?", (isbn,))
    book = cursor.fetchone()
    
    if book:
        # 差分チェック（タイトル、著者、出版社、発行日、分類、既読）
        if (new_data["title"] != book[1] or 
            new_data["creator"] != book[2] or 
            new_data["publisher"] != book[3] or 
            new_data["issued"] != book[4] or 
            new_data["classification"] != book[5] or 
            new_data["readed"] != book[6]):
            
            update_query = """
            UPDATE books SET title=?, creator=?, publisher=?, issued=?, classification=?, readed=? WHERE isbn=?
            """
            cursor.execute(update_query, (
                new_data["title"], new_data["creator"], new_data["publisher"], 
                new_data["issued"], new_data["classification"], new_data["readed"], isbn
            ))
            conn.commit()
    conn.close()