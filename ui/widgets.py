# ui/widgets.py
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel,
    QCheckBox, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QSize
from PySide6.QtGui import QCursor, QAction
from config import AppConfig, ThemeColors, QuestStatus, FilterMode, Professions, ColorSchemeMode, MUTUALLY_EXCLUSIVE_QUESTS
from .style import create_custom_icon

class FilterSelectorWidget(QWidget):
    filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.current_filter = FilterMode.ALL
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedWidth(145) 
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.main_button = QPushButton()
        self.main_button.setObjectName("FilterMainBtn")
        self.main_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_button.clicked.connect(self.toggle_menu)
        self.main_button.setFixedHeight(36)
        
        btn_layout = QHBoxLayout(self.main_button)
        btn_layout.setContentsMargins(10, 0, 10, 0)
        
        self.icon_label = QLabel()
        self.icon_label.setPixmap(create_custom_icon("filter", ThemeColors.WHITE).pixmap(14, 14))
        self.icon_label.setFixedSize(14, 14)
        
        self.filter_label = QLabel(FilterMode.ALL)
        self.filter_label.setStyleSheet(f"color: {ThemeColors.WHITE}; font-weight: 600; font-size: 11px; border: none; background: transparent;")
        
        self.dropdown_icon = QLabel("▼")
        self.dropdown_icon.setStyleSheet(f"color: {ThemeColors.GOLD}; font-size: 9px; border: none; background: transparent;")
        
        btn_layout.addWidget(self.icon_label)
        btn_layout.addWidget(self.filter_label)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.dropdown_icon)
        
        self.main_layout.addWidget(self.main_button)
        
        self.dropdown_container = QFrame()
        self.dropdown_container.setObjectName("FilterContainer")
        self.dropdown_container.setMaximumHeight(0) 
        
        self.list_layout = QVBoxLayout(self.dropdown_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(2)
        
        self.options = [FilterMode.ALL, FilterMode.NOT_STARTED, FilterMode.IN_PROGRESS, FilterMode.COMPLETED]
        for opt in self.options:
            btn = QPushButton(opt)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(26) 
            btn.clicked.connect(lambda checked, o=opt: self.select_filter(o))
            self.list_layout.addWidget(btn)

        self.main_layout.addWidget(self.dropdown_container)
        
        self.animation = QPropertyAnimation(self.dropdown_container, b"maximumHeight")
        self.animation.setDuration(140)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle_menu(self):
        if self.is_expanded: self.collapse_menu()
        else: self.expand_menu()
            
    def expand_menu(self):
        self.dropdown_icon.setText("▲") 
        target_h = (len(self.options) * 28) + 8 
        self.animation.stop()
        self.animation.setStartValue(self.dropdown_container.height())
        self.animation.setEndValue(target_h)
        self.animation.start()
        self.is_expanded = True
    
    def collapse_menu(self):
        if not self.is_expanded: return
        self.dropdown_icon.setText("▼")
        self.animation.setStartValue(self.dropdown_container.height())
        self.animation.setEndValue(0)
        self.animation.start()
        self.is_expanded = False

    def select_filter(self, mode):
        self.current_filter = mode
        self.filter_label.setText(mode)
        self.filter_changed.emit(mode)
        self.collapse_menu()


class ProfessionSelectorWidget(QWidget):
    profession_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.current_profession = Professions.ALL
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedWidth(145) 
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.main_button = QPushButton()
        self.main_button.setObjectName("ProfessionMainBtn")
        self.main_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_button.clicked.connect(self.toggle_menu)
        self.main_button.setFixedHeight(36)
        
        btn_layout = QHBoxLayout(self.main_button)
        btn_layout.setContentsMargins(10, 0, 10, 0)
        
        self.icon_label = QLabel()
        self.icon_label.setPixmap(create_custom_icon("user", ThemeColors.GOLD).pixmap(14, 14))
        self.icon_label.setFixedSize(14, 14)
        
        self.prof_label = QLabel("Class: All")
        self.prof_label.setStyleSheet(f"color: {ThemeColors.WHITE}; font-weight: 600; font-size: 11px; border: none; background: transparent;")
        
        self.dropdown_icon = QLabel("▼")
        self.dropdown_icon.setStyleSheet(f"color: {ThemeColors.GOLD}; font-size: 9px; border: none; background: transparent;")
        
        btn_layout.addWidget(self.icon_label)
        btn_layout.addWidget(self.prof_label)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.dropdown_icon)
        
        self.main_layout.addWidget(self.main_button)
        
        self.dropdown_container = QFrame()
        self.dropdown_container.setObjectName("ProfessionContainer")
        self.dropdown_container.setMaximumHeight(0) 
        
        self.list_layout = QVBoxLayout(self.dropdown_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(2)
        
        self.options = Professions.ALL_LIST
        for opt in self.options:
            btn = QPushButton(opt)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(24) 
            btn.clicked.connect(lambda checked, o=opt: self.select_profession(o))
            self.list_layout.addWidget(btn)

        self.main_layout.addWidget(self.dropdown_container)
        
        self.animation = QPropertyAnimation(self.dropdown_container, b"maximumHeight")
        self.animation.setDuration(160)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle_menu(self):
        if self.is_expanded: self.collapse_menu()
        else: self.expand_menu()
            
    def expand_menu(self):
        self.dropdown_icon.setText("▲") 
        target_h = (len(self.options) * 26) + 8 
        self.animation.stop()
        self.animation.setStartValue(self.dropdown_container.height())
        self.animation.setEndValue(target_h)
        self.animation.start()
        self.is_expanded = True
    
    def collapse_menu(self):
        if not self.is_expanded: return
        self.dropdown_icon.setText("▼")
        self.animation.setStartValue(self.dropdown_container.height())
        self.animation.setEndValue(0)
        self.animation.start()
        self.is_expanded = False

    def select_profession(self, prof):
        self.current_profession = prof
        display = "Class: All" if prof == Professions.ALL else prof
        self.prof_label.setText(display)
        self.profession_changed.emit(prof)
        self.collapse_menu()

    def set_profession(self, prof):
        self.current_profession = prof
        display = "Class: All" if prof == Professions.ALL else prof
        self.prof_label.setText(display)


class ProfileSelectorWidget(QWidget):
    profile_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.main_button = QPushButton()
        self.main_button.setObjectName("ProfileMainBtn")
        self.main_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_button.clicked.connect(self.toggle_menu)
        self.main_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_button.setFixedHeight(38) 
        
        btn_layout = QHBoxLayout(self.main_button)
        btn_layout.setContentsMargins(14, 0, 14, 0)
        
        self.profile_name_label = QLabel("")
        self.profile_name_label.setStyleSheet(f"color: {ThemeColors.WHITE}; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        
        self.dropdown_icon = QLabel("▼")
        self.dropdown_icon.setStyleSheet(f"color: {ThemeColors.GOLD}; font-size: 10px; border: none; background: transparent;")
        
        btn_layout.addWidget(self.profile_name_label)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.dropdown_icon)
        
        self.main_layout.addWidget(self.main_button)
        
        self.dropdown_container = QFrame()
        self.dropdown_container.setObjectName("ProfileContainer")
        self.dropdown_container.setMaximumHeight(0) 
        
        self.list_layout = QVBoxLayout(self.dropdown_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(2)
        
        self.main_layout.addWidget(self.dropdown_container)
        
        self.animation = QPropertyAnimation(self.dropdown_container, b"maximumHeight")
        self.animation.setDuration(160)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
    def update_state(self, profiles, current_profile, profession=None):
        display_name = current_profile
        if profession and profession != Professions.ALL:
            display_name = f"{current_profile} ({profession})"
        self.profile_name_label.setText(display_name)
        
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        for p in profiles:
            if p == current_profile: continue 
            btn = QPushButton(p)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28) 
            btn.clicked.connect(lambda checked, name=p: self.select_profile(name))
            self.list_layout.addWidget(btn)
        self.dropdown_container.adjustSize()
        if self.is_expanded: self.expand_menu()
             
    def toggle_menu(self):
        if self.is_expanded: self.collapse_menu()
        else: self.expand_menu()
            
    def expand_menu(self):
        self.dropdown_icon.setText("▲") 
        count = self.list_layout.count() 
        if count <= 0:
            self.collapse_menu(); return
        target_h = (count * 30) + 8 
        self.animation.stop()
        self.animation.setStartValue(self.dropdown_container.height())
        self.animation.setEndValue(target_h)
        self.animation.start()
        self.is_expanded = True
    
    def collapse_menu(self):
        if not self.is_expanded: return
        self.dropdown_icon.setText("▼")
        self.animation.setStartValue(self.dropdown_container.height())
        self.animation.setEndValue(0)
        self.animation.start()
        self.is_expanded = False

    def select_profile(self, name):
        self.profile_changed.emit(name)
        self.collapse_menu()


class QuestWidget(QFrame):
    status_changed = Signal(str, int)
    request_load = Signal(str)
    hide_toggled = Signal(str, bool)
    current_selected = None

    def __init__(self, name, data, metadata=None, color_scheme=ColorSchemeMode.CLASSIC, parent=None):
        super().__init__(parent)
        self.quest_name = name
        self.original_index = 0
        self.color_scheme = color_scheme
        self.metadata = metadata or {}
        self.is_locked = False
        self.conflicting_quest = ""
        self.is_hidden = False
        
        self.status = data.get("status", QuestStatus.NOT_STARTED) if isinstance(data, dict) else QuestStatus.NOT_STARTED
        self.timestamp = data.get("timestamp") if isinstance(data, dict) else None
        self.is_hidden = data.get("is_hidden", False) if isinstance(data, dict) else False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3) 
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setTristate(True) 
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setFixedWidth(22) 
        self._update_check_state()
        self.checkbox.stateChanged.connect(self._on_check_change)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.quest_button = QPushButton(name)
        self.quest_button.setObjectName("QuestLabel")
        self.quest_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quest_button.clicked.connect(self._on_click) 
        self.quest_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.quest_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.quest_button.customContextMenuRequested.connect(self._show_context_menu)
        
        text_layout.addWidget(self.quest_button)
        
        self.timestamp_label = QLabel("")
        self.timestamp_label.setObjectName("TimeLabel")
        self.timestamp_label.setVisible(False)
        text_layout.addWidget(self.timestamp_label)
        
        layout.addWidget(self.checkbox)
        layout.addLayout(text_layout)
        layout.addStretch() 
        self._update_style()

    def set_color_scheme(self, scheme):
        self.color_scheme = scheme
        self._update_style()

    def set_locked(self, is_locked, conflicting_quest=""):
        self.is_locked = is_locked
        self.conflicting_quest = conflicting_quest
        self.checkbox.setEnabled(not is_locked)
        self._update_style()

    def refresh_data(self, data, is_locked=False, conflicting_quest=""):
        self.status = data.get("status", QuestStatus.NOT_STARTED)
        self.timestamp = data.get("timestamp")
        self.is_hidden = data.get("is_hidden", False)
        self.is_locked = is_locked
        self.conflicting_quest = conflicting_quest
        self.checkbox.setEnabled(not is_locked)
        
        self._update_check_state()
        self._update_style()
        
        if QuestWidget.current_selected != self:
            self.timestamp_label.setVisible(False)
        elif self.status == QuestStatus.COMPLETED:
            self._set_timestamp_label()
            self.timestamp_label.setVisible(True)

    def _update_check_state(self):
        self.checkbox.blockSignals(True)
        if self.status == QuestStatus.COMPLETED: 
            self.checkbox.setCheckState(Qt.CheckState.Checked) 
        elif self.status == QuestStatus.IN_PROGRESS: 
            self.checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        else: 
            self.checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.checkbox.blockSignals(False)

    def _on_check_change(self, state):
        if self.is_locked:
            self._update_check_state()
            return
            
        if self.status == QuestStatus.NOT_STARTED:
            new_status = QuestStatus.IN_PROGRESS
        elif self.status == QuestStatus.IN_PROGRESS:
            new_status = QuestStatus.COMPLETED
        else:
            new_status = QuestStatus.NOT_STARTED
        
        self.status = new_status
        self._update_style()
        self._update_check_state()
        self.status_changed.emit(self.quest_name, self.status)
        
        if self.status == QuestStatus.COMPLETED:
            self.timestamp = datetime.datetime.now().strftime(AppConfig.DATE_FORMAT)
            self._set_timestamp_label()
            self.timestamp_label.setVisible(True)
        else:
            self.timestamp = None
            self.timestamp_label.setVisible(False) 

    def _set_timestamp_label(self):
        if self.timestamp:
            self.timestamp_label.setText(f"Completed: {self.timestamp}")
        else:
            self.timestamp_label.setText("Completed") 

    def _on_click(self):
        self.request_load.emit(self.quest_name)
        if QuestWidget.current_selected and QuestWidget.current_selected != self:
            QuestWidget.current_selected.timestamp_label.setVisible(False)
        QuestWidget.current_selected = self
        self.timestamp_label.setVisible(self.status == QuestStatus.COMPLETED)
        if self.status == QuestStatus.COMPLETED:
            self._set_timestamp_label()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        wiki_act = menu.addAction("Open Wiki Details")
        wiki_act.triggered.connect(self._on_click)
        menu.addSeparator()
        
        not_started_act = menu.addAction("Mark as Not Started")
        not_started_act.triggered.connect(lambda: self._set_status_direct(QuestStatus.NOT_STARTED))
        
        in_prog_act = menu.addAction("Mark as In Progress")
        in_prog_act.triggered.connect(lambda: self._set_status_direct(QuestStatus.IN_PROGRESS))
        
        comp_act = menu.addAction("Mark as Completed")
        comp_act.triggered.connect(lambda: self._set_status_direct(QuestStatus.COMPLETED))
        
        if self.is_locked:
            comp_act.setEnabled(False)
            in_prog_act.setEnabled(False)
        
        menu.addSeparator()
        hide_act = menu.addAction("Unhide Quest" if self.is_hidden else "Hide Quest")
        hide_act.triggered.connect(self._toggle_hide)
        
        menu.exec(QCursor.pos())

    def _set_status_direct(self, new_status):
        if self.is_locked and new_status != QuestStatus.NOT_STARTED:
            return
        self.status = new_status
        self._update_style()
        self._update_check_state()
        self.status_changed.emit(self.quest_name, self.status)
        if self.status == QuestStatus.COMPLETED:
            self.timestamp = datetime.datetime.now().strftime(AppConfig.DATE_FORMAT)
            self._set_timestamp_label()
            self.timestamp_label.setVisible(True)
        else:
            self.timestamp = None
            self.timestamp_label.setVisible(False)

    def _toggle_hide(self):
        self.is_hidden = not self.is_hidden
        self.hide_toggled.emit(self.quest_name, self.is_hidden)

    def _update_style(self):
        status_colors = ThemeColors.get_status_colors(self.color_scheme)
        in_prog_color = status_colors["in_progress"]
        comp_color = status_colors["completed"]
        in_prog_bg = status_colors["in_progress_bg"]
        comp_bg = status_colors["completed_bg"]
        
        # Locked by mutual exclusion
        if self.is_locked:
            label_text = f"🔒 {self.quest_name} (Locked)"
            self.quest_button.setText(label_text)
            self.quest_button.setToolTip(f"Mutually exclusive with '{self.conflicting_quest}' which is already completed.")
            self.quest_button.setStyleSheet(f"""
                QPushButton#QuestLabel {{
                    background-color: rgba(40, 40, 48, 0.4);
                    color: #666670;
                    border: 1px dashed #444450;
                    border-radius: 16px;
                    text-align: left;
                    padding: 7px 14px;
                    font-style: italic;
                }}
            """)
            return

        self.quest_button.setText(self.quest_name)
        prof_req = self.metadata.get("profession", "") if self.metadata else ""
        tip = f"Profession: {prof_req.title()}" if prof_req else "Available to all professions"
        self.quest_button.setToolTip(tip)

        if self.status == QuestStatus.COMPLETED:
            self.quest_button.setStyleSheet(f"""
                QPushButton#QuestLabel {{
                    background-color: {comp_bg};
                    color: #909095;
                    text-decoration: line-through;
                    border: 1px solid {comp_color};
                    border-radius: 16px;
                    text-align: left;
                    padding: 7px 14px;
                }}
            """)
        elif self.status == QuestStatus.IN_PROGRESS:
            self.quest_button.setStyleSheet(f"""
                QPushButton#QuestLabel {{
                    background-color: {in_prog_bg};
                    color: {in_prog_color};
                    font-style: italic;
                    font-weight: 600;
                    border: 1px solid {in_prog_color};
                    border-radius: 16px;
                    text-align: left;
                    padding: 7px 14px;
                }}
            """)
        else:
            self.quest_button.setStyleSheet("")
