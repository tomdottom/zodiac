import logging
import sys

import mistune
from PySide2 import QtCore, QtGui, QtWidgets

from .loaders import PageLoader

logger = logging.getLogger(__name__)


class Page(QtWidgets.QTextBrowser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self.click)
        # html = mistune.markdown("Foo")
        # self.set_content(html)

    def set_content(self, html):
        self.setHtml(html)

    def click(self, qurl, *args, **kwargs):
        logger.debug(f"Click: {qurl.url()}")


class Main(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_menu()
        self._create_url_bar()
        self._create_page()
        self._create_status_bar()

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self)
        shortcut.activated.connect(self.foo)

    @QtCore.Slot()
    def foo(self):
        self._addres_line_edit.setFocus()

    def _create_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        exit_action = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("application-exit"),
            "E&xit",
            self,
            shortcut="Ctrl+Q",
            triggered=qApp.quit,
        )
        file_menu.addAction(exit_action)

    def _create_url_bar(self):
        self._tool_bar = QtWidgets.QToolBar()
        self._tool_bar.setMovable(False)
        self.addToolBar(self._tool_bar)
        self._addres_line_edit = QtWidgets.QLineEdit()
        self._addres_line_edit.setClearButtonEnabled(True)
        # self._addres_line_edit.returnPressed.connect(self.load)
        self._tool_bar.addWidget(self._addres_line_edit)

    def _create_page(self):
        self._content = Page()
        self.setCentralWidget(self._content)

    @QtCore.Slot(str)
    def _update_page(self, html):
        logger.debug("Updating page")
        self._content.set_content(html)

    def _create_status_bar(self):
        self._status_bar = QtWidgets.QStatusBar()
        self._status = QtWidgets.QLabel("Foo")
        self._status_bar.addWidget(self._status, 0)
        self.setStatusBar(self._status_bar)

    @QtCore.Slot(str)
    def _update_status(self, status):
        self._status.setText(status)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    page_loader = PageLoader()
    main._addres_line_edit.textChanged.connect(page_loader.set_url)
    main._addres_line_edit.returnPressed.connect(page_loader.load_url)

    page_loader.content.connect(main._update_page)
    page_loader.status_msg.connect(main._update_status)

    main.show()
    sys.exit(app.exec_())
