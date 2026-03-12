# 全体の配線とアプリ起動を担う。
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette
from src.views import Window
from src import controller
from create_db import createdb
from src.views import CameraDialog

def get_qss_path(app, application_path):
    """
    OSのテーマを判定して適切なQSSパスを返す
    """
    # システムのパレットから背景の明るさを取得 (0-255)
    brightness = app.palette().color(QPalette.Window).lightness()
    is_dark = brightness < 128
    
    file_name = "dark_styles.qss" if is_dark else "styles.qss"
    
    # パス解決（既存のロジックを利用）
    path = os.path.join(application_path, "src", file_name)
    if not os.path.exists(path):
        path = os.path.join(application_path, "styles", file_name)
    return path
def handle_camera_dialog(main_window):
    from src import utils, controller
    from src.views import CameraDialog
    
    dialog = CameraDialog(main_window)
    dialog.load_db = main_window.load_db
    dialog.clear_camera_ui = dialog.accept

    cameras = utils.list_available_cameras()


    if not cameras:
        main_window.show_error("使用可能なカメラが見つかりませんでした。接続を確認してください。")
        return

    # 利用可能なカメラを取得してセット
    dialog.set_camera_list(cameras)

    def on_change():
        """プルダウンが変更された時に実行される内部関数"""
        # currentData() で、set_camera_list時に紐付けたインデックス番号を取得
        idx = dialog.camera_selector.currentData()
        if idx is not None:
            controller.switch_camera(dialog, idx)

    # プルダウンが変更された時の配線
    dialog.camera_selector.currentIndexChanged.connect(on_change)
    
    dialog.finish_button.clicked.connect(lambda: controller.stop_camera_session(dialog))
    
    # 初回の起動（最初に見つかったカメラを使用する）
    if cameras:
        # デフォルトの0ではなく、見つかったリストの先頭(cameras[0])を使う
        initial_camera = cameras[0]
        # Controller側の引数でインデックスを指定できるようにしている場合
        controller.start_camera_session(dialog, initial_camera)
    
    dialog.exec()
def main():
    # SQLiteデータベースがあるかどうか。なければ作成
    createdb()

    # アプリケーションの生成
    app = QApplication(sys.argv)

    # スタイルの読み込み
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    qss_path = get_qss_path(app, application_path)

    qss = ""
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            qss = f.read()
    else:
        print(f"Warning: QSS file not found at {qss_path}")

    # windowの生成
    window = Window()
    window.setStyleSheet(qss)
    # 配線作業
    # ボタンを押されたら、controllerの関数を呼ぶように繋ぐ。
    window.apply_button.clicked.connect(lambda: controller.handle_add_delete(window)) # applybuttonでcontrollerのhandle_add_deleteを呼ぶ
    window.filebutton.clicked.connect(lambda: controller.handle_batch_images(window)) # ファイルボタンで、handle_batch_imagesを呼ぶ。
    # 新規追加: カメラボタンの配線
    window.camerabutton.clicked.connect(lambda: handle_camera_dialog(window))

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