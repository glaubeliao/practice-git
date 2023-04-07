import sys
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QApplication

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Create widgets
        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.save_button = QPushButton("Save")

        # Connect the button to the save function
        self.save_button.clicked.connect(self.save_data)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_data(self):
        # Get the data from the inputs
        name = self.name_input.text()
        email = self.email_input.text()

        # Write the data to a file
        with open("data.txt", "a") as f:
            f.write(f"Name: {name}, Email: {email}\n")

        # Close the dialog
        self.accept()

if __name__ == "__main__":
    # Set up the application
    app = QApplication(sys.argv)

    # Create the dialog
    dialog = MyDialog()

    # Show the dialog and wait for it to be closed
    dialog.exec_()

    # Clean up the application
    sys.exit(app.exec())
