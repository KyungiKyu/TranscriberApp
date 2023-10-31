# PyPi Packages Import
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QInputDialog
import sounddevice as sd
import os
import sys
import shutil

# Local Packages Import
from transcription import AudioRecorder
class ButtonWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.button1 = QtWidgets.QPushButton('Button 1', self)
        self.button2 = QtWidgets.QPushButton('Button 2', self)
        self.button3 = QtWidgets.QPushButton('Button 3', self)

        self.button1.clicked.connect(lambda: print('Button 1'))
        self.button2.clicked.connect(lambda: print('Button 2'))
        self.button3.clicked.connect(lambda: print('Button 3'))

        self.layout.addWidget(self.button1)
        self.layout.addWidget(self.button2)
        self.layout.addWidget(self.button3)


class HoverListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_widget = ButtonWidget(self)
        self.button_widget.hide()

    def enterEvent(self, event: QtGui.QEnterEvent):  # Ensure the event is of type QEnterEvent
        super().enterEvent(event)  # Call the base class implementation
        item = self.itemAt(self.mapFromGlobal(QtGui.QCursor.pos()))  # Get the item at the cursor position
        if item:
            rect = self.visualItemRect(item)
            self.button_widget.move(rect.right(), rect.top())
            self.button_widget.show()

    def leaveEvent(self, event: QtCore.QEvent):  # Ensure the event is of type QEvent
        super().leaveEvent(event)  # Call the base class implementation
        self.button_widget.hide()



class Ui_MainWindow(object):
    def __init__(self):
        self.recorder = AudioRecorder()
        self.mics = sd.query_devices()
        self.Mic = [mic['name'] for mic in self.mics if mic['max_input_channels'] > 0][0]
        self.Language = 'de-DE'
        self.DATA = os.getcwd()+"\\DATA\\"
        self.projects = None

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 876)
        MainWindow.setMinimumSize(QtCore.QSize(800, 0))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.import_2 = QtWidgets.QPushButton(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.import_2.sizePolicy().hasHeightForWidth())
        self.import_2.setSizePolicy(sizePolicy)
        self.import_2.setStyleSheet("font: 10pt \"Segoe UI\";")
        self.import_2.setIcon(QtGui.QIcon("Assets/plus.png"))
        self.import_2.setIconSize(QtCore.QSize(11, 11))
        self.import_2.setObjectName("import_2")
        self.import_2.clicked.connect(self.open_file_dialog)
        self.gridLayout.addWidget(self.import_2, 0, 0, 1, 1)
        self.MicSelect = QtWidgets.QComboBox(parent=self.centralwidget)
        self.MicSelect.setObjectName("MicSelect")
        self.populate_mic_select()
        self.MicSelect.currentTextChanged.connect(self.on_mic_select_changed)
        self.MicSelect.setMaximumSize(QtCore.QSize(150, 16777215))
        self.gridLayout.addWidget(self.MicSelect, 0, 1, 1, 1)
        self.LanguageSelect = QtWidgets.QComboBox(parent=self.centralwidget)
        self.LanguageSelect.setMaximumSize(QtCore.QSize(150, 16777215))
        self.LanguageSelect.setObjectName("LanguageSelect")
        self.gridLayout.addWidget(self.LanguageSelect, 0, 2, 1, 1)
        self.populate_language_select()
        self.LanguageSelect.currentTextChanged.connect(self.on_language_select_changed)
        self.verticalLayout.addLayout(self.gridLayout)
        self.recordings = HoverListWidget(self.centralwidget)  # Replace your existing QListWidget with HoverListWidget
        self.recordings.setMaximumSize(QtCore.QSize(385, 16777215))
        self.recordings.setObjectName("recordings")
        self.populate_recordings()
        self.verticalLayout.addWidget(self.recordings)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.textBrowser = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.textBrowser.setObjectName("textBrowser")
        self.horizontalLayout.addWidget(self.textBrowser)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.Start = QtWidgets.QPushButton(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Start.sizePolicy().hasHeightForWidth())
        self.Start.setSizePolicy(sizePolicy)
        self.Start.setText("")
        self.Start.setIcon(QtGui.QIcon("./Assets/spielen.png"))
        self.Start.setObjectName("Start")
        self.Start.clicked.connect(lambda: self.recorder.start_recording(mic_index=[mic['index'] for mic in self.mics if mic['name'] == self.Mic][0],language=self.Language))
        self.gridLayout_2.addWidget(self.Start, 0, 1, 1, 1)
        self.Pause = QtWidgets.QPushButton(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Pause.sizePolicy().hasHeightForWidth())
        self.Pause.setSizePolicy(sizePolicy)
        self.Pause.setText("")
        self.Pause.setIcon(QtGui.QIcon("J:/50__EDV/69__Development/TranscriptionAI/01__Development/v0.1_dev/Assets/pause.png"))
        self.Pause.setObjectName("Pause")
        self.Pause.clicked.connect(self.save_recording)
        self.gridLayout_2.addWidget(self.Pause, 0, 3, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 0, 4, 1, 1)
        self.timeEdit = QtWidgets.QTimeEdit(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timeEdit.sizePolicy().hasHeightForWidth())
        self.timeEdit.setSizePolicy(sizePolicy)
        self.timeEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.timeEdit.setReadOnly(True)
        self.timeEdit.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.timeEdit.setCurrentSection(QtWidgets.QDateTimeEdit.Section.MinuteSection)
        self.timeEdit.setObjectName("timeEdit")
        self.gridLayout_2.addWidget(self.timeEdit, 0, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
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
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew = QtGui.QAction(parent=MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.menuFile.addAction(self.actionNew)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuWindow.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.import_2.setText(_translate("MainWindow", "Import"))
        self.timeEdit.setDisplayFormat(_translate("MainWindow", "mm:ss"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuWindow.setTitle(_translate("MainWindow", "Window"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionNew.setText(_translate("MainWindow", "New"))

    def open_file_dialog(self):
        file_name= QFileDialog.getOpenFileName(
            None,
            "Import File",
            "",
            str("Audio Files (*.mp3 *.wav);;Video Files (*.mp4)")
        )
        if file_name:
            shutil.copy2(file_name[0],os.getcwd().replace('\\','/')+"/DATA")
            self.populate_recordings()

            self.recorder.start_transcribe_file(self.DATA+file_name[0].split('/')[::-1][0])

    def populate_mic_select(self):
        # Get the list of available microphones.
        mic_names = [mic['name'] for mic in self.mics if mic['max_input_channels'] > 0]

        # Populate the MicSelect dropdown menu with the available microphones.
        self.MicSelect.addItems(mic_names)

    def populate_language_select(self):
        languages = {
            'Deutsch': 'de-DE',
            'Englisch': 'en-US',
            'Französisch': 'fr-FR',
        }

        for lang, tag in languages.items():
            self.LanguageSelect.addItem(lang, tag)

    def populate_recordings(self):
        self.projects = list(set([os.path.splitext(filename)[0] for filename in os.listdir(self.DATA)]))

        self.recordings.clear()
        self.recordings.addItems(self.projects)
        self.recordings.sortItems()

        self.recordings.itemClicked.connect(self.display_text)

    def on_mic_select_changed(self, mic_name):
        self.Mic = mic_name  # Store the selected microphone name in the variable.
        print(self.Mic)

    def on_language_select_changed(self, language_name):
        index = self.LanguageSelect.currentIndex()
        self.Language = self.LanguageSelect.itemData(index)  # Store the BCP-47 tag of the selected language in the variable.

    def save_recording(self):
        text, ok = QInputDialog.getText(None, "Save Recording", "Enter the name of the recording:")
        if not ok or not text:  # Check if 'Cancel' is clicked or if no text is entered.
            return  # Abort and return immediately if 'Cancel' is clicked.

        save_path = os.path.join(self.DATA, f"{text}.wav")
        self.recorder.stop_recording(save_path)
        self.populate_recordings()

    def display_text(self, item):
        # Get the text of the clicked item.
        project_name = item.text()

        # Construct the path to the .txt file associated with the clicked item.
        file_path = os.path.join(self.DATA, f"{project_name}.txt")

        try:
            # Try to open and read the file.
            with open(file_path, 'r') as file:
                text = file.read()

        except FileNotFoundError:
            text = "The corresponding text file could not be found."

        except Exception as e:
            text = f"An error occurred: {str(e)}"

        # Set the text to the textBrowser.
        self.textBrowser.setText(text)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
