import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSpacerItem,
    QSizePolicy,
    QListWidget,
    QLabel,
    QScrollArea,
    QInputDialog,
    QComboBox,
    QMenu,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QTimer
from PyQt6.QtGui import QIcon, QAction
from datetime import datetime
import requests
import json


class ChatListItem(QWidget):
    """ویجت سفارشی برای هر آیتم چت با دکمه تنظیمات"""
    def __init__(self, chat_name, chat_index, parent_window):
        super().__init__()
        self.chat_index = chat_index
        self.parent_window = parent_window
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # نام چت
        self.name_label = QLabel(chat_name)
        self.name_label.setStyleSheet("color: #ffffff; font-size: 13px;")
        layout.addWidget(self.name_label, 1)
        
        # دکمه تنظیمات (چرخ دنده)
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(25, 25)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                color: #ffffff;
            }
        """)
        self.settings_button.clicked.connect(self.show_menu)
        layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        
    def show_menu(self):
        """نمایش منوی تنظیمات"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        # گزینه تغییر نام
        rename_action = QAction("✏️ تغییر نام", self)
        rename_action.triggered.connect(self.rename_chat)
        menu.addAction(rename_action)
        
        # گزینه حذف
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(self.delete_chat)
        menu.addAction(delete_action)
        
        # استایل قرمز برای حذف
        for action in menu.actions():
            if "حذف" in action.text():
                font = action.font()
                action.setFont(font)
        
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 3px;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            QMenu::item:last-child {
                color: #ff4444;
            }
        """)
        
        menu.exec(self.settings_button.mapToGlobal(self.settings_button.rect().bottomLeft()))
    
    def rename_chat(self):
        """تغییر نام چت"""
        current_name = self.parent_window.chats[self.chat_index]["name"]
        new_name, ok = QInputDialog.getText(
            self, "تغییر نام چت", "نام جدید چت:", text=current_name
        )
        if ok and new_name.strip():
            self.parent_window.chats[self.chat_index]["name"] = new_name.strip()
            self.name_label.setText(new_name.strip())
            # به‌روزرسانی نام در label نمایش چت
            if self.chat_index == self.parent_window.current_chat_index:
                self.parent_window.chat_name_label.setText(new_name.strip())
            print(f"نام چت تغییر یافت به: {new_name.strip()}")
    
    def delete_chat(self):
        """حذف چت"""
        self.parent_window.delete_chat(self.chat_index)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChatBot")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: #1e1e1e;")

        # ویجت مرکزی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # لایوت اصلی افقی
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        main_horizontal_layout.setSpacing(0)
        central_widget.setLayout(main_horizontal_layout)

        # ===== بخش اصلی چت =====
        chat_widget = QWidget()
        chat_main_layout = QVBoxLayout()
        chat_main_layout.setContentsMargins(10, 10, 10, 10)
        chat_widget.setLayout(chat_main_layout)
        chat_widget.setStyleSheet("background-color: #1e1e1e;")

        # ===== هدر بالای صفحه =====
        header_layout = QHBoxLayout()
        
        # اسپیسر چپ برای مرکز کردن
        header_layout.addStretch(1)

        # Label برای نمایش نام چت (بدون قابلیت تغییر)
        self.chat_name_label = QLabel("چت ۱")
        self.chat_name_label.setFixedHeight(35)
        self.chat_name_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 5px 15px;
                font-size: 13px;
            }
        """)
        header_layout.addWidget(self.chat_name_label)
        
        # دکمه toggle سایدبار (فلش) - سمت راست Label
        self.toggle_sidebar_button = QPushButton("◀")
        self.toggle_sidebar_button.setFixedSize(35, 35)
        self.toggle_sidebar_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4CAF50;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
        """)
        self.toggle_sidebar_button.clicked.connect(self.toggle_sidebar)
        
        header_layout.addWidget(self.toggle_sidebar_button)
        
        # اسپیسر راست برای مرکز کردن
        header_layout.addStretch(1)
        
        chat_main_layout.addLayout(header_layout)

        # ===== بخش نمایش پیام‌ها =====
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
        """)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(10)
        self.messages_widget.setLayout(self.messages_layout)
        self.messages_widget.setStyleSheet("background-color: #1e1e1e;")

        self.messages_scroll.setWidget(self.messages_widget)
        chat_main_layout.addWidget(self.messages_scroll)

        # بخش ورودی + دکمه (کوچکتر - 70%)
        input_container_layout = QHBoxLayout()
        input_container_layout.addStretch(15)  # فضای خالی سمت چپ

        # دکمه ارسال (دایره‌ای)
        self.submit_button = QPushButton("↑")
        self.submit_button.setFixedSize(40, 40)
        self.submit_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                padding: 0;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #4CAF50;
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border-color: #3d8b40;
            }
        """)
        self.submit_button.clicked.connect(self.submit_prompt)

        # ورودی متن
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("اینجا پرامپت خود را بنویسید...")
        self.prompt_input.setFixedHeight(40)
        self.prompt_input.setStyleSheet("""
            QLineEdit {
                border-radius: 20px;
                padding: 0 15px;
                font-size: 14px;
                border: 2px solid #3d3d3d;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.prompt_input.returnPressed.connect(self.submit_prompt)

        # افزودن ویجت‌ها به لایوت افقی
        input_container_layout.addWidget(self.submit_button)
        input_container_layout.addWidget(self.prompt_input, 70)  # 70% فضا
        input_container_layout.addStretch(15)  # فضای خالی سمت راست

        # افزودن لایوت افقی به لایوت عمودی
        chat_main_layout.addLayout(input_container_layout)

        # اسپایسر پایین
        chat_main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # ===== سایدبار سمت راست =====
        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_widget.setLayout(sidebar_layout)
        self.sidebar_widget.setFixedWidth(250)
        self.sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-left: 1px solid #3d3d3d;
            }
        """)

        # دکمه چت جدید
        self.new_chat_button = QPushButton("گفت‌وگو جدید")
        self.new_chat_button.setFixedHeight(40)
        self.new_chat_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.new_chat_button.clicked.connect(self.create_new_chat)

        # لیست چت‌های قبلی
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 5px;
                margin: 2px 0;
                background-color: transparent;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: transparent;
                color: white;
            }
        """)
        self.chat_list.itemClicked.connect(self.load_chat)

        # افزودن به سایدبار
        sidebar_layout.addWidget(self.new_chat_button)
        sidebar_layout.addWidget(self.chat_list)

        # ===== ترکیب سایدبار و چت =====
        main_horizontal_layout.addWidget(chat_widget, 1)
        main_horizontal_layout.addWidget(self.sidebar_widget)

        # لیست چت‌ها (ذخیره داخلی)
        self.chats = []
        self.current_chat_index = None
        self.sidebar_visible = True
        
        # متغیرهای مربوط به تایپینگ
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_char)
        self.current_typing_text = ""
        self.current_typing_index = 0
        self.current_typing_label = None

        # ایجاد اولین چت
        self.create_new_chat()

    def toggle_sidebar(self):
        """باز و بسته کردن سایدبار با انیمیشن"""
        if self.sidebar_visible:
            # بستن سایدبار
            self.animation = QPropertyAnimation(self.sidebar_widget, b"maximumWidth")
            self.animation.setDuration(300)
            self.animation.setStartValue(250)
            self.animation.setEndValue(0)
            self.animation.finished.connect(lambda: self.sidebar_widget.hide())
            self.animation.start()
            self.sidebar_visible = False
            self.toggle_sidebar_button.setText("▶")  # تغییر جهت فلش
        else:
            # باز کردن سایدبار
            self.sidebar_widget.show()
            self.animation = QPropertyAnimation(self.sidebar_widget, b"maximumWidth")
            self.animation.setDuration(300)
            self.animation.setStartValue(0)
            self.animation.setEndValue(250)
            self.animation.start()
            self.sidebar_visible = True
            self.toggle_sidebar_button.setText("◀")  # تغییر جهت فلش

    def create_new_chat(self):
        """ایجاد یک چت جدید"""
        chat_name = f"چت {len(self.chats) + 1}"
        self.chats.append({"name": chat_name, "messages": []})
        
        # ایجاد آیتم سفارشی
        item = QListWidgetItem(self.chat_list)
        chat_widget = ChatListItem(chat_name, len(self.chats) - 1, self)
        item.setSizeHint(chat_widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, chat_widget)
        
        self.current_chat_index = len(self.chats) - 1
        self.chat_list.setCurrentRow(self.current_chat_index)
        self.chat_name_label.setText(chat_name)
        self.clear_messages_display()
        print(f"چت جدید ایجاد شد: {chat_name}")

    def delete_chat(self, chat_index):
        """حذف یک چت"""
        if len(self.chats) <= 1:
            print("نمی‌توانید آخرین چت را حذف کنید")
            return
        
        # حذف از لیست داخلی
        del self.chats[chat_index]
        
        # حذف از لیست ویجت
        self.chat_list.takeItem(chat_index)
        
        # به‌روزرسانی ایندکس‌ها
        for i in range(chat_index, self.chat_list.count()):
            item = self.chat_list.item(i)
            widget = self.chat_list.itemWidget(item)
            if widget:
                widget.chat_index = i
        
        # انتخاب چت جدید
        if self.current_chat_index >= len(self.chats):
            self.current_chat_index = len(self.chats) - 1
        
        self.chat_list.setCurrentRow(self.current_chat_index)
        self.chat_name_label.setText(self.chats[self.current_chat_index]["name"])
        self.display_chat_messages()
        print(f"چت حذف شد")

    def load_chat(self, item):
        """بارگذاری یک چت از لیست"""
        chat_index = self.chat_list.row(item)
        self.current_chat_index = chat_index
        self.chat_name_label.setText(self.chats[chat_index]["name"])
        self.display_chat_messages()
        print(f"چت بارگذاری شد: {self.chats[chat_index]['name']}")

    def submit_prompt(self):
        """ارسال پرامپت"""
        prompt_text = self.prompt_input.text().strip()
        if prompt_text and self.current_chat_index is not None:
            # ذخیره پیام در چت فعلی
            self.chats[self.current_chat_index]["messages"].append({
                "role": "user",
                "content": prompt_text
            })
            self.display_message(prompt_text, "user")
            print(f"پرامپت ارسالی: {prompt_text}")
            self.prompt_input.clear()
            
            # غیرفعال کردن ورودی و دکمه
            self.prompt_input.setEnabled(False)
            self.submit_button.setEnabled(False)
            
            # نمایش پیام "در حال پاسخگویی..."
            self.display_message("در حال پاسخگویی...", "assistant_loading")
            
            # ارسال به API
            QTimer.singleShot(100, lambda: self.send_to_lm_studio(prompt_text))
        else:
            print("پرامپت خالی است یا چتی انتخاب نشده.")

    def send_to_lm_studio(self, prompt_text):
        """ارسال درخواست به LM Studio API"""
        try:
            url = "http://localhost:1234/v1/chat/completions"
            
            # ساخت لیست پیام‌ها برای API
            messages = []
            for msg in self.chats[self.current_chat_index]["messages"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # ارسال درخواست
            response = requests.post(
                url,
                json={
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                
                # حذف پیام "در حال پاسخگویی..."
                self.remove_last_message()
                
                # ذخیره پاسخ دستیار
                self.chats[self.current_chat_index]["messages"].append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                # نمایش پاسخ با افکت تایپینگ
                self.start_typing_effect(assistant_message)
            else:
                self.remove_last_message()
                error_msg = f"خطا: {response.status_code}"
                self.display_message(error_msg, "assistant")
                print(f"خطای API: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            self.remove_last_message()
            error_msg = "خطا: اتصال به LM Studio برقرار نشد. لطفاً سرور را روشن کنید."
            self.display_message(error_msg, "assistant")
            print("خطای اتصال به LM Studio")
        
        except Exception as e:
            self.remove_last_message()
            error_msg = f"خطا: {str(e)}"
            self.display_message(error_msg, "assistant")
            print(f"خطای ناشناخته: {str(e)}")
        
        finally:
            # فعال کردن دوباره ورودی و دکمه
            self.prompt_input.setEnabled(True)
            self.submit_button.setEnabled(True)
            self.prompt_input.setFocus()

    def start_typing_effect(self, text):
        """شروع افکت تایپینگ برای پیام دستیار"""
        self.current_typing_text = text
        self.current_typing_index = 0
        
        # ایجاد پیام خالی برای دستیار
        message_widget = QWidget()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(5, 5, 5, 5)
        message_widget.setLayout(message_layout)

        self.current_typing_label = QLabel("")
        self.current_typing_label.setWordWrap(True)
        self.current_typing_label.setMaximumWidth(900)  # افزایش عرض به 3 برابر (از 300 به 900)
        self.current_typing_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.current_typing_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
        """)
        
        message_layout.addWidget(self.current_typing_label)
        message_layout.addStretch()

        self.messages_layout.addWidget(message_widget)
        
        # شروع تایمر تایپینگ (سرعت: هر 20 میلی‌ثانیه یک کاراکتر)
        self.typing_timer.start(20)

    def type_next_char(self):
        """نمایش کاراکتر بعدی در افکت تایپینگ"""
        if self.current_typing_index < len(self.current_typing_text):
            self.current_typing_index += 1
            self.current_typing_label.setText(self.current_typing_text[:self.current_typing_index])
            
            # اسکرول به پایین
            self.messages_scroll.verticalScrollBar().setValue(
                self.messages_scroll.verticalScrollBar().maximum()
            )
        else:
            # پایان تایپینگ
            self.typing_timer.stop()
            self.current_typing_label = None

    def remove_last_message(self):
        """حذف آخرین پیام از نمایش"""
        if self.messages_layout.count() > 0:
            last_item = self.messages_layout.takeAt(self.messages_layout.count() - 1)
            if last_item.widget():
                last_item.widget().deleteLater()

    def display_message(self, text, role):
        """نمایش یک پیام در بخش چت"""
        message_widget = QWidget()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(5, 5, 5, 5)
        message_widget.setLayout(message_layout)

        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if role == "user":
            message_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    color: white;
                    padding: 10px;
                    border-radius: 10px;
                    font-size: 14px;
                }
            """)
            message_layout.addStretch()
            message_layout.addWidget(message_label)
        elif role == "assistant_loading":
            message_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    color: #888888;
                    padding: 10px;
                    border-radius: 10px;
                    font-size: 14px;
                    font-style: italic;
                }
            """)
            message_layout.addWidget(message_label)
            message_layout.addStretch()
        else:
            message_label.setMaximumWidth(900)  # افزایش عرض به 3 برابر (از 300 به 900)
            message_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    color: white;
                    padding: 10px;
                    border-radius: 10px;
                    font-size: 14px;
                }
            """)
            message_layout.addWidget(message_label)
            message_layout.addStretch()

        self.messages_layout.addWidget(message_widget)
        
        # اسکرول به پایین
        self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()
        )

    def display_chat_messages(self):
        """نمایش تمام پیام‌های چت فعلی"""
        self.clear_messages_display()
        if self.current_chat_index is not None:
            messages = self.chats[self.current_chat_index]["messages"]
            for msg in messages:
                self.display_message(msg["content"], msg["role"])

    def clear_messages_display(self):
        """پاک کردن تمام پیام‌های نمایش داده شده"""
        while self.messages_layout.count():
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
