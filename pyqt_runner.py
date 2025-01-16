import sys
import subprocess
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSlot

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.process = None
        self.driver_process = None

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Web Scraper')

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("Web Scraper")
        layout.addWidget(self.label)

        self.startButton = QPushButton('Start')
        self.startButton.clicked.connect(self.onStartButtonClicked)
        layout.addWidget(self.startButton)

        self.stopButton = QPushButton('Stop')
        self.stopButton.clicked.connect(self.onStopButtonClicked)
        self.stopButton.setEnabled(False)
        layout.addWidget(self.stopButton)

    @pyqtSlot()
    def onStartButtonClicked(self):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.label.setText("Running...")

        # Run task.py in a separate thread
        threading.Thread(target=self.run_task_py).start()

    def run_task_py(self):
        # Activate virtual environment
        activate_cmd = 'env\\bin\\activate'
        if sys.platform == 'win32':
            activate_cmd += ' && '
        else:
            activate_cmd = 'source /Users/owner/Hassan/Freelance-work/env/bin/activate && '

        # Run task.py
        run_script_cmd = f'{activate_cmd} python /Users/owner/Hassan/Freelance-work/task.py'
        self.driver_process = subprocess.Popen(run_script_cmd, shell=True)

    @pyqtSlot()
    def onStopButtonClicked(self):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.label.setText("Stopped")

        # Terminate the task.py process
        if self.driver_process:
            self.driver_process.terminate()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

# pyinstaller --onefile pyqt_runner.py