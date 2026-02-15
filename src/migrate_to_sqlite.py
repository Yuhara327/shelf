import sqlite3
import sys
from shelf_gui import Book, load_library_from_file

conn = sqlite3.connect("/Users/soichiro/Documents/shelf/library.db")
cursor = conn.cursor()


# データを追加する関数
def save_book_to_db(book):
    insert_query = """
    INSERT OR REPLACE INTO books (isbn, title, creator, publisher,issued, classification, readed)
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
    conn.commit()


# JSONを読み込んで、データ追加を1行ずつやる
def migrate_data_to_db():
    library = load_library_from_file()
    for book in library:
        save_book_to_db(book)
        print(f"dbに追加:{book.title}")


# マイグレーションの実行
migrate_data_to_db()
# データベースを閉じる
conn.close()
