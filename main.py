# 全体の配線とアプリ起動を担う。
import sys
import os
from PySide6.QtWidgets import QApplication
from src.views import Window
from src import controller
from create_db import createdb

# SQLiteデータベースがあるかどうか。なければ作成
createdb()

# アプリケーションの生成
app = QApplication(sys.argv)

# スタイルの読み込み
application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
qss_path = os.path.join(application_path, "src", "styles.qss")
if not os.path.exists(qss_path):
        # 開発環境用のフォールバックパス
        qss_path = os.path.join(application_path, 'styles', 'styles.qss')
try:
    with open(qss_path, 'r') as f:
        qss = f.read()
except FileNotFoundError:
    print(f"Warning: QSS file not found at {qss_path}")

# windowの生成
window = Window()
window.setStyleSheet(qss)
# 配線作業
# ボタンを押されたら、controllerの関数を呼ぶように繋ぐ。
window.apply_button.clicked.connect(lambda: controller.handle_add_delete(window)) # applybuttonでcontrollerのhandle_add_deleteを呼ぶ
window.filebutton.clicked.connect(lambda: controller.handle_batch_images(window)) # ファイルボタンで、handle_batch_imagesを呼ぶ。

# view内部の動き
window.loadButton.clicked.connect(window.load_db) # 再読み込みボタンをload_dbに繋ぐ
window.focus_action.triggered.connect(window.focus_search_box) # command fでフォーカス移動関数を呼ぶ。
window.apply_action.triggered.connect(window.apply_button.click) # command sで適用
window.reload_action.triggered.connect(window.loadButton.click) # command rでリロード

# 検索ボックスの Enter キーで適用ボタンをクリックさせる配線
window.line_edit1.returnPressed.connect(window.apply_button.click)
window.line_edit2.returnPressed.connect(window.apply_button.click)

# データの初期読み込み
window.load_db()

# 表示と実行。
window.show()
sys.exit(app.exec())

if __name__ == "__main__":
    main()