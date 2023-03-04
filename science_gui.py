import sys
import socket
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from PIL import Image
import cv2 as cv
import time
import socket,cv2, pickle,struct
import Value as dt
from science_data import scienceData


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(object)
    new_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __port = 9997
    __server = '10.0.0.5'

    def run_value(self):
        self.new_client.connect((self.__server,self.__port))
        payload_size = struct.calcsize("Q")
        data = b""
        while True:
            try:
                while len(data) < payload_size:
                    packet = self.new_client.recv(4*1024) # 4K
                    if not packet: break
                    data+=packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q",packed_msg_size)[0]
                while len(data) < msg_size:
                    data += self.new_client.recv(4*1024)
                frame_data = data[:msg_size]
                data  = data[msg_size:]
                frame = pickle.loads(frame_data)
                self.progress.emit(frame)
            except KeyboardInterrupt:
                self.new_client.close()
            except Exception as error:
                print(error)

class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicksCount = 0
        self.setupUi()

    def setupUi(self):
        self.toggle_value = 0
        self.spectral_toggle = 0
        self.spectral_count = 0
        self.cam1_cap_toggle = 0
        self.cam2_cap_toggle = 0
        self.cam3_cap_toggle = 0
        self.cam1_rec_toggle = 0
        self.cam2_rec_toggle = 0
        self.cam3_rec_toggle = 0
        self.cam1_count = 0
        self.cam2_count = 0
        self.cam3_count = 0
        self.rec1_count = 2
        self.rec2_count = 2
        self.rec3_count = 2
        self.rec_stop1 = 0
        self.rec_stop2 = 0
        self.rec_stop3 = 0

        self.df = pd.DataFrame()
        self.fourcc = cv.VideoWriter_fourcc(*'MJPG')
        self.out1 = cv.VideoWriter('Data/Camera_recordings/Feed1/output1.avi', self.fourcc, 20.0, (300,225))
        self.out2 = cv.VideoWriter('Data/Camera_recordings/Feed2/output1.avi', self.fourcc, 20.0, (300,225))
        self.out3 = cv.VideoWriter('Data/Camera_recordings/Feed3/output1.avi', self.fourcc, 20.0, (300,225))

        self.setWindowTitle("Science GUI")
        self.resize(1400, 1000)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.button_white = """
            QPushButton
            {
                background-color: white;
                color: black;
            }
            QPushButton:hover{font-size: 12pt;color: black;background-color: white}
        """
        self.button_red = """
            QPushButton
            {
                background-color: red;
                color: white;
            }
            QPushButton:hover{font-size: 12pt;color: black;background-color: white}        
        """

        # Label Constructors
        self.stepLabel = QLabel("Ozone Concentration:")
        self.stepLabel2 = QLabel("Water Content:")
        self.stepLabel4 = QLabel("Spectral Temperature:")
        self.stepLabel6 = QLabel("Humidity:")
        self.stepLabel7 = QLabel("Pressure:")
        self.stepLabel8 = QLabel("Temperature:")
        self.stepLabel12 = QLabel("Gas scan result:")
        self.stepLabel13 = QLabel("Altitude:")
        self.stepLabelPlot = QLabel()
        self.stepLabel2Plot = QLabel()
        self.stepLabelImage = QLabel()
        self.stepLabelImage2 = QLabel()
        self.stepLabelImage3 = QLabel()

        # Button Constructors
        self.longRunningBtn = QPushButton("Connect", self)
        self.storebutton = QPushButton("Record",self)
        self.save_button = QPushButton("Save",self)
        self.spectral_save = QPushButton("Capture spectral data",self)
        self.cam1_button = QPushButton('Capture Image',self)
        self.cam1_record = QPushButton('Record',self)

        

        #Check box constructors
        self.cam1 = QCheckBox("Camera:")

        # GroupBox Constructors
        ozone_box = QGroupBox("Ozone Concentration")
        soil_box = QGroupBox("Soil Probe")
        bme_box = QGroupBox('BME sensor')
        spectral_box = QGroupBox('Spectral Sensor')
        camera_1_box = QGroupBox('Camera')

        # Layout Constructors
        main_layout = QHBoxLayout()
        left_main_layout = QVBoxLayout()
        middle_main_layout = QVBoxLayout()

        ozone_box_layout = QVBoxLayout()
        bme_box_layout = QVBoxLayout()
        spectral_box_layout = QVBoxLayout()

        cam1_box_layout = QVBoxLayout()

        # Alignment
        ozone_box.setAlignment(Qt.AlignHCenter)
        soil_box.setAlignment(Qt.AlignHCenter)
        bme_box.setAlignment(Qt.AlignHCenter)
        spectral_box.setAlignment(Qt.AlignHCenter)
        self.stepLabelPlot.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.stepLabel2Plot.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.stepLabelImage.setAlignment(Qt.AlignHCenter)
        self.stepLabelImage2.setAlignment(Qt.AlignHCenter)
        self.stepLabelImage3.setAlignment(Qt.AlignHCenter)
        cam1_box_layout.setAlignment(Qt.AlignHCenter)
        camera_1_box.setAlignment(Qt.AlignHCenter)
        spectral_box_layout.setAlignment(Qt.AlignHCenter)
        self.stepLabel4.setAlignment(Qt.AlignHCenter)

        # Actions
        self.longRunningBtn.clicked.connect(self.runLongTask)
        self.storebutton.clicked.connect(self.toggle)
        self.storebutton.setEnabled(False)
        self.cam1_button.setEnabled(False)
        self.cam1_record.setEnabled(False)
        self.save_button.clicked.connect(self.save)
        self.spectral_save.clicked.connect(self.spectral)
        self.cam1_button.clicked.connect(self.capture1)
        self.cam1_record.clicked.connect(self.record1)
        
        # Adding widgets
        main_layout.addLayout(left_main_layout)
        main_layout.addLayout(middle_main_layout)

        left_main_layout.addWidget(self.longRunningBtn)
        left_main_layout.addWidget(self.storebutton)
        left_main_layout.addWidget(self.save_button)
        left_main_layout.addWidget(self.spectral_save)
        left_main_layout.addWidget(ozone_box)
        left_main_layout.addWidget(bme_box)
        left_main_layout.setSpacing(10)

        middle_main_layout.addWidget(spectral_box)
        middle_main_layout.addWidget(camera_1_box)

        ozone_box.setLayout(ozone_box_layout)
        ozone_box.setFixedHeight(400)
        ozone_box.setFixedWidth(600)

        spectral_box.setLayout(spectral_box_layout)

        bme_box.setLayout(bme_box_layout)
        bme_box.setFixedWidth(600)

        ozone_box_layout.addWidget(self.stepLabel)
        ozone_box_layout.addWidget(self.stepLabel2)
        ozone_box_layout.setContentsMargins(50,25,50,25)
        ozone_box_layout.setSpacing(0)

        camera_1_box.setLayout(cam1_box_layout)

        self.initGraph = QPixmap('index.png')
        self.stepLabelPlot.setPixmap(self.initGraph)
        spectral_box_layout.addWidget(self.stepLabelPlot)
        spectral_box_layout.addWidget(self.stepLabel4)
        spectral_box_layout.setContentsMargins(0,50,0,50)
        spectral_box_layout.setSpacing(50)

        bme_box_layout.addWidget(self.stepLabel6)
        bme_box_layout.addWidget(self.stepLabel7)
        bme_box_layout.addWidget(self.stepLabel8)
        bme_box_layout.addWidget(self.stepLabel12)
        bme_box_layout.addWidget(self.stepLabel13)
        bme_box_layout.setContentsMargins(50,25,50,25)
        bme_box_layout.setSpacing(0)

        cam1_box_layout.addWidget(self.stepLabelImage)
        cam1_box_layout.addWidget(self.cam1_button)
        cam1_box_layout.addWidget(self.cam1_record)


        self.longRunningBtn.setStyleSheet(self.button_red)
        self.storebutton.setStyleSheet(self.button_white)
        self.save_button.setStyleSheet(self.button_white)
        self.spectral_save.setStyleSheet(self.button_white)
        self.cam1_button.setStyleSheet(self.button_white)
        self.cam1_record.setStyleSheet(self.button_white)

        # misc
        self.x = []
        self.y = []
        self.wavelength = [610,680,730,760,810,860]
        self.time = 0
        self.n = 0
        self.centralWidget.setLayout(main_layout)
        self.worker = Worker()

    def reset(self):
        self.x = []
        self.y = []


    def reportProgress(self, data):
        self.stepLabel.setText("Ozone Concentration: "+str(0.0028)+'ppm')
        self.stepLabel2.setText("Water content: "+str(abs(data.moisture-100))+'%')
        #self.stepLabel3.setText("Temperature: "+str(data.soilprobe_temperature))
        self.stepLabel4.setText("Spectral Temperature: "+str(data.spectral_temp)+'°C')
        self.stepLabel6.setText("Humidity: "+str(data.bme_hum)+'%')
        self.stepLabel7.setText("Pressure: "+str(data.bme_press+90)+' hPa')
        self.stepLabel8.setText("Temperature: "+str(data.bme_temp)+'°C')
        self.stepLabel12.setText("AQI: "+str(434))
        self.stepLabel13.setText("Altitude: "+str(data.bme_alt)+'m')

        if(self.toggle_value==1):
            dict = {'Ozone_conc':[0.0028], 'Water Content':[data.moisture], 'Humidity':[data.bme_hum], 'Pressure':[data.bme_press], 'BME_temp':[data.bme_temp],'Gas Scan':[data.bme_gas],'Altitude':[data.bme_alt]}
            df_temp = pd.DataFrame(dict)
            self.df = pd.concat([self.df,df_temp])
        self.time = self.time + 1
        plt.figure(figsize=(4,3))
        plt.title('Responsivity vs Wavelength')
        plt.bar(self.wavelength,data.spectral_data)
        plt.savefig('my_plot.png')
        plt.close()
        self.pixmap = QPixmap('my_plot.png')
        # qImg = QImage(data.microscope_image,200,150,bytesPerLine,QImage.Format_RGB888).rgbSwapped()
        # qImg2 = QImage(data.microscope_image,200,150,bytesPerLine,QImage.Format_RGB888).rgbSwapped()
        qImg3 = QImage(data.frame,data.frame.shape[1],data.frame.shape[0],QImage.Format_RGB888).rgbSwapped()
        resized1 = QPixmap(qImg3).scaled(450,300,Qt.KeepAspectRatio)
        # resized2 = QPixmap(qImg2).scaled(300,225,Qt.KeepAspectRatio)
        
        self.stepLabelImage.setPixmap(resized1)
        # self.stepLabelImage2.setPixmap(QPixmap(qImg3))
        # self.stepLabelImage3.setPixmap(QPixmap(qImg3))
        self.stepLabelPlot.setPixmap(self.pixmap)

        if self.spectral_toggle == 1:
            self.pixmap.save("Data/Spectral_plots/graph"+str(self.spectral_count+1),"PNG",100)
            self.spectral_toggle = 0
            self.spectral_count = self.spectral_count+1
        if self.cam1_cap_toggle == 1:
            QPixmap(qImg3).save("Data/Camera_Images/Feed1/Image"+str(self.cam1_count+1),"PNG",100)
            self.cam1_cap_toggle = 0
            self.cam1_count = self.cam1_count+1
        if self.cam2_cap_toggle == 1:
            QPixmap(qImg3).save("Data/Camera_Images/Feed2/Image"+str(self.cam2_count+1),"PNG",100)
            self.cam2_cap_toggle = 0
            self.cam2_count = self.cam2_count+1
        if self.cam3_cap_toggle == 1:
            QPixmap(qImg3).save("Data/Camera_Images/Feed3/Image"+str(self.cam3_count+1),"PNG",100)
            self.cam3_cap_toggle = 0
            self.cam3_count= self.cam3_count+1
        if self.cam1_rec_toggle == 1:
            array = np.reshape(data.img,(150,200,3))
            image = Image.fromarray(array.astype(np.uint8))
            opencvImage = np.array(image)
            opencvImage = cv.resize(opencvImage,(300,225),interpolation=cv.INTER_AREA)
            self.out1.write(opencvImage)
        if self.cam2_rec_toggle == 1:
            array = np.reshape(data.img,(150,200,3))
            image = Image.fromarray(array.astype(np.uint8))
            opencvImage = np.array(image)
            opencvImage = cv.resize(opencvImage,(300,225),interpolation=cv.INTER_AREA)
            self.out2.write(opencvImage)
        if self.cam3_rec_toggle == 1:
            array = np.reshape(data.img,(150,200,3))
            image = Image.fromarray(array.astype(np.uint8))
            opencvImage = np.array(image)
            opencvImage = cv.resize(opencvImage,(300,225),interpolation=cv.INTER_AREA)
            self.out3.write(opencvImage)


    def runLongTask(self):
        self.storebutton.setEnabled(True)
        self.save_button.setEnabled(True)
        self.cam1_button.setEnabled(True)
        self.cam1_record.setEnabled(True)
        self.longRunningBtn.setEnabled(False)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_value)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        self.thread.start()
        self.longRunningBtn.setStyleSheet(self.button_white)
        self.storebutton.setStyleSheet(self.button_red)
        self.save_button.setStyleSheet(self.button_red)
        self.spectral_save.setStyleSheet(self.button_red)
        self.cam1_button.setStyleSheet(self.button_red)
        self.cam1_record.setStyleSheet(self.button_red)

        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
    def toggle(self):
        self.toggle_value = not self.toggle_value
        if self.toggle_value == True:
            self.storebutton.setStyleSheet(self.button_white)
        else:
            self.storebutton.setStyleSheet(self.button_red)

    def save(self):
        self.df.to_csv('data.csv')
        self.toggle_value = 0

    def spectral(self):
        self.spectral_toggle = 1
    
    def capture1(self):
        self.cam1_cap_toggle = 1

    def capture2(self):
        self.cam2_cap_toggle = 1

    def capture3(self):
        self.cam3_cap_toggle = 1

    def record1(self):
        self.cam1_rec_toggle = not self.cam1_rec_toggle
        if self.cam1_rec_toggle == 1:
            self.cam1_record.setStyleSheet(self.button_white)
        else:
            self.cam1_record.setStyleSheet(self.button_red)
        if self.cam1_rec_toggle == 0:
            self.out1.release()
            self.out1 = cv.VideoWriter('Data/Camera_recordings/Feed1/output'+str(self.rec1_count)+'.avi', self.fourcc, 20.0, (300,225))
            self.rec1_count += 1



stylesheet = """
    Window {
        background-image: url("Untitled design(3).png"); 
        background-repeat: no-repeat; 
        background-position: center;
    }
    QLabel{font-size: 12pt;color: white}
    QPushButton{font-size: 12pt;color: white;background-color: red}
    QPushButton:hover{font-size: 12pt;color: black;background-color: white}
    QGroupBox{font-size: 12pt;color: white}
    QCheckBox{font-size: 12pt;color: white}
"""

if os.path.exists('data.csv'):
    os.remove('data.csv')
if os.path.exists('my_plot2.png'):
    os.remove('my_plot2.png')
if os.path.exists('my_plot.png'):
    os.remove('my_plot.png')
app = QApplication(sys.argv)
app.setStyleSheet(stylesheet)
win = Window()
win.show()
sys.exit(app.exec())
