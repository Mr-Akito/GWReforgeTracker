# ui/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt
from config import ThemeColors, ColorSchemeMode, Professions, AppConfig

class CustomDialog(QDialog):
    def __init__(self, title, message, parent=None, is_confirmation=True, show_input=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: #23232A;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
            }}
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(25, 25, 25, 25)
        c_layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 19px; font-weight: bold; color: {ThemeColors.GOLD}; border: none;")
        c_layout.addWidget(title_label)
        
        if message:
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet(f"color: {ThemeColors.WHITE}; font-size: 13px; border: none; margin-bottom: 5px;")
            c_layout.addWidget(msg_label)
        
        self.input_field = None
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if is_confirmation or show_input:
            self.reject_btn = QPushButton("Cancel" if show_input else "No")
            self.reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.reject_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.08);
                    color: {ThemeColors.WHITE};
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 12px;
                    padding: 8px 18px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.15); }}
            """)
            self.reject_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.reject_btn)
        
        self.accept_btn = QPushButton("Yes" if is_confirmation and not show_input else ("Create" if show_input else "OK"))
        self.accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accept_btn.clicked.connect(self.accept)
        
        if show_input:
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText("Enter name...")
            self.input_field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: rgba(0, 0, 0, 0.4);
                    border: 1px solid #555;
                    border-radius: 10px;
                    padding: 9px 12px;
                    color: #fff;
                    font-size: 13px;
                }}
                QLineEdit:focus {{ border: 1px solid {ThemeColors.GOLD}; }}
            """)
            self.input_field.textChanged.connect(self.validate_input)
            self.input_field.returnPressed.connect(self.on_return_pressed)
            c_layout.addWidget(self.input_field)
        
        if is_confirmation and not show_input:
            btn_style = f"""
                QPushButton {{
                    background-color: rgba(255, 107, 107, 0.15);
                    color: {ThemeColors.RED};
                    border: 1px solid {ThemeColors.RED};
                    border-radius: 12px;
                    padding: 8px 18px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background-color: rgba(255, 107, 107, 0.28); }}
            """
        else:
            btn_style = f"""
                QPushButton {{
                    background-color: rgba(212, 175, 55, 0.18);
                    color: {ThemeColors.GOLD};
                    border: 1px solid {ThemeColors.GOLD};
                    border-radius: 12px;
                    padding: 8px 18px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background-color: rgba(212, 175, 55, 0.32); }}
            """
        
        self.accept_btn.setStyleSheet(btn_style)
        if show_input:
            self.accept_btn.setEnabled(False)
            self.accept_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 100, 100, 0.15);
                    color: #777;
                    border: 1px solid #444;
                    border-radius: 12px;
                    padding: 8px 18px;
                    font-weight: 600;
                }
            """)
            
        btn_layout.addWidget(self.accept_btn)
        c_layout.addLayout(btn_layout)
        layout.addWidget(container)
    
    def validate_input(self, text):
        if self.input_field:
            has_text = len(text.strip()) > 0
            self.accept_btn.setEnabled(has_text)
            if has_text:
                self.accept_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(212, 175, 55, 0.18);
                        color: {ThemeColors.GOLD};
                        border: 1px solid {ThemeColors.GOLD};
                        border-radius: 12px;
                        padding: 8px 18px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{ background-color: rgba(212, 175, 55, 0.32); }}
                """)
            else:
                self.accept_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(100, 100, 100, 0.15);
                        color: #777;
                        border: 1px solid #444;
                        border-radius: 12px;
                        padding: 8px 18px;
                        font-weight: 600;
                    }
                """)

    def on_return_pressed(self):
        if self.accept_btn.isEnabled(): self.accept()

    def get_input_text(self):
        return self.input_field.text() if self.input_field else ""


class SettingsDialog(QDialog):
    def __init__(self, current_scheme, is_dark_wiki, show_hidden, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(440)
        
        self.selected_scheme = current_scheme
        self.is_dark_wiki = is_dark_wiki
        self.show_hidden = show_hidden
        
        layout = QVBoxLayout(self)
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: #23232A;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 18px;
            }}
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(25, 25, 25, 25)
        c_layout.setSpacing(18)
        
        title_label = QLabel("Settings & Preferences")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeColors.GOLD}; border: none;")
        c_layout.addWidget(title_label)
        
        # --- Color Scheme Section ---
        c_layout.addWidget(QLabel("Quest Status Color Scheme:", objectName="SubText"))
        scheme_frame = QFrame()
        scheme_frame.setStyleSheet("background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 10px;")
        scheme_layout = QVBoxLayout(scheme_frame)
        scheme_layout.setSpacing(10)
        
        self.scheme_group = QButtonGroup(self)
        
        self.rb_classic = QRadioButton("Classic Scheme\n(In-Progress: Green, Completed: Gold)")
        self.rb_classic.setStyleSheet(f"color: {ThemeColors.WHITE}; font-size: 12px;")
        self.rb_alternate = QRadioButton("Alternate Scheme\n(In-Progress: Yellow, Completed: Green)")
        self.rb_alternate.setStyleSheet(f"color: {ThemeColors.WHITE}; font-size: 12px;")
        
        self.scheme_group.addButton(self.rb_classic)
        self.scheme_group.addButton(self.rb_alternate)
        
        if current_scheme == ColorSchemeMode.ALTERNATE:
            self.rb_alternate.setChecked(True)
        else:
            self.rb_classic.setChecked(True)
            
        scheme_layout.addWidget(self.rb_classic)
        scheme_layout.addWidget(self.rb_alternate)
        c_layout.addWidget(scheme_frame)
        
        # --- Preferences Section ---
        c_layout.addWidget(QLabel("Display & Features:", objectName="SubText"))
        opt_frame = QFrame()
        opt_frame.setStyleSheet("background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 10px;")
        opt_layout = QVBoxLayout(opt_frame)
        opt_layout.setSpacing(10)
        
        self.cb_dark = QCheckBox("Dark Theme for Wiki Viewer")
        self.cb_dark.setChecked(self.is_dark_wiki)
        self.cb_dark.setStyleSheet(f"color: {ThemeColors.WHITE}; font-size: 12px;")
        opt_layout.addWidget(self.cb_dark)
        
        self.cb_hidden = QCheckBox("Show Hidden Quests in List")
        self.cb_hidden.setChecked(self.show_hidden)
        self.cb_hidden.setStyleSheet(f"color: {ThemeColors.WHITE}; font-size: 12px;")
        opt_layout.addWidget(self.cb_hidden)
        
        c_layout.addWidget(opt_frame)
        
        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFF;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Preferences")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(212, 175, 55, 0.2);
                color: {ThemeColors.GOLD};
                border: 1px solid {ThemeColors.GOLD};
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: rgba(212, 175, 55, 0.35); }}
        """)
        save_btn.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(save_btn)
        
        c_layout.addLayout(btn_layout)
        layout.addWidget(container)
        
    def _save_and_accept(self):
        self.selected_scheme = ColorSchemeMode.ALTERNATE if self.rb_alternate.isChecked() else ColorSchemeMode.CLASSIC
        self.is_dark_wiki = self.cb_dark.isChecked()
        self.show_hidden = self.cb_hidden.isChecked()
        self.accept()
