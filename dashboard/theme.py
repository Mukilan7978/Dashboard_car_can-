from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    surface: str
    surface_alt: str
    accent: str
    accent_soft: str
    accent2: str
    text: str
    muted: str
    faint: str
    red: str
    amber: str
    green: str
    blue: str
    border: str
    shadow: str


def _qss(theme: Theme) -> str:
    return f"""
QWidget {{
    color: {theme.text};
    font-family: "Lato", "DejaVu Sans", sans-serif;
    font-size: 13px;
}}
QMainWindow, QWidget#Root {{
    background-color: {theme.bg};
}}
QFrame#Card {{
    background-color: {theme.surface};
    border: 1px solid {theme.border};
    border-radius: 16px;
}}
QFrame#CardAlt {{
    background-color: {theme.surface_alt};
    border: 1px solid {theme.border};
    border-radius: 14px;
}}
QLabel#CardTitle {{
    color: {theme.muted};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}}
QLabel#CardValue {{
    color: {theme.text};
    font-size: 27px;
    font-weight: 700;
}}
QLabel#CardUnit {{
    color: {theme.muted};
    font-size: 11px;
}}
QLabel#SectionTitle {{
    color: {theme.text};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#Subtle {{
    color: {theme.muted};
    font-size: 12px;
}}
QLabel#Accent {{
    color: {theme.accent};
    font-size: 12px;
    font-weight: 600;
}}
QPushButton {{
    background-color: {theme.surface};
    border: 1px solid {theme.border};
    border-radius: 12px;
    padding: 10px 18px;
    color: {theme.text};
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {theme.accent};
    background-color: {theme.surface_alt};
}}
QPushButton:pressed {{
    background-color: {theme.accent_soft};
}}
QPushButton:checked {{
    background-color: {theme.accent};
    border-color: {theme.accent};
    color: #05080C;
}}
QPushButton:disabled {{
    color: {theme.faint};
    border-color: {theme.surface_alt};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {theme.surface_alt};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {theme.accent};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
    background: {theme.accent};
}}
QPushButton#Primary {{
    background-color: {theme.accent};
    border-color: {theme.accent};
    color: {theme.bg};
}}
QPushButton#Primary:hover {{
    background-color: {theme.accent2};
    border-color: {theme.accent2};
}}
QProgressBar {{
    background-color: {theme.surface_alt};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {theme.accent};
    border-radius: 4px;
}}
QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
    color: {theme.text};
}}
QListWidget::item {{
    background-color: {theme.surface_alt};
    border: 1px solid {theme.border};
    border-radius: 10px;
    padding: 9px 12px;
    margin: 3px 0;
}}
QListWidget::item:selected {{
    background-color: {theme.accent_soft};
    border-color: {theme.accent};
    color: {theme.text};
}}
QLineEdit {{
    background-color: {theme.surface_alt};
    border: 1px solid {theme.border};
    border-radius: 8px;
    padding: 6px 10px;
    color: {theme.text};
}}
QLineEdit:focus {{
    border-color: {theme.accent};
}}
QPlainTextEdit {{
    background-color: #03060A;
    color: {theme.text};
    border: 1px solid {theme.border};
    border-radius: 10px;
    padding: 8px;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 11px;
}}
QScrollBar:vertical {{
    background: {theme.surface};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {theme.border};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


THEMES: dict[str, Theme] = {
    "ECO": Theme(
        name="ECO",
        bg="#040907",
        surface="#0A1410",
        surface_alt="#102019",
        accent="#00C46A",
        accent_soft="#0B3B27",
        accent2="#5BF0A5",
        text="#F2FAF5",
        muted="#8BA79A",
        faint="#4C6258",
        red="#FF3B30",
        amber="#FFB300",
        green="#00D47E",
        blue="#38BDF8",
        border="#1C342A",
        shadow="#020504",
    ),
    "COMFORT": Theme(
        name="COMFORT",
        bg="#04070C",
        surface="#0A111A",
        surface_alt="#111B28",
        accent="#1E7BFF",
        accent_soft="#0C2C55",
        accent2="#67B6FF",
        text="#F4F8FF",
        muted="#8A9CB3",
        faint="#4C5D72",
        red="#FF3B30",
        amber="#FFB300",
        green="#2EE59D",
        blue="#38BDF8",
        border="#1B2A3D",
        shadow="#02040A",
    ),
    "SPORT": Theme(
        name="SPORT",
        bg="#0A0505",
        surface="#160B0B",
        surface_alt="#211010",
        accent="#FF2D2D",
        accent_soft="#4A1010",
        accent2="#FF7A4A",
        text="#FFF5F5",
        muted="#B08C8C",
        faint="#6B4A4A",
        red="#FF453A",
        amber="#FFB300",
        green="#2EE59D",
        blue="#5AB0FF",
        border="#351818",
        shadow="#060202",
    ),
    "SPORT PLUS": Theme(
        name="SPORT PLUS",
        bg="#050505",
        surface="#120A0A",
        surface_alt="#1D0F0B",
        accent="#FF1E1E",
        accent_soft="#520C08",
        accent2="#FFB000",
        text="#FFFFFF",
        muted="#B59A8A",
        faint="#6E5142",
        red="#FF1E1E",
        amber="#FFB000",
        green="#2EE59D",
        blue="#5AB0FF",
        border="#3A170F",
        shadow="#030202",
    ),
}

DEFAULT_THEME = THEMES["COMFORT"]


def get_theme(name: str | None) -> Theme:
    if not name:
        return DEFAULT_THEME
    return THEMES.get(name.upper(), DEFAULT_THEME)


def stylesheet(theme: Theme) -> str:
    return _qss(theme)
