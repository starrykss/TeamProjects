import sys
import pyqt5_fugueicons as fugue

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QImage, QCursor, QFont
from PyQt5.QtCore import Qt, QEvent

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("의류 피팅 서비스 - MS AI School Team 06")
        self.setFixedSize(700, 800)
        self.setWindowIcon(fugue.icon("dress", size=16, fallback_size=True))

        self.central_widget = QTabWidget(self)
        self.setCentralWidget(self.central_widget)

        tab1 = QWidget()
        self.central_widget.addTab(tab1, "시연1")
        self.setup_tab1(tab1)

        tab2 = QWidget()
        self.central_widget.addTab(tab2, "시연2")
        self.setup_tab2(tab2)

    def setup_tab1(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        title_label = QLabel("👗 의류 피팅 서비스")
        title_font = QFont("Malgun Gothic", 18, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label) 

        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)

        self.left_label = QLabel()
        left_pixmap = QPixmap('./img/m0.jpg')
        self.left_label.setPixmap(left_pixmap)
        left_layout.addWidget(self.left_label, alignment=Qt.AlignCenter) 

        right_labels = []
        for i in range(1, 5):
            right_label = QLabel()
            right_pixmap = QPixmap(f'./img/{i}.jpg')
            right_label.setPixmap(right_pixmap)
            right_labels.append(right_label)
            right_layout.addWidget(right_label, alignment=Qt.AlignCenter) 

        def label_click(index):
            left_pixmap = QPixmap(f'./img/m{index}.png')
            self.left_label.setPixmap(left_pixmap)

        for i, right_label in enumerate(right_labels):
            right_label.mousePressEvent = lambda event, index=i: label_click(index + 1)

        original_button = QPushButton("원본 사진")
        original_button.clicked.connect(self.show_original_image)
        right_layout.addWidget(original_button, alignment=Qt.AlignCenter)

    def show_original_image(self):
        left_pixmap = QPixmap('./img/m0.jpg')
        self.left_label.setPixmap(left_pixmap)
    
    def setup_tab2(self, tab): 
        layout = QVBoxLayout(tab)
        grid_layout = QGridLayout()
        
        title_label = QLabel("👗 의류 피팅 서비스")
        title_font = QFont("Malgun Gothic", 18, QFont.Bold)
        title_label.setFont(title_font)

        layout.addWidget(title_label)
        layout.addLayout(grid_layout)

        self.img_labels = []

        for i in range(3):
            for j in range(3):
                img_label = QLabel()
                img_path = f'./img/{chr(ord("a") + i * 3 + j)}.jpg'
                pixmap = QPixmap(img_path)
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignCenter)
                self.img_labels.append(img_label)
                grid_layout.addWidget(img_label, i, j)

        for i, img_label in enumerate(self.img_labels):
            img_label.setCursor(QCursor(Qt.PointingHandCursor))
            img_label.installEventFilter(self) 
            img_label.index = i 

    def label_entered(self, index):
        img_path = f'./img/{chr(ord("a") + index)}1.jpg'
        pixmap = QPixmap(img_path)
        self.img_labels[index].setPixmap(pixmap)

    def label_left(self, index):
        img_path = f'./img/{chr(ord("a") + index)}.jpg'
        pixmap = QPixmap(img_path)
        self.img_labels[index].setPixmap(pixmap)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Enter:
            index = source.index  
            if index is not None:
                self.label_entered(index) 
        elif event.type() == QEvent.Leave:
            index = source.index 
            if index is not None:
                self.label_left(index)  
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()