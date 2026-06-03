#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 入口文件
用法: python gui.py
"""

import sys
from pathlib import Path

# Ensure src is in sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
