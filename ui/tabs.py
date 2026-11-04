# ui/tabs.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QScrollArea, QPushButton, QFrame, QDialog
)
from PySide6.QtCore import QTimer, Signal, Qt
from config import AppConfig, ThemeColors, QuestStatus, SECTION_MARKER, FilterMode, Professions, ColorSchemeMode, MUTUALLY_EXCLUSIVE_QUESTS
from .widgets import QuestWidget
from .dialogs import CustomDialog

class CampaignTab(QWidget):
    quest_status_changed = Signal(str, int)
    reset_requested = Signal(str)
    wiki_requested = Signal(str)
    hide_toggled = Signal(str, bool)

    def __init__(self, campaign_name, quest_list, quest_status_data, quest_metadata=None, color_scheme=ColorSchemeMode.CLASSIC, locked_quests=None):
        super().__init__()
        self.campaign_name = campaign_name
        self.quest_widgets = [] 
        self.current_status_data = quest_status_data 
        self.quest_metadata = quest_metadata or {}
        self.sections = []
        self.color_scheme = color_scheme
        self.locked_quests = locked_quests or set()
        
        # State
        self.current_filter_text = ""
        self.current_filter_mode = FilterMode.ALL
        self.current_profession_filter = Professions.ALL
        self.show_hidden = False
        
        self.pending_quests = list(quest_list) if isinstance(quest_list, list) else []
        self.batch_timer = QTimer(self)
        self.batch_timer.setInterval(AppConfig.LAZY_LOAD_INTERVAL_MS)
        self.batch_timer.timeout.connect(self._process_batch)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 5, 0)
        
        header_layout = QHBoxLayout()
        self.percent_label = QLabel("0%", objectName="H1")
        self.update_percent_label_color()
        header_layout.addWidget(self.percent_label)
        header_layout.addWidget(QLabel(f"{campaign_name.upper()}", objectName="SubText"), alignment=Qt.AlignmentFlag.AlignBottom)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.campaign_progress_bar = QProgressBar()
        self.campaign_progress_bar.setObjectName("CampBar")
        self.campaign_progress_bar.setFixedHeight(6)
        self.campaign_progress_bar.setTextVisible(False)
        layout.addWidget(self.campaign_progress_bar)
        layout.addSpacing(12)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        scroll_area.setStyleSheet("background: transparent;")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(4)
        self.content_layout.setContentsMargins(2, 0, 20, 0) 

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
        reset_label = f"Reset All Quests" if campaign_name == "All" else f"Reset {campaign_name}"
        reset_button = QPushButton(reset_label, objectName="DangerBtn")
        reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_button.clicked.connect(self.reset_clicked)
        layout.addWidget(reset_button)
        
        self.batch_timer.start()

    def update_percent_label_color(self):
        colors = ThemeColors.get_status_colors(self.color_scheme)
        self.percent_label.setStyleSheet(f"color: {colors['completed']}; font-size: 26px; font-weight: bold;")

    def set_color_scheme(self, scheme):
        self.color_scheme = scheme
        self.update_percent_label_color()
        colors = ThemeColors.get_status_colors(scheme)
        self.campaign_progress_bar.setStyleSheet(f"""
            QProgressBar#CampBar::chunk {{
                border-radius: 3px;
                background-color: {colors['completed']};
            }}
        """)
        for qw in self.quest_widgets:
            qw.set_color_scheme(scheme)

    def set_locked_quests(self, locked_set):
        self.locked_quests = locked_set or set()
        for qw in self.quest_widgets:
            is_locked = qw.quest_name in self.locked_quests
            conflicting = self._find_conflicting_quest(qw.quest_name) if is_locked else ""
            qw.set_locked(is_locked, conflicting)
        self.update_progress()

    def _find_conflicting_quest(self, quest_name):
        if quest_name in MUTUALLY_EXCLUSIVE_QUESTS:
            for partner in MUTUALLY_EXCLUSIVE_QUESTS[quest_name]:
                val = self.current_status_data.get(partner)
                if val and isinstance(val, dict) and val.get("status") == QuestStatus.COMPLETED:
                    return partner
        return "Mutually Exclusive Quest"

    def stop_loading(self):
        if self.batch_timer.isActive():
            self.batch_timer.stop()

    def _process_batch(self):
        if not self.pending_quests:
            self.batch_timer.stop()
            self.update_progress() 
            self.apply_filters()
            return

        self.content_widget.setUpdatesEnabled(False)
        
        count = 0
        while self.pending_quests and count < AppConfig.LAZY_LOAD_BATCH_SIZE:
            item = self.pending_quests.pop(0)
            if SECTION_MARKER in item:
                header_lbl = QLabel(item.replace(SECTION_MARKER, "").strip(), objectName="H2")
                header_lbl.setParent(self.content_widget)
                self.content_layout.addWidget(header_lbl)
                self.sections.append({"header": header_lbl, "quests": []})
            else:
                qw = self._add_quest(item)
                if self.sections:
                    self.sections[-1]["quests"].append(qw)
            count += 1
            
        self.content_widget.setUpdatesEnabled(True)
            
        if self.pending_quests:
            self.update_progress()
        else:
            self.apply_filters()

    def _parse_status(self, quest_name):
        val = self.current_status_data.get(quest_name)
        if val is None or not isinstance(val, dict):
            return {"status": QuestStatus.NOT_STARTED, "timestamp": None, "is_hidden": False}
        return val

    def _matches_profession(self, quest_name):
        if self.current_profession_filter == Professions.ALL:
            return True
        meta = self.quest_metadata.get(quest_name, {})
        req = meta.get("profession", "").lower()
        if not req:
            return True # Available to all
        prof_term = self.current_profession_filter.lower()
        return prof_term in req

    def get_progress_stats(self):
        completed = 0
        total = 0
        
        # Count loaded widgets
        for qw in self.quest_widgets:
            if not self._matches_profession(qw.quest_name):
                continue
            if qw.is_hidden and not self.show_hidden:
                continue
            # If mutually exclusive and locked, exclude from total available
            if qw.is_locked:
                continue
            total += 1
            if qw.status == QuestStatus.COMPLETED: 
                completed += 1
                
        # Count pending quests
        for item in self.pending_quests:
            if SECTION_MARKER in item: continue
            if not self._matches_profession(item):
                continue
            status_data = self._parse_status(item)
            if status_data.get("is_hidden") and not self.show_hidden:
                continue
            if item in self.locked_quests:
                continue
            total += 1
            if status_data.get("status") == QuestStatus.COMPLETED: 
                completed += 1
                
        return completed, total

    def refresh_tab_state(self, current_data, locked_set=None):
        self.current_status_data = current_data
        if locked_set is not None:
            self.locked_quests = locked_set
            
        for quest_widget in self.quest_widgets:
            quest_name = quest_widget.quest_name
            status_data = self._parse_status(quest_name)
            is_locked = quest_name in self.locked_quests
            conflicting = self._find_conflicting_quest(quest_name) if is_locked else ""
            quest_widget.refresh_data(status_data, is_locked=is_locked, conflicting_quest=conflicting)
            
        self.update_progress()
        self.apply_filters()
        
    def _add_quest(self, name):
        status_data = self._parse_status(name)
        meta = self.quest_metadata.get(name, {})
        
        is_locked = name in self.locked_quests
        conflicting = self._find_conflicting_quest(name) if is_locked else ""
        
        quest_widget = QuestWidget(
            name, status_data, metadata=meta,
            color_scheme=self.color_scheme,
            parent=self.content_widget
        )
        quest_widget.original_index = len(self.quest_widgets)
        if is_locked:
            quest_widget.set_locked(True, conflicting)
        
        quest_widget.status_changed.connect(self._on_quest_changed)
        quest_widget.request_load.connect(self.wiki_requested.emit)
        quest_widget.hide_toggled.connect(self._on_hide_toggled)
        
        self.content_layout.addWidget(quest_widget)
        self.quest_widgets.append(quest_widget)
        return quest_widget

    def _on_quest_changed(self, name, status):
        self.quest_status_changed.emit(name, status)
        self.update_progress()
        if self.current_filter_mode != FilterMode.ALL:
            self.apply_filters()

    def _on_hide_toggled(self, name, is_hidden):
        self.hide_toggled.emit(name, is_hidden)
        self.update_progress()
        self.apply_filters()

    def set_filter_mode(self, mode):
        self.current_filter_mode = mode
        self.apply_filters()

    def set_profession_filter(self, prof):
        self.current_profession_filter = prof
        self.apply_filters()
        self.update_progress()

    def set_show_hidden(self, show):
        self.show_hidden = show
        self.apply_filters()
        self.update_progress()

    def filter_content(self, text):
        self.current_filter_text = text.lower().strip()
        self.apply_filters()

    def apply_filters(self):
        self.content_widget.setUpdatesEnabled(False)
        
        mode = self.current_filter_mode
        search = self.current_filter_text
        prof = self.current_profession_filter
        
        for section in self.sections:
            section_has_visible = False
            for qw in section['quests']:
                # 1. Search text match
                text_match = True
                if search:
                    text_match = search in qw.quest_name.lower()
                
                # 2. Status match
                status_match = True
                if mode == FilterMode.NOT_STARTED:
                    status_match = (qw.status == QuestStatus.NOT_STARTED)
                elif mode == FilterMode.IN_PROGRESS:
                    status_match = (qw.status == QuestStatus.IN_PROGRESS)
                elif mode == FilterMode.COMPLETED:
                    status_match = (qw.status == QuestStatus.COMPLETED)
                
                # 3. Profession match
                prof_match = self._matches_profession(qw.quest_name)
                
                # 4. Hidden match
                hide_match = True
                if qw.is_hidden and not self.show_hidden:
                    hide_match = False
                
                is_visible = text_match and status_match and prof_match and hide_match
                qw.setVisible(is_visible)
                
                if is_visible:
                    section_has_visible = True
            
            if section['header']:
                section['header'].setVisible(section_has_visible)
                
        self.content_widget.setUpdatesEnabled(True)

    def reset_clicked(self):
        target = "ALL campaigns" if self.campaign_name == "All" else f"the {self.campaign_name} campaign"
        dlg = CustomDialog("Confirm Reset", f"Are you sure you want to reset all quest progress for {target}?", self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.reset_requested.emit(self.campaign_name)

    def update_progress(self):
        done, total = self.get_progress_stats()
        if total == 0:
            self.percent_label.setText("100%" if done > 0 else "0%")
            self.campaign_progress_bar.setMaximum(1)
            self.campaign_progress_bar.setValue(1 if done > 0 else 0)
            return
        percent = int((done / total) * 100)
        self.percent_label.setText(f"{percent}%")
        self.campaign_progress_bar.setMaximum(total)
        self.campaign_progress_bar.setValue(done)
