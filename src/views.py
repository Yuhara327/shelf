# UI
import PySide6.QtWidgets
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, Slot
from src import models
import numpy as np # OpenCVの配列の型アノテーション等に用いる場合

class Window(PySide6.QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shelf")
        self.setGeometry(100, 100, 1300, 900)

        self.setup_ui()

    def setup_ui(self):
        """UI全体の組み立て"""
        central_widget = PySide6.QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = PySide6.QtWidgets.QVBoxLayout(central_widget)
        #各セクションの配置
        self._create_info_bar() # 蔵書数、検索ボックス
        self._create_table_section() # 表、読み込みボタン
        self._create_input_form() # 追加・削除フォーム
        self._create_action_buttons() # バーコード・適用ボタン
        # ショートカット設定
        self._setup_shortcuts()
    def _create_info_bar(self):
        # 3オブジェクトを定義
        self.label_data_count = PySide6.QtWidgets.QLabel("蔵書数: 0", objectName="datacount")
        self.label_read_count = PySide6.QtWidgets.QLabel("既読数: 0", objectName="readcount")
        self.loadButton = PySide6.QtWidgets.QPushButton("再読み込み(⌘R)", objectName="loadbutton") # 再読み込みボタンを定義
        self.search_box = PySide6.QtWidgets.QLineEdit(placeholderText="検索(⌘F)", fixedWidth=300)
        # 配置
        layout = PySide6.QtWidgets.QHBoxLayout()
        layout.addWidget(self.label_data_count)
        layout.addWidget(self.label_read_count)
        layout.addStretch()
        layout.addWidget(self.loadButton)
        layout.addWidget(self.search_box)
        # メインレイアウトに置く。
        self.main_layout.addLayout(layout)
    def _create_table_section(self):
        self.tableWidget = PySide6.QtWidgets.QTableWidget(columnCount=8) # テーブルを定義
        self.tableWidget.setSortingEnabled(True) # 設定
        self.tableWidget.verticalHeader().setVisible(False) #設定
        # メインレイアウトに置く
        self.main_layout.addWidget(self.tableWidget)
    def _create_input_form(self):
        self.line_edit1 = PySide6.QtWidgets.QLineEdit(placeholderText="追加する本のISBNコード")
        self.line_edit2 = PySide6.QtWidgets.QLineEdit(placeholderText="削除する本のISBNコード")

        layout = PySide6.QtWidgets.QHBoxLayout()
        layout.addWidget(self.line_edit1)
        layout.addWidget(self.line_edit2)
        self.main_layout.addLayout(layout)
    def _create_action_buttons(self):
        self.filebutton = PySide6.QtWidgets.QPushButton("バーコードの画像ファイルから本を追加する")
        self.camerabutton = PySide6.QtWidgets.QPushButton("カメラでバーコードを読み取る")

        layout = PySide6.QtWidgets.QHBoxLayout()
        layout.addWidget(self.filebutton)
        layout.addWidget(self.camerabutton)
        self.main_layout.addLayout(layout)

        self.apply_button = PySide6.QtWidgets.QPushButton("変更を適用(⌘S)", objectName="saveButton", default=True)
        self.main_layout.addWidget(self.apply_button)
    def _setup_shortcuts(self):
            # 検索フォーカス用のAction
            focus_action = PySide6.QtWidgets.QWidgetAction(self)
            focus_action.setShortcut("Ctrl+F")
            self.addAction(focus_action)
            self.focus_action = focus_action # アクションも一つの物体として持っておく
            self.apply_action = PySide6.QtWidgets.QWidgetAction(self)
            self.apply_action.setShortcut("Ctrl+S")
            self.addAction(self.apply_action)

            self.reload_action = PySide6.QtWidgets.QWidgetAction(self)
            self.reload_action.setShortcut("Ctrl+R")
            self.addAction(self.reload_action)
    # 以下エラーと情報ダイアログの定義
    @Slot(str)
    def show_error(self, message: str):
        error_msg = PySide6.QtWidgets.QMessageBox()
        error_msg.setIcon(PySide6.QtWidgets.QMessageBox.Icon.Critical)
        error_msg.setText(message)
        error_msg.setWindowTitle("エラー")
        error_msg.setWindowFlag(Qt.WindowStaysOnTopHint)  # 追加
        error_msg.exec()

    @Slot(str)
    def show_info(self, message: str):
        info_msg = PySide6.QtWidgets.QMessageBox()
        info_msg.setIcon(PySide6.QtWidgets.QMessageBox.Icon.Information)
        info_msg.setText(message)
        info_msg.setWindowTitle("情報")
        info_msg.setWindowFlag(Qt.WindowStaysOnTopHint)  # 追加
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
            self.tableWidget.setItem(row, 0, PySide6.QtWidgets.QTableWidgetItem(item.isbn))
            # 文字列連結などの整形ロジック
            title = ", ".join(item.title) if isinstance(item.title, list) else item.title or "No Title"
            self.tableWidget.setItem(row, 1, PySide6.QtWidgets.QTableWidgetItem(title))
            
            creator = ", ".join(item.creator) if isinstance(item.creator, list) else item.creator or "No Creator"
            self.tableWidget.setItem(row, 2, PySide6.QtWidgets.QTableWidgetItem(creator))
            
            publisher = ", ".join(item.publisher) if isinstance(item.publisher, list) else item.publisher or "No Publisher"
            self.tableWidget.setItem(row, 3, PySide6.QtWidgets.QTableWidgetItem(publisher))
            
            self.tableWidget.setItem(row, 4, PySide6.QtWidgets.QTableWidgetItem(item.issued))
            self.tableWidget.setItem(row, 5, PySide6.QtWidgets.QTableWidgetItem(item.classification))

            # 既読チェックボックス（Itemとして設定）
            readed_item = PySide6.QtWidgets.QTableWidgetItem()
            readed_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            readed_item.setCheckState(Qt.Checked if item.readed else Qt.Unchecked)
            self.tableWidget.setItem(row, 6, readed_item)

            # 削除用チェックボックス（Widgetとして設定）
            checkbox = PySide6.QtWidgets.QCheckBox()
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
    

class CameraDialog(PySide6.QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("カメラでバーコードを読み取る")
        # メインウィンドウの操作をロックするモーダル設定
        self.setModal(True) 
        self.resize(900, 520)

        self.setup_ui()

    def setup_ui(self):
        main_layout = PySide6.QtWidgets.QHBoxLayout(self)

        # --- 左側：プレビュー領域 ---
        self.preview_label = PySide6.QtWidgets.QLabel("カメラを起動しています...")
        # カメラの標準的なアスペクト比（VGA）に合わせて固定
        self.preview_label.setFixedSize(640, 480) 
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #222; color: white;")
        main_layout.addWidget(self.preview_label)

        # --- 右側：データと操作領域 ---
        right_layout = PySide6.QtWidgets.QVBoxLayout()

        # カメラ選択用プルダウンを追加
        self.camera_selector = PySide6.QtWidgets.QComboBox()
        right_layout.addWidget(PySide6.QtWidgets.QLabel("使用するカメラ:"))
        right_layout.addWidget(self.camera_selector)

        self.status_label = PySide6.QtWidgets.QLabel("読み取り待機中... (0件)")
        right_layout.addWidget(self.status_label)

        # 読み取ったISBNが縦に並ぶリストUI
        self.isbn_list = QListWidget()
        right_layout.addWidget(self.isbn_list)

        self.finish_button = PySide6.QtWidgets.QPushButton("終了してデータベースへ追加")
        # ボタンを少し目立たせる（高さを持たせる）
        self.finish_button.setMinimumHeight(40) 
        right_layout.addWidget(self.finish_button)

        main_layout.addLayout(right_layout)

    @Slot(object)
    def update_camera_preview(self, frame_rgb):
        """
        Controllerの別スレッドから送られてきたnumpy配列(RGB)を受け取り、
        PySide6で描画可能なQPixmapに変換してQLabelにセットする。
        """
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        # メモリ上の配列データをQImageとして解釈
        q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.preview_label.setPixmap(QPixmap.fromImage(q_img))

    @Slot(list)
    def update_scanned_list_ui(self, new_isbns):
        """
        新規取得したISBNを右側のリストUIに追加し、一番下までスクロールする。
        """
        for isbn in new_isbns:
            item = QListWidgetItem(f"ISBN: {isbn}")
            self.isbn_list.addItem(item)
        
        # 自動で最新のデータが見えるようにスクロール
        self.isbn_list.scrollToBottom()
        
        # 件数表示の更新
        total_count = self.isbn_list.count()
        self.status_label.setText(f"読み取り完了: {total_count} 件")

    @Slot(str)
    def show_error(self, message: str):
        error_msg = PySide6.QtWidgets.QMessageBox()
        error_msg.setIcon(PySide6.QtWidgets.QMessageBox.Icon.Critical)
        error_msg.setText(message)
        error_msg.setWindowTitle("エラー")
        error_msg.exec()

    @Slot(str)
    def show_info(self, message: str):
        info_msg = PySide6.QtWidgets.QMessageBox()
        info_msg.setIcon(PySide6.QtWidgets.QMessageBox.Icon.Information)
        info_msg.setText(message)
        info_msg.setWindowTitle("情報")
        info_msg.exec()

    def closeEvent(self, event):
        """
        ウィンドウ右上の「×」ボタンが押された時の特殊処理。
        バックグラウンドのカメラ起動ループを安全に終了させるため、
        そのままウィンドウを閉じることを拒否し、終了ボタンのクリックを強制する。
        """
        # まだスレッドが動いている可能性があるため、ウィンドウの破棄を一時保留
        event.ignore() 
        # 終了ボタンが押されたことにして、Controllerに停止処理を委ねる
        self.finish_button.click()

    # views.py の CameraDialog クラス内に追加
    def set_camera_list(self, camera_indices):
        """
        利用可能なカメラのインデックスリストを受け取り、プルダウンメニューに反映させる。
        """
        self.camera_selector.clear()
        for index in camera_indices:
            label = f"Camera {index}" + (" (Built-in)" if index == 0 else " (External/iPhone)")
            # addItem(表示名, 内部データ)
            self.camera_selector.addItem(label, index)