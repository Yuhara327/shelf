import sqlite3
import os

# データベースファイルの完全パスを指定します。
db_path = "/Users/soichiro/Documents/shelf/library.db"

# ディレクトリが存在しない場合は作成します。
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# データベースに接続します。
conn = sqlite3.connect(db_path)
    
# カーソルオブジェクトを作成します。
cursor = conn.cursor()
    
# テーブルを作成します。
create_table_query = '''
    CREATE TABLE IF NOT EXISTS books (
        isbn TEXT PRIMARY KEY,
        title TEXT,
        creator TEXT,
        publisher TEXT,
        issued TEXT,
        classification TEXT,
        readed BOOLEAN DEFAULT FALSE
    )
'''
cursor.execute(create_table_query)
    
# コミットして変更を保存します。
conn.commit()
conn.close()