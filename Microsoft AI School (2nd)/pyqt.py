import sys
import os
import csv
import pyqt5_fugueicons as fugue
import cv2
import smtplib
import time
import sqlite3
import numpy as np
import pandas as pd

from PIL import Image, ImageFont, ImageDraw

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PyQt5.QtCore import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.video_source = None
        self.button_return_value = 0  
        self.is_video_paused = False
        self.is_bring_csv_content_working = False
        self.image_window = None
        self.is_detection_enabled = False
        self.is_bring_detection_info_from_table_enabled = False
        self.frame_nmr = -1

        self.setWindowTitle("EV 차량 번호판 감지 프로그램")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(fugue.icon("surveillance-camera", size=16, fallback_size=True))

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("background-color: #F0F0F0;")

        self.tab1 = QWidget()
        self.tab_widget.addTab(self.tab1, fugue.icon("camera", size=16, fallback_size=True), "실시간 체크")

        tab_bar = self.tab_widget.tabBar()
        font = QFont("Malgun Gothic", 8)
        font.setBold(True)
        tab_bar.setFont(font)

        tab_layout1 = QVBoxLayout(self.tab1)
        tab1_splitter_layout = QSplitter(Qt.Horizontal)
        tab_layout1.addWidget(tab1_splitter_layout)

        self.tab2 = QWidget()
        self.tab_widget.addTab(self.tab2, fugue.icon("eye", size=16, fallback_size=True), "관리자 페이지")

        tab_layout2 = QVBoxLayout(self.tab2)
        tab2_splitter_layout = QSplitter(Qt.Horizontal)
        tab_layout2.addWidget(tab2_splitter_layout)


        self.tab1_web_view_label = QLabel('🌐 서버', font=QFont('Malgun Gothic', 18, QFont.Bold))
        self.tab1_web_view_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")
        self.tab1_web_view_label.setFixedHeight(30)

        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("http://127.0.0.1:5001/"))

        tab1_inner_layout1 = QVBoxLayout()
        tab1_inner_layout1.addWidget(self.tab1_web_view_label)
        tab1_inner_layout1.addWidget(self.web_view)
        
        self.tab1_image_viewer_label = QLabel('🚘 차량 사진 확인', font=QFont('Malgun Gothic', 18, QFont.Bold))  
        self.tab1_image_viewer_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")
        self.tab1_image_viewer_label.setFixedHeight(30)

        self.tab1_image_viewer = QLabel()
        self.tab1_image_viewer.setAlignment(Qt.AlignCenter)

        self.tab1_button_ev = QPushButton('EV', self)
        self.tab1_one_line_ev = QPushButton('One Line', self)
        self.tab1_two_line_ev = QPushButton('Two Line', self)

        button_style = (
            "QPushButton {"
            "   background-color: #333;"
            "   border: none;"
            "   color: white;"
            "   padding: 8px 16px;"
            "   text-align: center;"
            "   text-decoration: none;"
            "   display: inline-block;"
            "   font-size: 16px;"
            "   margin: 4px 2px;"
            "   cursor: pointer;"
            "   border-radius: 8px;"
            "   font-weight: bold;"
            "   font-family: Consolas;"
            "}"
            "QPushButton:hover {"
            "   background-color: #222;"
            "}"
            "QPushButton:pressed {"
            "   background-color: #111;"
            "}"
        )

        self.tab1_button_ev.setStyleSheet(button_style)
        self.tab1_one_line_ev.setStyleSheet(button_style)
        self.tab1_two_line_ev.setStyleSheet(button_style)

        self.tab1_video_player_label = QLabel('📺 영상', font=QFont('Malgun Gothic', 18, QFont.Bold))
        self.tab1_video_player_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")
        self.tab1_video_player_label.setFixedHeight(30)

        self.video_player = QLabel()
        self.video_player.setAlignment(Qt.AlignCenter)

        self.detection_info = QLabel()
        self.detection_info.setFixedHeight(15)
        self.detection_info.setAlignment(Qt.AlignCenter)
        self.detection_info.setFont(QFont('Malgun Gothic', 10))

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 100)
        self.position_slider.sliderMoved.connect(lambda position: self.set_position(position))
        self.position_slider.setEnabled(False)

        tab2_button_layout = QHBoxLayout()
        tab2_button_layout.addWidget(self.tab1_button_ev)
        tab2_button_layout.addWidget(self.tab1_one_line_ev)
        tab2_button_layout.addWidget(self.tab1_two_line_ev)

        tab1_inner_layout2 = QVBoxLayout()
        tab1_inner_layout2.addWidget(self.tab1_image_viewer_label)
        tab1_inner_layout2.addWidget(self.tab1_image_viewer)
        tab1_inner_layout2.addLayout(tab2_button_layout)
        tab1_inner_layout2.addWidget(self.tab1_video_player_label)
        tab1_inner_layout2.addWidget(self.video_player)
        tab1_inner_layout2.addWidget(self.detection_info)
        tab1_inner_layout2.addWidget(self.position_slider)


        self.tab1_db_list_label = QLabel('💾 DB 정보', font=QFont('Malgun Gothic', 18, QFont.Bold))
        self.tab1_db_list_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")

        self.tab1_db_list_table = QTableWidget(font=QFont('Malgun Gothic', 10))
        self.tab1_db_list_table_headers = ["id", "video_name", "video_file", "upload_date"]
        self.tab1_db_list_table.setColumnCount(len(self.tab1_db_list_table_headers))
        self.tab1_db_list_table.setHorizontalHeaderLabels(self.tab1_db_list_table_headers)
        self.tab1_db_list_table.setStyleSheet("background-color: white;")
        self.tab1_db_list_table.setEditTriggers(QTableWidget.NoEditTriggers)    
        
        self.tab1_db_list_table.setColumnWidth(0, 10)    # 체크박스 컬럼

        self.tab1_item_list_label = QLabel('🚗 차량 정보', font=QFont('Malgun Gothic', 18, QFont.Bold))  
        self.tab1_item_list_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")

        self.tab1_item_list_table = QTableWidget(font=QFont('Malgun Gothic', 10))
        self.tab1_item_list_table_headers = ["√", "frame_nmr", "car_id", "car_bbox", "license_plate_bbox", "license_plate_bbox_score", "license_number", "license_number_score"]
        self.tab1_item_list_table.setColumnCount(len(self.tab1_item_list_table_headers))
        self.tab1_item_list_table.setHorizontalHeaderLabels(self.tab1_item_list_table_headers)
        self.tab1_item_list_table.setStyleSheet("background-color: white;")
        self.tab1_item_list_table.setEditTriggers(QTableWidget.NoEditTriggers)     # 수정 금지
        
        self.tab1_item_list_table.setColumnWidth(0, 10)    # 체크박스 컬럼

        self.tab1_item_list_table.itemDoubleClicked.connect(self.show_car_image)

        tab1_inner_layout3 = QVBoxLayout()
        tab1_inner_layout3.addWidget(self.tab1_db_list_label)
        tab1_inner_layout3.addWidget(self.tab1_db_list_table)
        tab1_inner_layout3.addWidget(self.tab1_item_list_label)
        tab1_inner_layout3.addWidget(self.tab1_item_list_table)

        tab1_widget1 = QWidget()
        tab1_widget1.setLayout(tab1_inner_layout1)

        tab1_widget2 = QWidget()
        tab1_widget2.setLayout(tab1_inner_layout2)

        tab1_widget3 = QWidget()
        tab1_widget3.setLayout(tab1_inner_layout3)

        tab1_splitter_layout.addWidget(tab1_widget1)
        tab1_splitter_layout.addWidget(tab1_widget2)
        tab1_splitter_layout.addWidget(tab1_widget3)

        self.image_viewer = QLabel()
        self.image_viewer.setMaximumHeight(1200)

        tab2_inner_layout1 = QVBoxLayout()
        tab2_inner_layout1.addWidget(self.image_viewer)
        
        self.tab2_section_label = QLabel('✅ 버튼 클릭', font=QFont('Malgun Gothic', 18, QFont.Bold))  
        self.tab2_section_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")
        self.tab2_section_label.setAlignment(Qt.AlignCenter)

        self.tab2_button_ev = QPushButton('EV', self)
        self.tab2_one_line_ev = QPushButton('One Line', self)
        self.tab2_two_line_ev = QPushButton('Two Line', self)

        button_style = (
            "QPushButton {"
            "   background-color: #4CAF50;"
            "   border: none;"
            "   color: white;"
            "   padding: 10px 20px;"
            "   text-align: center;"
            "   text-decoration: none;"
            "   display: inline-block;"
            "   font-size: 16px;"
            "   margin: 4px 2px;"
            "   cursor: pointer;"
            "   border-radius: 8px;"
            "   font-weight: bold;"
            "   font-family: Consolas;"
            "}"
            "QPushButton:hover {"
            "   background-color: #45a049;"
            "}"
            "QPushButton:pressed {"
            "   background-color: #367d39;"
            "}"
        )

        self.tab2_button_ev.setStyleSheet(button_style)
        self.tab2_one_line_ev.setStyleSheet(button_style)
        self.tab2_two_line_ev.setStyleSheet(button_style)

        self.tab2_button_ev.clicked.connect(lambda: self.on_button_click("EV"))
        self.tab2_one_line_ev.clicked.connect(lambda: self.on_button_click("One Line"))
        self.tab2_two_line_ev.clicked.connect(lambda: self.on_button_click("Two Line"))

        tab2_inner_layout2_1 = QVBoxLayout()
        tab2_inner_layout2_1.addWidget(self.tab2_section_label)

        tab2_inner_layout2_2 = QVBoxLayout()
        tab2_inner_layout2_2.addWidget(self.tab2_button_ev)
        tab2_inner_layout2_2.addWidget(self.tab2_one_line_ev)
        tab2_inner_layout2_2.addWidget(self.tab2_two_line_ev)

        tab2_inner_layout2 = QVBoxLayout()
        tab2_inner_layout2.addStretch() 
        tab2_inner_layout2.addLayout(tab2_inner_layout2_1)
        tab2_inner_layout2.addLayout(tab2_inner_layout2_2)
        tab2_inner_layout2.addStretch()  
    
        tab2_widget1 = QWidget()
        tab2_widget1.setLayout(tab2_inner_layout1)

        tab2_widget2 = QWidget()
        tab2_widget2.setFixedWidth(280)
        tab2_widget2.setLayout(tab2_inner_layout2)

        tab2_splitter_layout.addWidget(tab2_widget1)
        tab2_splitter_layout.addWidget(tab2_widget2)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: rgba(240, 240, 240, 0.65); color: black;")

        self.filemenu = menubar.addMenu("파일")
        self.infomenu = menubar.addMenu("정보")

        self.menuNames = {
            "파일": self.filemenu,
            "정보": self.infomenu
        }

        filemenu_items = [
            {
                "icon": "application-plus",
                "text": "CCTV 녹화 동영상 파일 불러오기",
                "shortcut": "Ctrl+O",
                "status_tip": "CCTV 녹화 동영상 파일을 불러옵니다.",
                "triggered": self.open_video_file
            },
            {
                "icon": "cross",
                "text": "프로그램 종료",
                "shortcut": "Ctrl+Q",
                "status_tip": "프로그램을 종료합니다.",
                "triggered": qApp.quit
            }
        ]

        infomenu_items = [
            {
                "icon": "information",
                "text": "프로그램 정보",
                "shortcut": "Ctrl+I",
                "status_tip": "프로그램 정보를 확인합니다.",
                "triggered": lambda: QMessageBox.information(self, "프로그램 정보", "EV 차량 번호판 감지 프로그램 \n제작: MS AI School 6팀 (2기)")
            },
        ]

        self.setItems("파일", filemenu_items)
        self.setItems("정보", infomenu_items)

        toolbar_style = """
        QToolButton:checked { 
                background-color: #CCE8FF; 
                border: 1px solid #99D1FF; 
                border-radius: 2px;
                padding: 2px; 
        }
        QToolButton:hover { 
            background-color: #E5F3FF; 
            border: 1px solid #CCE8FF; 
            border-radius: 2px; 
        }
        """
        
        self.tab1_toolbar1 = QToolBar()
        self.tab1_toolbar1.setMovable(False)
        self.tab1_toolbar1.setFixedHeight(50)
        self.tab1_toolbar1.setStyleSheet(toolbar_style)

        self.tab1_toolbar2 = QToolBar()
        self.tab1_toolbar2.setMovable(True)
        self.tab1_toolbar2.setFixedHeight(50)
        self.tab1_toolbar2.setStyleSheet(toolbar_style)

        self.tab1_toolbar3 = QToolBar()
        self.tab1_toolbar3.setMovable(True)
        self.tab1_toolbar3.setFixedHeight(50)
        self.tab1_toolbar3.setStyleSheet(toolbar_style)

        self.tab2_toolbar1 = QToolBar()
        self.tab2_toolbar1.setMovable(False)
        self.tab2_toolbar1.setFixedHeight(50)
        self.tab2_toolbar1.setStyleSheet(toolbar_style)

        self.tab2_toolbar2 = QToolBar()
        self.tab2_toolbar2.setMovable(True)
        self.tab2_toolbar2.setFixedHeight(50)
        self.tab2_toolbar2.setStyleSheet(toolbar_style)

        self.toolBarNames = {
            '툴바1': self.tab1_toolbar1,
            '툴바2': self.tab1_toolbar2,
            '툴바3': self.tab1_toolbar3,
            '툴바4': self.tab2_toolbar1,
            '툴바5': self.tab2_toolbar2,
        }

        tab1_toolbar1_actions = [
            ("서버에 접속하기", "feed", lambda: self.web_view.load(QUrl("http://127.0.0.1:5001/")), False, False),
            ("브라우저에서 서버 띄우기", "globe", lambda: self.open_browser_with_Chrome("http://127.0.0.1:5001/"), False, False),
        ]

        tab1_toolbar2_actions = [
            ("CCTV 동영상 불러오기", "film", self.open_video_file, False, False),
            ("CCTV 동영상 멈추기", "light-bulb-off", self.pause_the_video, False, False),
            ("CCTV 동영상 재생하기", "light-bulb", self.resume_the_video, False, False),
            ("재생 속도 올리기 (x0.1)", "navigation-090", self.speed_up_video, False, False),
            ("재생 속도 내리기 (x0.1)", "navigation-270", self.speed_down_video, False, False),
            ("CCTV 동영상 지우기", "scissors", lambda: self.clear_the_content("동영상"), False, False),
        ]

        tab1_toolbar3_actions = [
            ("DB 내용 불러오기", "database", lambda: self.load_db_to_table(self.tab1_db_list_table), False, False),
            ("CSV 파일 내용 불러오기", "magnet", lambda checked: self.bring_contents_from_csv_file_and_fill_table_event(checked), False, True),
            ("Detection 모드 켜기", "camera-lens", lambda checked: self.start_detection(checked), False, True),
            ("테이블에 내용 불러오기 (CSV)", "table-import", lambda: self.import_table_widget(self.tab1_item_list_table), False, False),
            ("테이블 내용 내보내기 (CSV)", "table-export", lambda: self.export_table_widget(self.tab1_item_list_table), False, False),
            ("선택한 행 지우기", "scissors-blue", lambda: self.delete_selected_row_on_table(self.tab1_item_list_table), False, False),
            ("이메일로 보내기", "mail", self.send_email, False, False),
            ("카카오톡으로 보내기", "./icon/kakaotalk.ico_ni", self.send_kakaotalk_alarm, False, False),
        ]

        tab2_toolbar1_actions = [
            ("이미지 불러오기", "photo-album-blue", self.open_image_file, False, False),
            ("이미지 지우기", "scissors", lambda: self.clear_the_content("이미지"), False, False),
        ]


        self.setToobarWithActions("툴바1", tab1_toolbar1_actions)
        self.setToobarWithActions("툴바2", tab1_toolbar2_actions)
        self.setToobarWithActions("툴바3", tab1_toolbar3_actions)
        self.setToobarWithActions("툴바4", tab2_toolbar1_actions)

        
        tab1_inner_layout1.addWidget(self.tab1_toolbar1)
        tab1_inner_layout2.addWidget(self.tab1_toolbar2)    
        tab1_inner_layout3.addWidget(self.tab1_toolbar3)    
        tab2_inner_layout1.addWidget(self.tab2_toolbar1)    


    def setToobarWithActions(self, target, actions):
        toolbar = self.toolBarNames[target]

        for text, icon_name, connect_func, shortcut, checkable in actions: 
            action = QAction(text, toolbar)
            
            if "_ni" in icon_name:
                icon_name = icon_name.replace("_ni", "")
                action.setIcon(QIcon(icon_name))
            else:    
                action.setIcon(fugue.icon(icon_name, size=24, fallback_size=True))
            action.triggered.connect(connect_func)
            action.setShortcut(shortcut)
            action.setCheckable(checkable)
            toolbar.addAction(action)

        
    def setItems(self, target, items):
        menu = self.menuNames[target]
        
        for item in items:
            if item["icon"] != None:
                action = QAction(fugue.icon(item["icon"], size=16, fallback_size=True), item["text"], self)
                action.setShortcut(item["shortcut"])
                action.setStatusTip(item["status_tip"])
                action.triggered.connect(item["triggered"])
                menu.addAction(action)
            else:
                menu.addSeparator()


    def export_table_widget(self, target):
        file_dialog = QFileDialog(self)

        datetime_format_style = "%Y%m%d_%H%M%S"
        current_datetime = datetime.now().strftime(datetime_format_style)
        
        fileName = f"차량정보_{current_datetime}.csv"
        file_path, _ = file_dialog.getSaveFileName(self, f"차량 정보 테이블 내용 내보내기", fileName, filter="CSV File (*.csv)")

        if file_path:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)

                column_names = []
                for column in range(target.columnCount()):
                    column_names.append(target.horizontalHeaderItem(column).text())
                writer.writerow(column_names)

                for row in range(target.rowCount()):
                    row_data = []
                    for column in range(target.columnCount()):
                        item = target.item(row, column)
                        if item is not None:
                            if isinstance(item, QCheckBox):
                                row_data.append("1" if item.isChecked() else "0")
                            else:
                                row_data.append(item.text())
                        else:
                            row_data.append("")
                    writer.writerow(row_data)
                
            QMessageBox.information(self, "알림", "차량 정보 테이블의 내용을 내보냈습니다.", QMessageBox.Ok)

            file.close()


    def import_table_widget(self, target_table):
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix("csv")

        file_path, _ = file_dialog.getOpenFileName(self, "차량 정보 테이블에 내용 불러오기", filter="CSV File (*.csv)")

        if file_path:
            target_table.clearContents()
            target_table.setRowCount(0)

            with open(file_path, newline='', encoding='utf-8') as file:
                try:
                    reader = csv.reader(file)
                    next(reader)    
                    data = list(reader)
                except:
                    QMessageBox.warning(self, "알림", "파일의 인코딩 방식에 문제가 있습니다.")
                
                target_table.setRowCount(len(data))
                target_table.setColumnCount(len(data[0]) + 1)

                for row_idx, row_data in enumerate(data):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(cell_data.strip())
                        
                        cell_font = QFont("Consolas", 9)
                        item.setFont(cell_font)

                        if col_idx == 0:
                            row_checkbox = QTableWidgetItem()
                            row_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                            row_checkbox.setCheckState(Qt.Unchecked)
                            target_table.setColumnWidth(0, 16)
                            target_table.setItem(row_idx, col_idx, row_checkbox)

                        target_table.setItem(row_idx, col_idx + 1, item)    # 체크박스 빼고 넣기
                
                QMessageBox.information(self, "알림", "차량 정보 테이블에 내용을 가져왔습니다.")

                file.close()

    def setStatusBarMessage(self, message):
        self.statusBar.showMessage(message, 3000)

    def open_video_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "동영상 선택", "", "동영상 파일 (*.mp4 *.avi *.mkv);;모든 파일 (*)", options=options)

        if file_name:
            self.position_slider.setValue(0)
            self.play_video(file_name)

    def pause_the_video(self):
        if self.video_source is not None and not self.is_video_paused:
            self.is_video_paused = True
            self.setStatusBarMessage("동영상 재생이 멈추었습니다.")

            while self.is_video_paused:
                cv2.waitKey(100)

    def resume_the_video(self):
        try:
            if self.video_source is not None and self.is_video_paused:
                self.is_video_paused = False
                self.setStatusBarMessage("동영상 재생이 재개되었습니다.")

                if not self.is_video_playing:
                    self.is_video_playing = True
                    while self.is_video_playing and not self.is_video_paused and self.video_source.isOpened():
                        ret, frame = self.video_source.read()

                        if not ret:
                            self.stop_video()
                            break

                        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, c = img.shape
                        qImg = QImage(img.data, w, h, w * c, QImage.Format_RGB888)

                        pixmap = QPixmap.fromImage(qImg)
                        p = pixmap.scaled(int(w * 480 / h), 480, Qt.IgnoreAspectRatio)
                        self.video_player.setPixmap(p)

                        key = cv2.waitKey(int(1000 / (self.base_fps * self.fps_multiplier)))

                        if key == ord('q') or self.is_video_paused:
                            break

                    if not self.is_video_playing:
                        self.video_source.release()
                        cv2.destroyAllWindows()
        except:
            pass

    def speed_up_video(self):
        if self.video_source is not None:
            self.fps_multiplier += 0.1
            self.update_video_speed()

    def speed_down_video(self):
        if self.video_source is not None:
            self.fps_multiplier = max(0.1, self.fps_multiplier - 0.1)
            self.update_video_speed()

    def update_video_speed(self):
        if self.video_source is not None:
            self.video_source.set(cv2.CAP_PROP_FPS, self.base_fps * self.fps_multiplier)
            self.setStatusBarMessage(f"재생 속도: {self.fps_multiplier:.1f}배")

    def play_video(self, video_src):
        self.current_video_source = video_src
        self.video_source = cv2.VideoCapture(video_src)

        self.position_slider.setEnabled(True)
        self.base_fps = 60
        self.fps_multiplier = 1.0

        try:
            if self.video_source is not None:
                try:
                    base_dir = os.path.dirname(__file__)
                    csv_path = os.path.join(base_dir, 'result_final.csv')
                    results = pd.read_csv(csv_path, encoding='utf-8')    # 기존에 있는 파일 불러오기
                except:
                    pass

                cap = self.video_source
                self.frame_nmr = -1

                # cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                while True:
                    ret, frame = cap.read()
                    self.frame_nmr += 1

                    if not ret:
                        self.frame_nmr = -1
                        self.video_player.clear()      # 비디오 플레이어 내용 지우기
                        self.video_source.release()      # 비디오 소스 종료
                        self.video_source = None
                        self.position_slider.setValue(0)
                        self.position_slider.setEnabled(False)
                        break

                    if self.is_detection_enabled:
                        selected_df = results[results['frame_nmr'] == self.frame_nmr]

                        if not selected_df.empty and self.frame_nmr == selected_df['frame_nmr'].values[0]:
                            # 자동차 바운딩 박스 표시
                            car_bbox_str = selected_df['car_bbox'].values[0]
                            car_x1, car_y1, car_x2, car_y2 = map(float, car_bbox_str.strip('[]').split())
                            cv2.rectangle(frame, (int(car_x1), int(car_y1)), (int(car_x2), int(car_y2)), (0, 255, 0), 3)

                            # 번호판 바운딩 박스 표시
                            plate_bbox_str = selected_df['license_plate_bbox'].values[0]
                            plate_x1, plate_y1, plate_x2, plate_y2 = map(float, plate_bbox_str.strip('[]').split())

                            cv2.rectangle(frame, (int(plate_x1), int(plate_y1)), (int(plate_x2), int(plate_y2)), (0, 0, 255), 3)

                            # print(self.frame_nmr, car_x1, car_y1, car_x2, car_y2, plate_x1, plate_y1, plate_x2, plate_y2)
                            
                            # Convert the frame to PIL Image
                            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

                            # Initialize PIL draw object
                            draw = ImageDraw.Draw(pil_img)

                            # Choose a font and size
                            base_dir = os.path.dirname(__file__)
                            font_path = os.path.join(base_dir, "./MaruBuri-Bold.ttf")  
                            font_size = 15
                            font = ImageFont.truetype(font_path, font_size)

                            # Draw text
                            license_number_str = selected_df['license_number'].values[0]
                            text_position = (int(plate_x2) + 10, int(plate_y2) + 10)
                            
                            if float(selected_df['license_number_score'].iloc[0]) >= 0.9:
                                draw.text(text_position, license_number_str, font=font, fill=(255, 0, 0, 225))
                                self.detection_info.setText(f"<b>#{self.frame_nmr}</b> : {license_number_str}")
                            else:
                                self.detection_info.setText(f"<b>#{self.frame_nmr}</b> : -")

                            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_BGR2RGB)
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                            pixmap = QPixmap.fromImage(QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888))
                            
                        else:
                            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, c = img.shape
                            qImg = QImage(img.data, w, h, w * c, QImage.Format_RGB888)

                            pixmap = QPixmap.fromImage(qImg)

                            self.detection_info.setText(f"<b>#{self.frame_nmr}</b> : -")
                    else:
                        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, c = img.shape
                        qImg = QImage(img.data, w, h, w * c, QImage.Format_RGB888)

                        pixmap = QPixmap.fromImage(qImg)

                        self.detection_info.setText(f"<b>#{self.frame_nmr}</b> : -")
                    
                    p = pixmap.scaled(int(640), int(320), Qt.IgnoreAspectRatio)
                    self.video_player.setPixmap(p)

                    current_frame = int(self.video_source.get(cv2.CAP_PROP_POS_FRAMES))
                    total_frames = int(self.video_source.get(cv2.CAP_PROP_FRAME_COUNT))
                    position = (current_frame / total_frames) * 100
                    QTimer.singleShot(10, lambda: self.position_slider.setValue(int(position)))

                    key = cv2.waitKey(int(1000 / (self.base_fps * self.fps_multiplier)))

                    if key == ord('q'):
                        break

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        finally:
            if self.video_source is not None:
                self.video_source.release()
            cv2.destroyAllWindows()

        self.current_video_source = video_src

    def closeEvent(self, event):
        self.stop_video()
        super().closeEvent(event)

    def stop_video(self):
        if self.video_source is not None:
            self.video_source.release()
            cv2.destroyAllWindows()

    def open_image_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "이미지 불러오기", "", "이미지 파일 (*.jpg *.png *.bmp);;모든 파일 (*)", options=options)

        if file_name:
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            self.image_viewer.setPixmap(scaled_pixmap)
            self.image_viewer.setAlignment(Qt.AlignCenter)

    def clear_the_content(self, type):
        ok = QMessageBox.information(self, "알림", f"{type}을(를) 삭제하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
        if ok == QMessageBox.Yes:
            if type == "동영상":
                if self.video_source is not None:
                    self.video_player.clear()      # 비디오 플레이어 내용 지우기
                    self.video_source.release()      # 비디오 소스 종료
                    self.video_source = None
                    self.position_slider.setValue(0) 
            elif type == "이미지":
                self.image_viewer.clear()

            self.setStatusBarMessage(f"{type}을 지웠습니다.")

    def delete_selected_row_on_table(self, target):
        rows_to_delete = []
        count_checkbox = 0

        for row in range(target.rowCount() - 1, -1, -1):
            item_checkbox = target.item(row, 0)

            if item_checkbox and item_checkbox.checkState() == Qt.Checked:
                count_checkbox += 1
                rows_to_delete.append(row)
                
        for row_index in rows_to_delete:
            target.removeRow(row_index)
        
        self.setStatusBarMessage(f"테이블에서 {count_checkbox}개의 행을 삭제하였습니다.")
    
    def on_header_double_clicked_table(self, col, target):
        if col == 0:
            check_state = Qt.Checked if all(target.item(row, 0).checkState() == Qt.Unchecked for row in range(target.rowCount())) else Qt.Unchecked

            for row in range(target.rowCount()):
                item = target.item(row, 0)
                item.setCheckState(check_state)

    def on_button_click(self, type):
        self.button_return_value = 0    # 초기화

        ok = QMessageBox.information(self, "알림", f"{type}을(를) 클릭하였습니다. 맞습니까?", QMessageBox.Yes | QMessageBox.No)

        if ok == QMessageBox.Yes:

            if type == "EV":
                self.button_return_value = 1

            elif type == "One Line":
                self.button_return_value = 2
                
            elif type == "Two Line":
                self.button_return_value = 3
        
        # QMessageBox.information(self, "알림", f"{type}({self.button_return_value})")

        dialog = QDialog(self)
        dialog.setFixedSize(dialog.sizeHint())

        outer_layout = QVBoxLayout()
        
        # 이미지 넣기
        pixmap = self.image_viewer.pixmap()

        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        outer_layout.addWidget(image_label)

        # 설명 넣기
        item_label = QLabel(f"<b>{type}</b>({self.button_return_value})")
        label_font = QFont("Consolas", 9)

        item_label.setAlignment(Qt.AlignCenter)
        item_label.setFont(label_font)
        
        inner_layout = QHBoxLayout()
        inner_layout.addWidget(item_label)

        outer_layout.addLayout(inner_layout)  
        dialog.setLayout(outer_layout)
        dialog.setWindowTitle("차량 사진")
        dialog.setWindowIcon(fugue.icon("car-red"))
        dialog.show()

    def send_kakaotalk_alarm(self):

        QMessageBox.information(self, "알림", "카카오톡으로 메시지를 전송하였습니다.")
    
    def set_position(self, position):
        if self.video_source is not None:
            total_frames = int(self.video_source.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = int((position / 100) * total_frames)
            self.video_source.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            self.frame_nmr = target_frame

    def send_email(self):
        value, ok = QInputDialog.getText(self, "알림", "수신 이메일 주소를 입력하세요: ")

        if ok:
            # 이메일 발송자(관리자) 정보 입력
            from_email = "admin_msteam06@gmail.com"   
            password = "Msteam#06"   

            # 주차 위반 차량 번호
            plate_number = "구현하기"

            subject = "주차 위반 알림"                     # 메시지 제목
            message = f"주차 위반 차량이 발견되었습니다. (차량 번호 : {plate_number})"     # 메시지 내용
            to_email = value                              # 수신자 이메일

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)    # gmail (587)
                server.starttls()
                server.login(from_email, password)
                server.sendmail(from_email, to_email, msg.as_string())
                server.quit()

                self.setStatusBarMessage("이메일이 발송되었습니다.")

            except:
                self.setStatusBarMessage("이메일 발송 중 오류가 발생했습니다")

    def bring_contents_from_csv_file_and_fill_table_event(self, checked):
        self.is_bring_csv_content_working = checked

        if self.is_bring_csv_content_working:
            self.timer = QTimer(self)
            self.timer.timeout.connect(lambda check=self.is_bring_csv_content_working: self.bring_contents_from_csv_file_and_fill_table(check))
            self.timer.start(2000)  # 5초 마다 반복 실행
        else:
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()

    def bring_contents_from_csv_file_and_fill_table(self, check):
        print("CSV 내용을 불러왔습니다.")

        try:
            if self.is_bring_csv_content_working:
                all_infos = []

                base_dir = os.path.dirname(__file__)
                csv_dir = os.path.join(base_dir, "result.csv")
                
                with open(csv_dir, 'r') as file:
                    csv_reader = csv.reader(file)

                    next(csv_reader)    # 첫 번째 행 건너 뛰기 (열 이름)

                    for row in csv_reader:
                        info = []
                        info.append(row[0])    # frame_nmr
                        info.append(float(row[1]))    # car_id
                        info.append(row[2])    # car_bbox
                        info.append(row[3])    # license_plate_bbox

                        info.append(float(row[4]))    # license_plate_bbox_score
                        info.append(row[5])    # license_number
                        info.append(float(row[6]))    # license_number_score
                        all_infos.append(info)

                # print(all_infos)
                target_table = self.tab1_item_list_table
                
                # 테이블 내용 초기화
                target_table.clearContents()
                target_table.setRowCount(0)
                
                for row_info in all_infos:
                    row = target_table.rowCount()
                    target_table.setRowCount(row + 1)

                    # 체크 박스
                    checkbox_item = QTableWidgetItem()
                    checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    checkbox_item.setCheckState(Qt.Unchecked)
                    
                    # row_info 리스트의 인덱스를 사용하여 데이터를 가져옵니다.
                    frame_nmr_item = QTableWidgetItem(str(row_info[0]))  # frame_nmr
                    car_id_item = QTableWidgetItem(str(row_info[1]))  # car_id
                    car_bbox_item = QTableWidgetItem(str(row_info[2]))  # car_bbox
                    license_plate_bbox_item = QTableWidgetItem(str(row_info[3]))  # license_plate_bbox
                    license_plate_bbox_score_item = QTableWidgetItem(str(row_info[4]))  # license_plate_bbox_score
                    license_number_item = QTableWidgetItem(str(row_info[5]))  # license_number
                    license_number_score_item = QTableWidgetItem(str(row_info[6]))  # license_number_score

                    target_table.setItem(row, 0, checkbox_item)
                    target_table.setItem(row, 1, frame_nmr_item)
                    target_table.setItem(row, 2, car_id_item)
                    target_table.setItem(row, 3, car_bbox_item)
                    target_table.setItem(row, 4, license_plate_bbox_item)
                    target_table.setItem(row, 5, license_plate_bbox_score_item)
                    target_table.setItem(row, 6, license_number_item)
                    target_table.setItem(row, 7, license_number_score_item)
        except:
            pass
    
    def load_db_to_table(self, target_table):
        base_dir = os.path.dirname(__file__)
        db_path = os.path.join(base_dir, 'car_plate.db')
        conn = sqlite3.connect(db_path)  
        
        # 커서 생성
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM videos")
        data = cursor.fetchall()

        target_table.setRowCount(len(data))
        target_table.setColumnCount(len(data[0]))

        for row_num, row_data in enumerate(data):
            for col_num, cell_data in enumerate(row_data):
                item = QTableWidgetItem()
                if col_num == 2:
                    item.setData(Qt.UserRole, cell_data)
                    item.setText('📺')
                else:
                    item = QTableWidgetItem(str(cell_data))
                
                target_table.setItem(row_num, col_num, item)

        target_table.itemDoubleClicked.connect(self.play_video2)

        conn.close()

    def play_video2(self, item):
        if item.column() == 2:
            base_dir = os.path.dirname(__file__)
            temp_video_path = os.path.join(base_dir, "temp_video.mp4")

            # 기존의 temp_video 파일 삭제
            for filename in os.listdir(base_dir):
                if "temp_video" in filename:
                    file_path = os.path.join(base_dir, filename)
                    try:
                        os.remove(file_path)
                    except:
                        pass
                        
            video_data = item.data(Qt.UserRole)

            with open(temp_video_path, 'wb') as f:
                f.write(video_data)

            self.play_video(temp_video_path)
    

    def start_detection(self, checked):
        self.is_detection_enabled = checked

        if self.is_detection_enabled:
            # 내용 모두 지우기
            target_table = self.tab1_item_list_table

            target_table.setRowCount(0)
            
            # 열 이름 설정
            column_names = self.tab1_item_list_table_headers 
            target_table.setColumnCount(len(column_names))
            target_table.setHorizontalHeaderLabels(column_names)

            # 테이블에 CSV 파일 내용 넣기
            base_dir = os.path.dirname(__file__)
            file_path = os.path.join(base_dir, 'result_final.csv')

            with open(file_path, newline='', encoding='utf-8') as file:
                try:
                    reader = csv.reader(file)
                    next(reader)
                    data = list(reader)
                except:
                    QMessageBox.warning(self, "알림", "파일의 인코딩 방식에 문제가 있습니다.")
                
                target_table.setRowCount(len(data))

                for row_idx, row_data in enumerate(data):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(cell_data.strip())
                        
                        # 폰트 설정
                        cell_font = QFont("Consolas", 9)
                        item.setFont(cell_font)

                        if col_idx == 0:
                            row_checkbox = QTableWidgetItem()
                            row_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                            row_checkbox.setCheckState(Qt.Unchecked)
                            target_table.setColumnWidth(0, 16)
                            target_table.setItem(row_idx, col_idx, row_checkbox)

                        target_table.setItem(row_idx, col_idx + 1, item)    # 체크박스 빼고 넣기

    def bring_detection_info_from_table(self, checked):
        self.is_bring_detection_info_from_table_enabled = checked

    def show_car_image(self, item):
        if item.column() == 1 and hasattr(self, 'current_video_source'):  # "frame_nmr" 열을 더블 클릭한 경우
            frame_nmr = int(item.text())
            car_bbox = self.tab1_item_list_table.item(item.row(), 3).text().replace("[", "").replace("]", "")
            car_bbox = [int(float(coord)) for coord in car_bbox.split()]
            video_frame = self.get_video_frame(frame_nmr)
            car_image = self.extract_car_image(video_frame, car_bbox)
            self.tab1_image_viewer.setPixmap(self.convert_opencv_image_to_pixmap(car_image))


    def get_video_frame(self, frame_nmr):
        cap = cv2.VideoCapture(self.current_video_source)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nmr)
        
        ret, frame = cap.read()  # 프레임 읽기

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        else:
            raise Exception("Failed to read frame")

        cap.release()

    def extract_car_image(self, video_frame, car_bbox):
        x1, y1, x2, y2 = car_bbox
        car_image = video_frame[y1:y2, x1:x2]
        return car_image


    def show_image_in_new_window(self, image):
        if self.image_window is not None:
            self.image_window.close()  

        self.image_window = QMainWindow()
        self.image_window.setWindowTitle("차량 사진")
        self.image_window.setWindowIcon(fugue.icon("car-red"))
        self.image_window.setFixedSize(640, 640)  # 창 크기 고정

        image_label = QLabel()
        image_pixmap = self.convert_opencv_image_to_pixmap(image)

        # 이미지 크기를 창의 크기 비율에 맞게 조정
        image_pixmap = image_pixmap.scaled(640, 640, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 이미지를 가운데 정렬
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setPixmap(image_pixmap)

        self.image_window.setCentralWidget(image_label)

        # 버튼 추가
        button_layout = QHBoxLayout()
        button_ev = QPushButton('EV', self.image_window)
        button_one_line_ev = QPushButton('One Line', self.image_window)
        button_two_line_ev = QPushButton('Two Line', self.image_window)

        button_style = (
            "QPushButton {"
            "   background-color: #4CAF50;"
            "   border: none;"
            "   color: white;"
            "   padding: 10px 20px;"
            "   text-align: center;"
            "   text-decoration: none;"
            "   display: inline-block;"
            "   font-size: 16px;"
            "   margin: 4px 2px;"
            "   cursor: pointer;"
            "   border-radius: 8px;"
            "   font-weight: bold;"
            "   font-family: Consolas;"
            "}"
            "QPushButton:hover {"
            "   background-color: #45a049;"
            "}"
            "QPushButton:pressed {"
            "   background-color: #367d39;"
            "}"
        )

        button_ev.setStyleSheet(button_style)
        button_one_line_ev.setStyleSheet(button_style)
        button_two_line_ev.setStyleSheet(button_style)

        # 버튼 위치 및 크기 설정
        button_height = 50
        button_width = 150
        button_margin = 10

        button_ev.setFixedSize(button_width, button_height)
        button_one_line_ev.setFixedSize(button_width, button_height)
        button_two_line_ev.setFixedSize(button_width, button_height)

        button_layout.addWidget(button_ev)
        button_layout.addWidget(button_one_line_ev)
        button_layout.addWidget(button_two_line_ev)

        # 수직 레이아웃 생성 및 위젯 추가
        layout_outer = QVBoxLayout()
        layout_outer.addWidget(image_label)
        layout_outer.addLayout(button_layout)

        widget = QWidget()
        widget.setLayout(layout_outer)

        self.image_window.setCentralWidget(widget)
        self.image_window.show()

    def convert_opencv_image_to_pixmap(self, image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_image = QImage(image.data.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(q_image)

    def make_csv_file(self):
        import torch
        import torch.nn.functional as F
        import torch.utils.data
        import torchvision.transforms as transforms

        base_dir = os.path.dirname(__file__)

        def load_models(self):
            self.yolo_best_pt_dir = os.path.join(base_dir, "models", "yolo_best.pt")
            self.pose_best_pt_dir = os.path.join(base_dir, "models", "pose_best.pt")
            self.twoline_best_pt_dir = os.path.join(base_dir, "models", "twoline_best.pt")
            self.yml_dir = os.path.join(base_dir, "opt.yaml")
        
        def set_paths(self):
            save_path_result, save_path_detection_error, save_path_white, save_path_blue, save_path_twoline = util_file.save_file()
            self.save_path_result = os.path.join(base_dir, save_path_result)
            self.save_path_detection_error = os.path.join(base_dir, save_path_detection_error)
            self.save_path_white = os.path.join(base_dir, save_path_white)
            self.save_path_blue = os.path.join(base_dir, save_path_blue)
            self.save_path_twoline = os.path.join(base_dir, save_path_twoline)
    

        model = YOLO(self.yolo_best_pt_dir)
        # mot_tracker = Sort()

        # 테스트 데이터가 있는 폴더 경로 찾기
        data_path = None

        target_dir = os.path.join(base_dir, "uploads")
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if "compressed_" in file:
                    data_path = os.path.join(root, file)

    
    def open_browser_with_Chrome(self, url):
        target_url = url

        chrome_browser_path = "C:/Program Files/Google/Chrome/Application/chrome.exe" 
        edge_browser_path = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"    

        process = QProcess(self)
        try:
            process.startDetached(edge_browser_path, [target_url])
        except:
            process.startDetached(chrome_browser_path, [target_url])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())