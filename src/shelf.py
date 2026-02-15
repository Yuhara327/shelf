import json
import urllib
import xmltodict
import os

# API叩き
def getdata(isbn):
    global bookdata
    url = f'http://iss.ndl.go.jp/api/opensearch?isbn={isbn}'
    urlopen = urllib.request.urlopen(url)
    bookdata = xmltodict.parse(urlopen.read().decode('utf-8'))
    return bookdata

# Bookクラス
class Book:
    def __init__ (self, isbn, title, creator, publisher, issued, classification = "", readed = False):
        self.isbn = isbn
        self.title = title
        self.creator = creator
        self.publisher = publisher
        self.issued = issued
        self.classification = classification
        self.readed = readed

    def __repr__(self):
        return f"Book(ISBN={self.isbn}, Title={self.title}, Creator={self.creator}, Publisher={self.publisher}, Issued={self.issued}, Classification-{self.classification}, readed={self.readed})"

# インスタンス作成
def create_book_from_data(isbn, bookdata):
    isbn = f"{isbn}"
    title = bookdata.get('rss', {}).get('channel', {}).get('item', {}).get('dc:title')
    creator = bookdata.get('rss', {}).get('channel', {}).get('item', {}).get('dc:creator')
    publisher = bookdata.get('rss', {}).get('channel', {}).get('item', {}).get('dc:publisher')
    issued = bookdata.get('rss', {}).get('channel', {}).get('item', {}).get('dcterms:issued')


    # Bookインスタンスを生成
    return Book(isbn, title, creator, publisher, issued)

# ファイルに保存
def save_library_to_file(library, filename="library.json"):
    with open (filename, "w", encoding = "utf-8") as f:
        json.dump([book.__dict__ for book in library], f, ensure_ascii=False, indent=4)

# ファイル読み込み
def load_library_from_file(filename="library.json"):
    # ユーザーのホームディレクトリを取得
    home_directory = os.path.expanduser("~")
    # 'Documents/Shelf/'ディレクトリに結合してフルパスを作成
    library_dir = os.path.join(home_directory, "Documents", "Shelf")
    library_path = os.path.join(library_dir, filename)
    try:
        with open(library_path, "r", encoding="utf-8") as f:
           books_lib = json.load(f)
        return [Book(**data) for data in books_lib]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# 削除
def remove_book(isbn):
    global library
    library = load_library_from_file()  # 既存データを読み込む
    
    # ISBNに一致する本を探して削除
    book_to_remove = next((book for book in library if book.isbn == str(isbn)), None)
    
    if book_to_remove:
        library.remove(book_to_remove)  # 一致する本があれば削除
        save_library_to_file(library)
        print(f"ISBN {isbn} の本は削除されました。")
    else:
        raise ValueError(f"ISBN {isbn} はライブラリに存在しません。")


# 追加
def addlibrary(isbn):
    library = load_library_from_file()

    # 重複回避
    if any(book.isbn == str(isbn) for book in library):
        raise ValueError("すでに登録されています。")
    
    bookdata = getdata(isbn)
    book = create_book_from_data(isbn,bookdata)
    library.append(book)
    save_library_to_file(library)

currentlib = load_library_from_file()
print("現在の蔵書です。")
print(currentlib)
code = input("追加の場合はA、削除の場合はDを入力します。:")
if code == "D":
    isbn = input("削除する本のISBNを入力してください：")
    remove_book(isbn)
elif code == "A":
    isbn = input("追加する本のISBNを入力してください：")
    addlibrary(isbn)

currentlib = load_library_from_file()
print("現在の蔵書です。")
print(currentlib)