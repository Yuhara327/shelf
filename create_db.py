import sqlite3
import os
from src.models import db_path


def createdb(filename="library.db"):

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
    conn.close()