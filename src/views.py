# UI
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
    QMainWindow,
)
from PySide6.QtCore import Qt, Slot
from src import models

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shelf")
        self.setGeometry(100, 100, 1300, 900)

        self.setup_ui()

    def setup_ui(self):
        """UI全体の組み立て"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        #各セクションの配置
        self._create_info_bar() # 蔵書数、検索ボックス
        self._create_table_section() # 表、読み込みボタン
        self._create_input_form() # 追加・削除フォーム
        self._create_action_buttons() # バーコード・適用ボタン
        # ショートカット設定
        self._setup_shortcuts()
    def _create_info_bar(self):
        # 3オブジェクトを定義
        self.label_data_count = QLabel("蔵書数: 0", objectName="datacount")
        self.label_read_count = QLabel("既読数: 0", objectName="readcount")
        self.search_box = QLineEdit(placeholderText="検索(⌘F)", fixedWidth=300)
        # 配置
        layout = QHBoxLayout()
        layout.addWidget(self.label_data_count)
        layout.addWidget(self.label_read_count)
        layout.addStretch()
        layout.addWidget(self.search_box)
        # メインレイアウトに置く。
        self.main_layout.addLayout(layout)
    def _create_table_section(self):
        self.tableWidget = QTableWidget(columnCount=8) # テーブルを定義
        self.tableWidget.setSortingEnabled(True) # 設定
        self.tableWidget.verticalHeader().setVisible(False) #設定

        self.loadButton = QPushButton("再読み込み(⌘R)") # 再読み込みボタンを定義
        # メインレイアウトに置く
        self.main_layout.addWidget(self.tableWidget)
        self.main_layout.addWidget(self.loadButton)
    def _create_input_form(self):
        layout = QGridLayout()
        self.line_edit1 = QLineEdit(placeholderText="追加する本のISBNコード")
        self.line_edit2 = QLineEdit(placeholderText="削除する本のISBNコード")

        layout.addWidget(QLabel("追加"), 0, 0)
        layout.addWidget(QLabel("追加"), 0, 0)
        layout.addWidget(self.line_edit1, 0, 1)
        layout.addWidget(QLabel("削除"), 0, 2)
        layout.addWidget(self.line_edit2, 0, 3)
        self.main_layout.addLayout(layout)
    def _create_action_buttons(self):
        self.filebutton = QPushButton("バーコードの画像ファイルから本を追加する")
        self.apply_button = QPushButton("変更を適用(⌘S)", objectName="saveButton", default=True)

        self.main_layout.addWidget(self.filebutton)
        self.main_layout.addWidget(self.apply_button)
    def _setup_shortcuts(self):
            # 検索フォーカス用のAction
            focus_action = QWidgetAction(self)
            focus_action.setShortcut("Ctrl+F")
            self.addAction(focus_action)
            self.focus_action = focus_action # アクションも一つの物体として持っておく
            self.apply_action = QWidgetAction(self)
            self.apply_action.setShortcut("Ctrl+S")
            self.addAction(self.apply_action)

            self.reload_action = QWidgetAction(self)
            self.reload_action.setShortcut("Ctrl+R")
            self.addAction(self.reload_action)
    # 以下エラーと情報ダイアログの定義
    @Slot(str)
    def show_error(self, message: str):
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText(message)
        error_msg.setWindowTitle("エラー")
        error_msg.exec()

    @Slot(str)
    def show_info(self, message: str):
        info_msg = QMessageBox()
        info_msg.setIcon(QMessageBox.Icon.Information)
        info_msg.setText(message)
        info_msg.setWindowTitle("情報")
        info_msg.exec()
    """ここまでUIの配置"""

    # テーブルに描画。modelsのget_all_dataと繋がっている
    def load_db(self):
        # 1. テーブルの初期化
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels([
            "ISBN", "タイトル", "著者", "出版社", "出版年月", "分類番号", "既読", "削除"
        ])
        self.tableWidget.setSortingEnabled(False)

        # 2. Modelからデータを取得（SQLはここで書かない）
        library = models.get_all_books()
        
        data_count = len(library)
        self.label_data_count.setText(f"蔵書数: {data_count}")
        self.tableWidget.setRowCount(data_count)

        # 3. テーブルへの描画
        for row, item in enumerate(library):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(item.isbn))
            # 文字列連結などの整形ロジック
            title = ", ".join(item.title) if isinstance(item.title, list) else item.title or "No Title"
            self.tableWidget.setItem(row, 1, QTableWidgetItem(title))
            
            creator = ", ".join(item.creator) if isinstance(item.creator, list) else item.creator or "No Creator"
            self.tableWidget.setItem(row, 2, QTableWidgetItem(creator))
            
            publisher = ", ".join(item.publisher) if isinstance(item.publisher, list) else item.publisher or "No Publisher"
            self.tableWidget.setItem(row, 3, QTableWidgetItem(publisher))
            
            self.tableWidget.setItem(row, 4, QTableWidgetItem(item.issued))
            self.tableWidget.setItem(row, 5, QTableWidgetItem(item.classification))

            # 既読チェックボックス（Itemとして設定）
            readed_item = QTableWidgetItem()
            readed_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            readed_item.setCheckState(Qt.Checked if item.readed else Qt.Unchecked)
            self.tableWidget.setItem(row, 6, readed_item)

            # 削除用チェックボックス（Widgetとして設定）
            checkbox = QCheckBox()
            self.tableWidget.setCellWidget(row, 7, checkbox)

        # 4. 列幅の設定
        column_widths = [150, 300, 150, 354, 100, 100, 60, 60]
        for i, width in enumerate(column_widths):
            self.tableWidget.setColumnWidth(i, width)

        # 5. 既読数のカウント（View上の表示から計算）
        read_count = sum(
            1 for r in range(self.tableWidget.rowCount())
            if self.tableWidget.item(r, 6).checkState() == Qt.Checked
        )
        self.label_read_count.setText(f"既読数: {read_count}")

        self.tableWidget.setSortingEnabled(True)
        self.show_info("データベースがリロードされました。")

    # src/views.py 内の Window クラスメソッドとして保持。検索ボックスに入力されたキーワードでテーブルの行をフィルタリングする。
    def search_table(self):
        keyword = self.search_box.text().lower()
        for row in range(self.tableWidget.rowCount()):
            match = False
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, col)
                # セルにテキストがあり、キーワードが含まれていればマッチと判定
                if item and keyword in item.text().lower():
                    match = True
                    break
            # マッチしない行を非表示にする
            self.tableWidget.setRowHidden(row, not match)

    # 検索ボックスにフォーカスを移動し、既存のテキストを選択状態にする。

    def focus_search_box(self):
        self.search_box.setFocus()
        self.search_box.selectAll()  # すぐに上書き入力できるように全選択
    