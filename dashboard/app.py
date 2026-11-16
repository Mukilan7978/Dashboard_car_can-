from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from config.settings import APP_NAME, ORG_NAME
from .main_window import MainWindow


def create_application(argv: list[str] | None = None) -> QApplication:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setFont(QFont("Lato", 10))
    return app


def run(
    channel: str = "vcan0",
    interface: str = "socketcan",
    control_socket: Path | str | None = None,
) -> int:
    app = create_application()
    window = MainWindow(
        channel=channel,
        interface=interface,
        control_socket=control_socket or "",
    )
    window.show()
    return app.exec()
