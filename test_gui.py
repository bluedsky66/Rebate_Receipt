import sys
from PyQt6.QtWidgets import QApplication
from us_rebate_receipts.gui import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
print("GUI Initialized Successfully.")
sys.exit(0)
