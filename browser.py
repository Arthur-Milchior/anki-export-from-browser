from PyQt5.QtWidgets import QAction

from anki.hooks import addHook
from aqt import mw
from aqt.exporting import ExportDialog
from aqt.qt import QKeySequence

# Adding action to menu


def setupMenu(browser):
    a = QAction("Export selection", browser)
    a.setShortcut(QKeySequence("Ctrl+Shift+E"))
    a.triggered.connect(lambda : ExportDialog(mw, cids=browser.selectedCards()))
    browser.form.menu_Cards.addAction(a)

addHook("browser.setupMenus", setupMenu)
