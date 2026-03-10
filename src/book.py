# Bookクラスを定義。
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