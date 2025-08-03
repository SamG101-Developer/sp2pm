from PyQt6.QtGui import QFont

from sp2mp.ui import UI

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    sys.excepthook = lambda *args: sys.__excepthook__(*args)

    app = QApplication(sys.argv)
    app.setFont(QFont("Jetbrains Mono", 10))
    ui = UI()
    ui.exec()
    sys.exit(app.exec())
