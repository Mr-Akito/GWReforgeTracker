# ui/style.py
from PySide6.QtGui import QColor, QPainter, QPixmap, QPen, QIcon, QPainterPath, QBrush, QFont
from PySide6.QtCore import Qt, QRect
from config import AppConfig, ThemeColors, ColorSchemeMode

def get_stylesheet(color_scheme=ColorSchemeMode.CLASSIC):
    status_colors = ThemeColors.get_status_colors(color_scheme)
    in_prog_color = status_colors["in_progress"]
    comp_color = status_colors["completed"]
    in_prog_bg = status_colors["in_progress_bg"]
    comp_bg = status_colors["completed_bg"]
    
    return f"""
    QMainWindow {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ThemeColors.DARK_BG_GRADIENT_START}, stop:1 {ThemeColors.DARK_BG_GRADIENT_END});
    }}
    
    QWidget {{
        font-family: "{AppConfig.FONT_FAMILY}";
        font-size: 13px;
        color: {ThemeColors.WHITE};
    }}

    /* --- PANELS --- */
    QFrame#CardPanel {{
        background-color: {ThemeColors.PANEL_BG};
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
    }}
    QFrame#Transparent {{ background: transparent; border: none; }}

    /* --- SCROLLBARS --- */
    QScrollBar:vertical {{
        border: none;
        background: rgba(0, 0, 0, 0.2);
        width: 6px;
        margin: 4px 1px 4px 1px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.25);
        min-height: 24px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {ThemeColors.GOLD};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

    /* --- BUTTONS --- */
    QPushButton {{
        background-color: rgba(255, 255, 255, 0.06);
        color: {ThemeColors.WHITE};
        border-radius: 16px;
        padding: 7px 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {ThemeColors.HOVER_WHITE};
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, 0.12);
    }}
    
    /* PRIMARY SYNC BUTTON */
    QPushButton#PrimaryBtn {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E5C04A, stop:1 {ThemeColors.GOLD});
        color: #111113;
        border: none;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}
    QPushButton#PrimaryBtn:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F7D468, stop:1 #E5C04A);
    }}
    QPushButton#PrimaryBtn:disabled {{
        background-color: rgba(255, 255, 255, 0.05);
        color: {ThemeColors.DARK_GREY};
    }}
    
    /* HEADER BUTTONS (CIRCULAR) */
    QPushButton#HeaderBtn {{
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 17px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    QPushButton#HeaderBtn:hover {{
        background-color: rgba(255, 255, 255, 0.14);
        border: 1px solid {ThemeColors.GOLD};
    }}
    
    /* DANGER BUTTON (Reset/Delete) */
    QPushButton#DangerBtn {{ 
        background-color: rgba(255, 107, 107, 0.12); 
        color: {ThemeColors.RED}; 
        border: 1px solid rgba(255, 107, 107, 0.4); 
        border-radius: 16px;
        padding: 6px 14px;
    }}
    QPushButton#DangerBtn:hover {{
        background-color: rgba(255, 107, 107, 0.25);
        color: #FFA0A0;
        border-color: {ThemeColors.RED};
    }}
    
    /* SMALL TOOL BTN */
    QPushButton#ToolBtn {{
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 4px;
        color: {ThemeColors.WHITE};
    }}
    QPushButton#ToolBtn:hover {{
        border-color: {ThemeColors.GOLD};
        background-color: rgba(255, 255, 255, 0.1);
    }}
    
    /* --- DROPDOWN SELECTOR WIDGETS --- */
    QPushButton#FilterMainBtn, QPushButton#ProfessionMainBtn {{
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        color: {ThemeColors.WHITE};
        text-align: left;
    }}
    QPushButton#FilterMainBtn:hover, QPushButton#ProfessionMainBtn:hover {{
        border-color: {ThemeColors.GOLD};
        background-color: rgba(255, 255, 255, 0.09);
    }}
    
    QFrame#FilterContainer, QFrame#ProfessionContainer, QFrame#ProfileContainer {{
        background-color: #23232A;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-top: none;
        border-bottom-left-radius: 14px;
        border-bottom-right-radius: 14px;
    }}
    QFrame#FilterContainer QPushButton, QFrame#ProfessionContainer QPushButton, QFrame#ProfileContainer QPushButton {{
        background-color: transparent;
        color: #BBB;
        text-align: left;
        padding-left: 10px;
        border-radius: 8px;
        border: none;
        font-size: 12px;
    }}
    QFrame#FilterContainer QPushButton:hover, QFrame#ProfessionContainer QPushButton:hover, QFrame#ProfileContainer QPushButton:hover {{
        background-color: rgba(212, 175, 55, 0.16);
        color: {ThemeColors.GOLD};
    }}
    
    /* --- PROFILE SELECTOR WIDGET --- */
    QPushButton#ProfileMainBtn {{
        background-color: rgba(0, 0, 0, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
    }}
    QPushButton#ProfileMainBtn:hover {{
        border-color: {ThemeColors.GOLD};
        background-color: rgba(0, 0, 0, 0.5);
    }}

    /* --- CHECKBOXES (TRI-STATE) --- */
    QCheckBox {{
        spacing: 12px;
        background: transparent;
    }}
    QCheckBox::indicator {{ 
        width: 18px;
        height: 18px; 
        border: 2px solid #555560; 
        border-radius: 6px; 
        background-color: #1A1A20; 
    }}
    QCheckBox::indicator:hover {{
        border-color: {ThemeColors.WHITE};
        background-color: #24242C;
    }}
    
    /* COMPLETED STATE */
    QCheckBox::indicator:checked {{ 
        background-color: {comp_color}; 
        border-color: {comp_color}; 
    }}
    
    /* IN-PROGRESS STATE (Indeterminate) */
    QCheckBox::indicator:indeterminate {{
        background-color: {in_prog_color};
        border-color: {in_prog_color};
    }}

    /* DISABLED / LOCKED CHECKBOX */
    QCheckBox::indicator:disabled {{
        background-color: #222226;
        border-color: #383840;
    }}

    /* --- INPUTS --- */
    QLineEdit {{
        background-color: rgba(0, 0, 0, 0.35);
        border-radius: 16px;
        padding: 8px 14px;
        color: {ThemeColors.WHITE};
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    QLineEdit:focus {{
        border: 1px solid {ThemeColors.GOLD};
        background-color: rgba(0, 0, 0, 0.45);
    }}
    
    QLineEdit#PillSearchInput {{
        background-color: rgba(0, 0, 0, 0.35);
        border-radius: 16px;
        padding: 0px 14px;
        color: {ThemeColors.WHITE};
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    QLineEdit#PillSearchInput:focus {{
        border: 1px solid {ThemeColors.GOLD};
    }}

    /* --- QUEST PILLS --- */
    QPushButton#QuestLabel {{
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 8px 14px;
        text-align: left;
        border: 1px solid transparent;
        font-size: 13px;
    }}
    QPushButton#QuestLabel:hover {{
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }}

    /* --- TIMESTAMP LABEL --- */
    QLabel#TimeLabel {{
        color: {ThemeColors.GREY};
        font-size: 11px;
        font-style: italic;
        margin-left: 6px;
    }}

    /* --- TABS --- */
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar::tab {{
        background: transparent;
        color: {ThemeColors.GREY};
        padding: 8px 12px;
        font-weight: 600;
        font-size: 13px;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:hover {{
        color: {ThemeColors.WHITE};
    }}
    QTabBar::tab:selected {{
        color: {ThemeColors.GOLD};
        border-bottom: 2px solid {ThemeColors.GOLD};
    }}
    QTabBar::scroller {{ width: 0px; }}

    /* --- HEADERS --- */
    QLabel#H1 {{ font-size: 22px; font-weight: bold; color: {ThemeColors.WHITE}; }}
    QLabel#H2 {{
        font-size: 12px;
        font-weight: 700;
        color: {ThemeColors.GOLD};
        margin-top: 14px;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    QLabel#SubText {{ font-size: 11px; color: {ThemeColors.GREY}; font-weight: 500; }}
    
    /* GLOBAL PROGRESS BAR */
    QProgressBar {{
        background: rgba(0, 0, 0, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06); 
        border-radius: 9px; 
        text-align: center;
        color: #fff;
        font-weight: bold;
        font-size: 11px;
    }}
    
    QProgressBar::chunk {{ 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C89F2A, stop:1 {comp_color}); 
        border-radius: 8px; 
    }}

    /* CAMPAIGN PROGRESS BAR */
    QProgressBar#CampBar {{
        min-height: 6px;
        max-height: 6px;
        border-radius: 3px; 
        border: none;
        background: rgba(255, 255, 255, 0.08);
    }}

    QProgressBar#CampBar::chunk {{
        border-radius: 3px;
        background-color: {comp_color};
    }}
    
    QSplitter::handle {{ background: transparent; }}
    
    /* MENU STYLING */
    QMenu {{
        background-color: #23232A;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 5px;
        color: {ThemeColors.WHITE};
    }}
    QMenu::item {{
        padding: 6px 20px 6px 12px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background-color: rgba(212, 175, 55, 0.2);
        color: {ThemeColors.GOLD};
    }}
    """

def create_custom_icon(shape, color_hex):
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    pen = QPen(QColor(color_hex))
    pen.setWidth(4)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    
    if shape == "search":
        painter.drawEllipse(12, 12, 28, 28)
        painter.drawLine(36, 36, 52, 52)
    elif shape == "info":
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(36)
        font.setFamily(AppConfig.FONT_FAMILY)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "i")
    elif shape == "moon":
        path = QPainterPath()
        path.addEllipse(12, 12, 36, 36)
        cut = QPainterPath()
        cut.addEllipse(22, 6, 36, 36)
        path = path.subtracted(cut)
        painter.fillPath(path, QBrush(QColor(color_hex)))
    elif shape == "sun":
        painter.drawEllipse(20, 20, 24, 24)
        painter.drawLine(32, 8, 32, 16) 
        painter.drawLine(32, 48, 32, 56) 
        painter.drawLine(8, 32, 16, 32) 
        painter.drawLine(48, 32, 56, 32) 
    elif shape == "trash":
        painter.drawRect(20, 24, 24, 30)
        painter.drawLine(16, 20, 48, 20)
        painter.drawLine(28, 16, 36, 16)
    elif shape == "filter":
        path = QPainterPath()
        path.moveTo(10, 14)
        path.lineTo(54, 14)
        path.lineTo(38, 36)
        path.lineTo(38, 52)
        path.lineTo(26, 46)
        path.lineTo(26, 36)
        path.lineTo(10, 14)
        painter.drawPath(path)
    elif shape == "palette":
        painter.drawEllipse(12, 12, 40, 40)
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(20, 22, 6, 6)
        painter.drawEllipse(32, 18, 6, 6)
        painter.drawEllipse(40, 28, 6, 6)
    elif shape == "settings":
        painter.drawEllipse(22, 22, 20, 20)
        for i in range(8):
            painter.drawLine(32, 10, 32, 16)
            painter.rotate(45)
    elif shape == "lock":
        painter.drawRoundedRect(18, 28, 28, 24, 4, 4)
        painter.drawArc(24, 14, 16, 26, 0, 180 * 16)
    elif shape == "user":
        painter.drawEllipse(24, 12, 16, 16)
        path = QPainterPath()
        path.moveTo(14, 52)
        path.quadTo(14, 34, 32, 34)
        path.quadTo(50, 34, 50, 52)
        painter.drawPath(path)
        
    painter.end()
    return QIcon(pixmap)
