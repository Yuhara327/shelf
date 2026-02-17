import sqlite3
import os


def createdb(filename="library.db"):
    # データベースファイルの完全パスを指定します。
    # ユーザーのホームディレクトリを取得
    home_directory = os.path.expanduser("~")
    # 'Documents/Shelf/'ディレクトリに結合してフルパスを作成
    library_dir = os.path.join(home_directory, "Documents", "Shelf")
    db_path = os.path.join(library_dir, filename)

    # ディレクトリが存在しない場合は作成します。
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # データベースに接続します。
    global conn
    conn = sqlite3.connect(db_path)

    # カーソルオブジェクトを作成します。
    global cursor
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
    conn.close()
