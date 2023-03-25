#QDialog
from PyQt5.QtWidgets import  QVBoxLayout,QWidget,QApplication ,QHBoxLayout,QDialog,QPushButton,QMainWindow,QGridLayout,QLabel

from PyQt5.QtGui import QIcon,QPixmap,QFont
from PyQt5.QtCore import  Qt

import sys

class WindowClass(QWidget):

    def __init__(self,parent=None):

        super(WindowClass, self).__init__(parent)
        layout=QVBoxLayout()
        self.btn=QPushButton()
        self.btn.setText("To Show the Dialog Window")
        self.btn.clicked.connect(self.showDialog)
        self.resize(500,500)
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def showDialog(self):

         self.dialog=QDialog()
         self.dialog.resize(500,500)
         self.dialog.setWindowTitle("Target Molecular Information")
         self.dialog.exec_()



if __name__=="__main__":
    app=QApplication(sys.argv)
    win=WindowClass()
    win.show()
    sys.exit(app.exec_())
