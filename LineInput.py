import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize    

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(320, 140))    
        self.setWindowTitle("PyQt Line Edit example (textfield) - pythonprogramminglanguage.com") 

        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Channel1:')
        self.line = QLineEdit(self)

        # Ch1
        self.line.move(85, 20)
        self.line.resize(200, 32)
        self.nameLabel.move(20, 20)


        # Ch2  
        self.line2 = QLineEdit(self)
        self.line2.move(85, 60)
        self.line2.resize(200, 32)
        self.nameLabel.move(20, 20)

        # Print
        pybutton = QPushButton('Print', self)
        pybutton.clicked.connect(self.clickMethod)
        pybutton.resize(200,32)
        pybutton.move(85, 100)        

    def clickMethod(self):
        print('Channel1: ' + self.line.text())
        print('Channel2: ' + self.line2.text())
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #-----------------------------------------
    mainWin = MainWindow()
    mainWin.show()
    #-----------------------------------------
    sys.exit( app.exec_() )
