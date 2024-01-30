# PyPi Packages Import
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QCoreApplication
import sounddevice as sd
import os
import sys
import shutil
import time
import logging

# Local Packages Import
from transcription import AudioRecorder, MessageEvent

# Configure logging
logging.basicConfig(filename=str(os.path.join(os.getenv('APPDATA'), 'TranscriptionApp','main.log')), level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

# Thread Classes
class TimerThread(QThread):
    update_signal = pyqtSignal()

    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.interval)
            self.update_signal.emit()

    def stop(self):
        self.running = False
        self.wait()

class SaveRecordingThread(QThread):
    requestInput = pyqtSignal()

    def __init__(self, recorder, parent=None):
        super().__init__(parent)
        self.recorder = recorder

    def run(self):
        global temp_file_path
        temp_file_path = self.recorder.stop_recording()

        self.requestInput.emit()


# Core Classes
class ListWidget(QtWidgets.QListWidget):
    def __init__(self, main_ui, parent=None):
        super().__init__(parent)
        self.main_ui = main_ui

    def contextMenuEvent(self, event):
        contextMenu = QtWidgets.QMenu(self)
        deleteAction = contextMenu.addAction("Delete")
        renameAction = contextMenu.addAction("Rename")

        action = contextMenu.exec(self.mapToGlobal(event.pos()))
        if action:
            selected_item = self.itemAt(event.pos())

            if selected_item:
                if action == deleteAction:
                    handler.remove_recording(selected_item.text())
                elif action == renameAction:
                    text, ok = QInputDialog.getText(None, "Rename Recording", "Enter the new name of the recording:")
                    if not ok or not text:
                        return

                    os.rename(os.path.join(handler.data_folder, f"{selected_item.text()}.wav"), os.path.join(handler.data_folder, f"{text}.wav"))
                    os.rename(os.path.join(handler.data_folder, f"{selected_item.text()}.txt"), os.path.join(handler.data_folder, f"{text}.txt"))

                    handler.populate_recordings()

class Ui_MainWindow(object):
    def __init__(self):
        self.timeLabel = QtWidgets.QLabel("00:00")
        self.assets_folder = os.path.join(os.getenv('APPDATA'), 'TranscriptionApp', 'Assets')

    def setupUi(self, MainWindow):
        # Main Window Setup
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 876)
        MainWindow.setMinimumSize(QtCore.QSize(800, 0))

        # Central Widget Setup
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Main Vertical Layout
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        # Horizontal Layout for List and Text Browser
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Vertical Layout for List Widget
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        # Grid Layout for Import Button and Microphone Selection
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        # Import Button Setup
        self.import_2 = QtWidgets.QPushButton(parent=self.centralwidget)
        self.configureButton(self.import_2, "font: 10pt \"Segoe UI\";",QtGui.QIcon(os.path.join(self.assets_folder, 'plus.png')) , QtCore.QSize(11, 11), "Import", handler.open_file_dialog)
        self.gridLayout.addWidget(self.import_2, 0, 0, 1, 1)

        # Microphone Selection Dropdown Setup
        self.MicSelect = QtWidgets.QComboBox(parent=self.centralwidget)
        self.MicSelect.setObjectName("MicSelect")
        handler.populate_mic_select()
        self.MicSelect.currentTextChanged.connect(handler.on_mic_select_changed)
        self.MicSelect.setMaximumSize(QtCore.QSize(150, 16777215))
        self.gridLayout.addWidget(self.MicSelect, 0, 1, 1, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        # List Widget for Recordings
        self.recordings = ListWidget(self, self.centralwidget)
        self.recordings.setMaximumSize(QtCore.QSize(385, 16777215))
        self.recordings.setObjectName("recordings")
        handler.populate_recordings()
        self.verticalLayout.addWidget(self.recordings)

        self.horizontalLayout.addLayout(self.verticalLayout)

        # Setup for the tab widget
        self.tabWidget = QtWidgets.QTabWidget(parent=self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")

        # Tab 1: Transcription
        self.tabTranscription = QtWidgets.QWidget()
        self.tabTranscription.setObjectName("tabTranscription")
        self.textBrowserTranscript = QtWidgets.QTextBrowser(parent=self.tabTranscription)
        self.textBrowserTranscript.setGeometry(QtCore.QRect(10, 10, 381, 671))  # Adjust as needed
        self.tabTranscription.layout = QtWidgets.QVBoxLayout(self.tabTranscription)
        self.tabTranscription.layout.addWidget(self.textBrowserTranscript)
        self.tabWidget.addTab(self.tabTranscription, "Transcription")

        # Tab 2: Keynotes
        self.tabKeynotes = QtWidgets.QWidget()
        self.tabKeynotes.setObjectName("tabKeynotes")
        self.textBrowserKeynotes = QtWidgets.QTextBrowser(parent=self.tabKeynotes)
        self.textBrowserKeynotes.setGeometry(QtCore.QRect(10, 10, 381, 671))  # Adjust geometry as needed
        self.tabKeynotes.layout = QtWidgets.QVBoxLayout(self.tabKeynotes)
        self.tabKeynotes.layout.addWidget(self.textBrowserKeynotes)
        self.tabWidget.addTab(self.tabKeynotes, "Keynotes")

        # Tab 3: Protocol
        self.tabProtocol = QtWidgets.QWidget()
        self.tabProtocol.setObjectName("tabProtocol")
        self.textBrowserProtocol = QtWidgets.QTextBrowser(parent=self.tabProtocol)
        self.textBrowserProtocol.setGeometry(QtCore.QRect(10, 10, 381, 671))  # Adjust geometry as needed
        self.tabProtocol.layout = QtWidgets.QVBoxLayout(self.tabProtocol)
        self.tabProtocol.layout.addWidget(self.textBrowserProtocol)
        self.tabWidget.addTab(self.tabProtocol, "Protocol")

        self.horizontalLayout.addWidget(self.tabWidget)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        # Grid Layout for Start, Pause, and Time Label
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")

        # Start Recording Button Setup
        self.Start = QtWidgets.QPushButton(parent=self.centralwidget)
        self.configureButton(self.Start, "", QtGui.QIcon(os.path.join(self.assets_folder, 'spielen.png')), None, "", lambda: handler.start_recording())
        self.gridLayout_2.addWidget(self.Start, 0, 1, 1, 1)

        # Pause Recording Button Setup
        self.Pause = QtWidgets.QPushButton(parent=self.centralwidget)
        self.configureButton(self.Pause, "", QtGui.QIcon(os.path.join(self.assets_folder, 'pause.png')), None, "", handler._save_recording)
        self.gridLayout_2.addWidget(self.Pause, 0, 3, 1, 1)

        # Time Label Setup
        self.timeLabel = QtWidgets.QLabel("00:00")
        self.configureLabel(self.timeLabel, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.gridLayout_2.addWidget(self.timeLabel, 0, 2, 1, 1)

        # Adding Spacers for Grid Layout
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 0, 4, 1, 1)

        self.verticalLayout_2.addLayout(self.gridLayout_2)

        # Setting Central Widget
        MainWindow.setCentralWidget(self.centralwidget)

        # Menu Bar Setup
        self.setupMenuBar(MainWindow)

        # Status Bar Setup
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def configureButton(self, button, style, icon, iconSize, text, clickEvent):
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(button.sizePolicy().hasHeightForWidth())
        button.setSizePolicy(sizePolicy)
        button.setStyleSheet(style)
        button.setIcon(icon)

        if iconSize:
            button.setIconSize(iconSize)
        button.setText(text)
        button.clicked.connect(clickEvent)

    def configureLabel(self, label, alignment):
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
        label.setSizePolicy(sizePolicy)
        label.setAlignment(alignment)

    def setupMenuBar(self, MainWindow):
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")

        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuWindow = QtWidgets.QMenu(parent=self.menubar)
        self.menuWindow.setObjectName("menuWindow")
        self.menuHelp = QtWidgets.QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")

        MainWindow.setMenuBar(self.menubar)

        self.actionNew = QtGui.QAction(parent=MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionNew.triggered.connect(handler.open_file_dialog)

        self.actionRefresh = QtGui.QAction(parent=MainWindow)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.setText("Refresh")
        self.actionRefresh.triggered.connect(handler.populate_recordings)

        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionRefresh)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuWindow.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.import_2.setText(_translate("MainWindow", "Import"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuWindow.setTitle(_translate("MainWindow", "Window"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionNew.setText(_translate("MainWindow", "New"))


class handler(QObject):
    def __init__(self, ui_instance):
        super().__init__()
        self.ui = ui_instance
        self.recorder = AudioRecorder(self)
        self.mics = sd.query_devices()
        self.Mic = [mic['name'] for mic in self.mics if mic['max_input_channels'] > 0][0]
        self.projects = None
        self.program_folder = os.path.join(os.getenv('APPDATA'), 'TranscriptionApp')
        self.data_folder = os.path.join(self.program_folder, 'DATA')
        self.temp_folder = os.path.join(self.program_folder, 'TEMP')
        self.timer_thread = TimerThread()
        self.timer_thread.update_signal.connect(self.update_timer)
        self.elapsed_time = 0

        try:
            if not os.path.exists(self.program_folder) or os.path.exists(self.data_folder) or os.path.exists(self.temp_folder):
                os.makedirs(self.program_folder)
                os.makedirs(self.data_folder)
                os.makedirs(self.temp_folder)
        except:
            pass

    def event(self, event):
        if event.type() == MessageEvent.EVENT_TYPE:
            self.show_message(event.message)
            return True
        return super(handler, self).event(event)

    def show_message(self, text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    def start_recording(self):
        # Reinitialize the timer thread for a new recording
        if self.timer_thread.isRunning():
            self.timer_thread.stop()
        self.timer_thread = TimerThread()  # Create a new instance
        self.timer_thread.update_signal.connect(self.update_timer)
        self.elapsed_time = 0
        self.update_timer_display()

        # Start the timer thread
        self.timer_thread.start()

        self.recorder.start_recording(mic_index=[mic['index'] for mic in self.mics if mic['name'] == self.Mic][0], sys_sound_device=[mic['index'] for mic in self.mics if 'Stereo Mix' in mic['name']][0])

    def update_timer(self):
        self.elapsed_time += 1
        self.update_timer_display()

    def update_timer_display(self):
        # Format the elapsed time and update the display
        time_str = f"{self.elapsed_time // 60:02d}:{self.elapsed_time % 60:02d}"
        self.ui.timeLabel.setText(time_str)

    def _save_recording(self):
        self.timer_thread.stop()
        self.save_thread = SaveRecordingThread(self.recorder)
        self.save_thread.requestInput.connect(self.showInputDialog)
        self.save_thread.start()

    def showInputDialog(self):
        text, ok = QInputDialog.getText(None, "Save Recording", "Enter the name of the recording:")
        if not ok or not text:
            return

        project_folder = os.path.join(self.data_folder,text)

        os.mkdir(project_folder) # Create project folder

        self.recorder.transcription_mapping[temp_file_path] = text

        # Reset the elapsed time to zero
        self.elapsed_time = 0
        self.update_timer_display()

    def remove_recording(self, name):
        reply = QtWidgets.QMessageBox.question(
            None,
            'Confirm Delete',
            f"Do you really want to delete this transcription ({name})?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(os.path.join(self.data_folder, name), ignore_errors=False, onerror=None) # Remove Project Folder
            except:
                pass #TODO: add logging

            self.populate_recordings()

            return

    def open_file_dialog(self):
        file_name = QFileDialog.getOpenFileName(
            None,
            "Import File",
            "",
            str("Audio Files (*.mp3 *.wav);;Video Files (*.mp4)")
        )
        if file_name[0] != '':
            try:
                project_name = ' '.join(file_name[0].split('/')[::-1][0].split('.')[0].split())
                project_folder = os.path.join(self.data_folder, project_name)
                project_wav_file = os.path.join(project_folder, file_name[0].split('/')[::-1][0])

                os.mkdir(project_folder)
                shutil.copy2(file_name[0], project_folder)
                self.populate_recordings()
                self.recorder.start_transcribe_file(project_wav_file, True)

            except Exception as e:
                logger.info(e)
                handler.show_message("Error: File could not be copied.")
                os.rmdir(project_folder)

    def populate_mic_select(self):
        # Get the list of available microphones.
        mic_names = list(dict.fromkeys([mic['name'] for mic in self.mics if mic['max_input_channels'] > 0]))

        # Populate the MicSelect dropdown menu with the available microphones.
        self.ui.MicSelect.addItems(mic_names)

    def populate_recordings(self):
        self.projects = list(set([os.path.splitext(filename)[0] for filename in os.listdir(self.data_folder)]))
        self.ui.recordings.clear()
        self.ui.recordings.addItems(self.projects)
        self.ui.recordings.sortItems()

        self.ui.recordings.itemClicked.connect(self.display_text)

    def on_mic_select_changed(self, mic_name):
        self.Mic = mic_name  # Store the selected microphone name in the variable.
        print(self.Mic)

    def display_text(self, item):
        # Get the text of the clicked item.
        project_name = item.text()
        project_folder = os.path.join(self.data_folder,project_name)

        # Construct the path to the .txt file associated with the clicked item.
        transcript_file_path = os.path.join(project_folder, f"{project_name}_transcript.txt")
        keynote_file_path = os.path.join(project_folder, f"{project_name}_keynote.txt")
        protocol_file_path = os.path.join(project_folder, f"{project_name}_protocol.txt")

        # Transcription Text
        try:
            # Try to open and read the file.
            with open(transcript_file_path, 'r') as file:
                text = file.read()

        except FileNotFoundError:
            text = "The corresponding text file could not be found."

        except Exception as e:
            text = f"An error occurred: {str(e)}"

        # Set the text to the textBrowserTranscript.
        self.ui.textBrowserTranscript.setText(text)

        # Keynote Text
        try:
            # Try to open and read the file.
            with open(keynote_file_path, 'r') as file:
                text = file.read()

        except FileNotFoundError:
            text = "The corresponding text file could not be found."

        except Exception as e:
            text = f"An error occurred: {str(e)}"

        # Set the text to the textBrowserTranscript.
        self.ui.textBrowserKeynotes.setText(text)

        # Protocol Text
        try:
            # Try to open and read the file.
            with open(protocol_file_path, 'r') as file:
                text = file.read()

        except FileNotFoundError:
            text = "The corresponding text file could not be found."

        except Exception as e:
            text = f"An error occurred: {str(e)}"

        # Set the text to the textBrowserTranscript.
        self.ui.textBrowserProtocol.setText(text)

    def closeEvent(self, event):
        if self.timer_thread.is_alive():
            self.timer_thread.stop()
        super(handler, self).closeEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    handler = handler(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
