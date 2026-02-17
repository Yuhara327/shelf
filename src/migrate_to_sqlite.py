import sqlite3
import sys
import os
from shelf_gui import Book, load_library_from_json

def createdb(filename="library.db"):
    # ユーザーのホームディレクトリを取得
    home_directory = os.path.expanduser("~")
    # 'Documents/Shelf/'ディレクトリに結合してフルパスを作成
    library_dir = os.path.join(home_directory, "Documents", "Shelf")
    db_path = os.path.join(library_dir, filename)

    # ディレクトリが存在しない場合は作成します。
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # データベースに接続します。
    conn = sqlite3.connect(db_path)

    # カーソルオブジェクトを作成します。
    cursor = conn.cursor()

    # テーブルを作成します。
    create_table_query = """
        CREATE TABLE IF NOT EXISTS books (
            isbn TEXT PRIMARY KEY,
            title TEXT,
            creator TEXT,
            publisher TEXT,
            issued TEXT,
            classification TEXT,
            readed BOOLEAN DEFAULT FALSE
        )
    """
    cursor.execute(create_table_query)
    conn.commit()
    return conn, cursor

# データを追加する関数
def save_book_to_db(book, cursor):
    insert_query = """
    INSERT OR REPLACE INTO books (isbn, title, creator, publisher, issued, classification, readed)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(
        insert_query,
        (
            book.isbn,
            book.title,
            book.creator,
            book.publisher,
            book.issued,
            book.classification,
            int(book.readed),
        ),
    )

# JSONを読み込んで、データ追加を1行ずつやる
def migrate_data_to_db():
    conn, cursor = createdb()
    library = load_library_from_json()
    for book in library:
        save_book_to_db(book, cursor)
        print(f"dbに追加: {book.title}")
    
    # データベースを閉じる
    conn.commit()
    conn.close()

# マイグレーションの実行
if __name__ == "__main__":
    migrate_data_to_db()
