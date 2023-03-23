import sys
sys.path.append("../")
import time
import logging
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import py3lib.QuLogger as Qlogger
import py3lib.FileToArray as fil2a
import QSS017A_Widget as UI
import QSS017A_Action as ACT
import QSS017A_Const as CONST
import QSS017A_Default as DEF
import QSS017A_Function as FUNC
import numpy as np

#---GB 23/0315------------------------------------------
from QSS017A_Analysis import *
from scipy.signal import find_peaks
from scipy.signal import savgol_filter   # smooth
import datetime

HVCOUNT=0
MEK=[]
ACETONE=[]
EA=[]
TOLUENE=[]
AVE_RESET_TIMES=5

#----------------------------------------------------------
global MEK_START, ACETONE_START,EA_START,TOLUENE_START, RANGE
ACETONE_START=57
MEK_START=73
EA_START=87
TOLUENE_START=90
RANGE=100
#-------------------------------------------------------
M1Peak_withT=[]
M2Peak_withT=[]
M3Peak_withT=[]
M4Peak_withT=[]

T=[]
DATETIME=[]      # 日期格式
ST=[]            # Scan Times
#-------------------------------------------------------

TITLE_TEXT = " iAnalyzer pMS "
VERSION_TEXT = TITLE_TEXT + "\n" + \
" QSS017A V1.11 \n\n" + \
" Copyright @ 2022 TAIP \n" + \
" Maintain by Quantaser Photonics Co. Ltd "

DisConnICON = "icon\\connect-blue.png"
ConnICON = "icon\\connect.png"
ModeICON = "icon\\mode.png"
CalibICON = "icon\\calib.png"
LayoutICON = "icon\\layout.png"
StartICON = "icon\\start.png"
StartICON_g = "icon\\start-gray.png"
PauseICON = "icon\\pause.png"
StopICON = "icon\\stop.png"
StopICON_g = "icon\\stop-gray.png"
AnaICON = "icon\\analyze.png"
EngICON = "icon\\engineer.png"
AvgICON = "icon\\average.png"
ESIoffICON = "icon\\ESI_Off.png"
ESIoffICON_g = "icon\\ESI_Off_g.png"
ESIonICON = "icon\\ESI_On.png"

Conn_Label = "Connect"
DisConn_Label = "Dis-connect"
Start_Label = "Execute"
Pause_Label = "Pause"
Stop_Label = "Stop"
Average_Label = "Save Average Data"
ESIoff_Label = "Turn ESI Off"
ESIon_Label = "Turn ESI On"

FT232H_ERROR1 = "FT232H Read Data Error ("
FT232H_ERROR2 = ")\nPlease Re-connect."

TEST_MODE = True
# Toolbar
Engineering_Mode = False
Average_Mode = True
ESI_Mode = True

USER_SCAN_MASS = True



class mainWindow(QMainWindow):
    def __init__(self, parent = None):
        super (mainWindow, self).__init__(parent)
        self.setWindowTitle(TITLE_TEXT)
        self.move(50,50)
        self.loggername = "Total"
        self.addAccesoryFlag(self.loggername) # Add logger
        #------------------------------------------------------------------
        #self.top = UI.mainWidget()

        # GB
        #------------------------------------------------------------------
        self.top = UI.mainWidget1()  
        #------------------------------------------------------------------
        self.act = ACT.qss017aAction(self.loggername, TEST_MODE)
        # self.actHK = ACT.qss017ActionHK(self.act.ft232, self.loggername)
        self.msgSc = QShortcut(QKeySequence('Ctrl+M'), self)

        self.mainUI()
        self.mainMenu()
        self.ToolBar()
        self.mainInit()
        self.linkFunction()

    def mainUI(self):
        mainLayout = QGridLayout()
        self.setCentralWidget(QWidget(self))
        mainLayout.addWidget(self.top,0,0,1,1)
        self.centralWidget().setLayout(mainLayout)

    def mainMenu(self):
        mainMenu = self.menuBar()
        menu_eng = QAction("&Engineering Parameters", self)
        menu_load = QAction("&Load User Setting Data", self)
        menu_save = QAction("&Save User Setting Data", self)
        menu_new = QAction("Save User Setting as &New File", self)

        menu_eng.triggered.connect(self.engSetting)
        menu_load.triggered.connect(self.loadSetting)
        menu_save.triggered.connect(self.saveSetting)
        menu_new.triggered.connect(self.newSetting)

        fileMenu = mainMenu.addMenu("&File")
        fileMenu.addAction(menu_eng)
        fileMenu.addAction(menu_load)
        fileMenu.addAction(menu_save)
        fileMenu.addAction(menu_new)

        menu_about = QAction("&Version", self)
        menu_about.triggered.connect(self.aboutBox)
        aboutMenu = mainMenu.addMenu("&About")
        aboutMenu.addAction(menu_about)

    def mainInit(self):
        self.connect_status = 0 # False
        self.setInfoText()
        self.changePlotType()
        self.select_path = ""
        self.readyRun = False
        self.save_flag = False

        # self.thread1 = QThread()
        # self.actHK.moveToThread(self.thread1)
        # self.thread1.started.connect(self.actHK.gauge_pump_readData)
        # self.actHK.gauge_pump_update_text.connect(self.gaugePumpUpdate)
        # self.actHK.gauge_finished.connect(self.gaugeClose)
        # self.actHK.ft232_error.connect(self.showFt232ErrorBox)

        self.thread = QThread()
        self.act.moveToThread(self.thread)
        self.thread.started.connect(self.act.massStart)
        self.act.update_data.connect(self.updateSignalData)
        #-GB-------------------------------------------------
        self.act.update_data.connect(self.analysis1)     
        #----------------------------------------------------
        self.act.finished.connect(self.signalClose)
        self.act.connected.connect(self.connected)
        self.act.update_gauge.connect(self.gaugePumpUpdate)
        self.act.show_error.connect(self.errorBox)
        # self.act.gauge_error.connect(self.showGaugeError)
        self.act.readyRun.connect(lambda:self.changeToolBarIcon(True))
        if (ESI_Mode):
            self.act.update_ESI.connect(self.update_ESI)

        self.accuTime = np.zeros(CONST.MAX_SAMPLE_COUNT)
        self.ticData = np.zeros(CONST.MAX_SAMPLE_COUNT)
        self.xicData = np.zeros(CONST.MAX_SAMPLE_COUNT)

        self.top.info.setUserFile(self.act.userLastFile[0])
        self.top.info.setEngFile(self.act.userLastFile[1])
        # print("mainInit massTheory = ", self.act.massTheory[0])
        # print("mainInit massCalibed = ", self.act.massCalibed[0])

    def linkFunction(self):
        self.msgSc.activated.connect(self.callPwdDialog)

    def getMinMaxValue(self, ms_center, ms_range):
        ms_center = float(ms_center)
        ms_range = int(ms_range)

        ms_min = ms_center - ms_range/2
        if (ms_min < self.act.abs_minMass):
            ms_min = self.act.abs_minMass
        elif (ms_min > self.act.abs_maxMass):
            ms_min = self.act.abs_maxMass

        ms_max = ms_center + ms_range/2
        if (ms_max < self.act.abs_minMass):
            ms_max = self.act.abs_minMass
        elif (ms_max > self.act.abs_maxMass):
            ms_max = self.act.abs_maxMass

        # print("min = " + str(ms_min))
        # print("max = " + str(ms_max))
        return ms_min, ms_max

    def setInfoText(self):
        if (USER_SCAN_MASS):
            # 2022-11-22 sherry++ , min_mass of scan_amp is abs_min_mass
            if (int(self.act.engPreset['mode']) == 0):
                min_mass = self.act.abs_minMass
            else:
                min_mass = int(self.act.userPreset['ms1_scan_min'])
                if (min_mass == DEF.MS1_Scan_Min) or (min_mass < self.act.abs_minMass):
                    min_mass = self.act.abs_minMass
                elif (min_mass > self.act.abs_maxMass):
                    min_mass = self.act.abs_maxMass

            max_mass = int(self.act.userPreset['ms1_scan_max'])
            if (max_mass == DEF.MS1_Scan_Max) or (max_mass > self.act.abs_maxMass):
                max_mass = self.act.abs_maxMass
            elif (max_mass < self.act.abs_minMass):
                max_mass = self.act.abs_minMass

            min_text = "%4.2f" % min_mass
            max_text = "%4.2f" % max_mass
        else:
            min_text = "%4.2f" % self.act.abs_minMass
            max_text = "%4.2f" % self.act.abs_maxMass

        scan_mass_text = min_text + " ~ " + max_text
        self.top.info.scan_mass_text.setText(scan_mass_text)

        trap_freq = int(self.act.engPreset['Trap_Freq'])
        r0 = float(self.act.engPreset['r0'])
        z0 = float(self.act.engPreset['z0'])

        freq_min,_,_ = FUNC.massFreqTransfer(self.act.trap_vol, trap_freq, r0, z0, FUNC.realyMass2theoryMass(self.act.abs_minMass, self.act.userPreset), 0)
        freq_max,_,_ = FUNC.massFreqTransfer(self.act.trap_vol, trap_freq, r0, z0, FUNC.realyMass2theoryMass(self.act.abs_maxMass, self.act.userPreset), 0)
        min_text = "%4.2f" % freq_min
        max_text = "%4.2f" % freq_max
        scan_freq_text = min_text + " ~ " + max_text + " (kHz)"
        self.top.info.scan_freq_text.setText(scan_freq_text)

        if (int(self.act.userPreset['mode']) == 2) or (int(self.act.userPreset['mode']) == 1):
            ms2_mass_min, ms2_mass_max = self.getMinMaxValue(self.act.userPreset['ms2_center'], self.act.userPreset['ms2_range'])
            min_text = "%4.2f" % ms2_mass_min
            max_text = "%4.2f" % ms2_mass_max
            ms2_mass_text = min_text + " ~ " + max_text

            self.act.ms2_freq2,_,_ = FUNC.massFreqTransfer(self.act.trap_vol, trap_freq, r0, z0, FUNC.realyMass2theoryMass(ms2_mass_min, self.act.userPreset), 0)
            self.act.ms2_freq1,_,_ = FUNC.massFreqTransfer(self.act.trap_vol, trap_freq, r0, z0, FUNC.realyMass2theoryMass(ms2_mass_max, self.act.userPreset), 0)
            min_text = "%4.2f" % self.act.ms2_freq2
            max_text = "%4.2f" % self.act.ms2_freq1
            ms2_freq_text = min_text + " ~ " + max_text + " (kHz)"

        if (int(self.act.userPreset['mode']) == 2):
            ms3_mass_min, ms3_mass_max = self.getMinMaxValue(self.act.userPreset['ms3_center'], self.act.userPreset['ms3_range'])
            min_text = "%4.2f" % ms3_mass_min
            max_text = "%4.2f" % ms3_mass_max
            ms3_mass_text = min_text + " ~ " + max_text

            self.act.ms3_freq2,_,_ = FUNC.massFreqTransfer(self.act.trap_vol, trap_freq, r0, z0, FUNC.realyMass2theoryMass(ms3_mass_min, self.act.userPreset), 0)
            self.act.ms3_freq1,_,_ = FUNC.massFreqTransfer(self.act.trap_vol, trap_freq, r0, z0, FUNC.realyMass2theoryMass(ms3_mass_max, self.act.userPreset), 0)
            min_text = "%4.2f" % self.act.ms3_freq2
            max_text = "%4.2f" % self.act.ms3_freq1
            ms3_freq_text = min_text + " ~ " + max_text + " (kHz)"

        if (int(self.act.engPreset['mode']) == 1):
            eng_mode_text = "Scan Freq."
        else:
            eng_mode_text = "Scan Amp."

        if (int(self.act.userPreset['mode']) == 2):
            user_mode_text = "MS3"
        elif (int(self.act.userPreset['mode']) == 1):
            user_mode_text = "MS2"
            ms3_mass_text = CONST.Unavailable_Text
            ms3_freq_text = CONST.Unavailable_Text
        else:
            user_mode_text = "MS1"
            ms2_mass_text = CONST.Unavailable_Text
            ms2_freq_text = CONST.Unavailable_Text
            ms3_mass_text = CONST.Unavailable_Text
            ms3_freq_text = CONST.Unavailable_Text

        mode_text = eng_mode_text + " / " + user_mode_text
        self.top.info.mode_text.setText(mode_text)
        self.top.info.ms2_mass_text.setText(ms2_mass_text)
        self.top.info.ms2_freq_text.setText(ms2_freq_text)
        self.top.info.ms3_mass_text.setText(ms3_mass_text)
        self.top.info.ms3_freq_text.setText(ms3_freq_text)

        if (int(self.act.userPreset['check_ticXic']) == 0):
            xic_text = CONST.Unavailable_Text
        else:
            xic_min, xic_max = self.getMinMaxValue(self.act.userPreset['xic_center'], self.act.userPreset['xic_range'])
            xic_min_text = "%4.2f" % xic_min
            xic_max_text = "%4.2f" % xic_max
            xic_text = xic_min_text + " ~ " + xic_max_text
        self.top.info.xic_text.setText(xic_text)

        # esi_text = str(self.act.userPreset['esi'])
        esi_text = str(self.act.dacValue[2])
        self.top.info.esi_text.setText(esi_text)

    def callPwdDialog(self):
        input = UI.pwdDialog.getParameter()
        if (input == CONST.Eng_Input):
            self.doEngAct()
        elif (input != ""):
            self.errorBox("Input Error")

    def doEngAct(self):
        self.act.userLastFile[1], self.act.engPreset, self.act.cg_data, self.act.tv_data = \
        UI.engDialog.getParameter(self.act.userLastFile[1], self.act.engPreset, self.act.cg_data, self.act.tv_data, self.loggername)
        self.act.saveUserLastFile()
        self.top.info.setEngFile(self.act.userLastFile[1])
        self.act.saveEngPreset(self.act.userLastFile[1])
        self.act.updatePlotMass()
        self.setInfoText()

    def ToolBar(self):
        toolbar = QToolBar("Setting")
        toolbar.setIconSize(QSize(64, 64))

        self.ConnAct = QAction(QIcon(ConnICON), Conn_Label, self)
        self.ConnAct.triggered.connect(self.doConnAct)
        toolbar.addAction(self.ConnAct)

        ModeAct = QAction(QIcon(ModeICON), CONST.Mode_Label, self)
        ModeAct.triggered.connect(self.doModeAct)
        toolbar.addAction(ModeAct)

        CalibAct = QAction(QIcon(CalibICON), CONST.Calib_Label, self)
        CalibAct.triggered.connect(self.doCalibAct)
        toolbar.addAction(CalibAct)

        LayoutAct = QAction(QIcon(LayoutICON), CONST.Layout_Label, self)
        LayoutAct.triggered.connect(self.doLayoutAct)
        toolbar.addAction(LayoutAct)

        self.RunAct = QAction(QIcon(StartICON_g), Start_Label, self)
        self.RunAct.triggered.connect(self.doRunAct)
        toolbar.addAction(self.RunAct)

        self.StopAct = QAction(QIcon(StopICON_g), Stop_Label, self)
        self.StopAct.triggered.connect(self.doStopAct)
        toolbar.addAction(self.StopAct)

        AnaAct = QAction(QIcon(AnaICON), CONST.Ana_Label, self)
        AnaAct.triggered.connect(self.doAnaAct)
        toolbar.addAction(AnaAct)

        if (Engineering_Mode):
            EngAct = QAction(QIcon(EngICON), CONST.Engineering_Mode_Label, self)
            EngAct.triggered.connect(self.doEngAct)
            toolbar.addAction(EngAct)

        if (Average_Mode):
            AvgAct = QAction(QIcon(AvgICON), Average_Label, self)
            AvgAct.triggered.connect(self.doAvgAct)
            toolbar.addAction(AvgAct)

        if (ESI_Mode):
            self.ESIAct = QAction(QIcon(ESIoffICON_g), ESIoff_Label, self)
            self.ESIAct.triggered.connect(self.doESIAct)
            toolbar.addAction(self.ESIAct)

        self.addToolBar(toolbar)

    def changeToolBarIcon(self, flag):
        if (flag):
            self.readyRun = True
            self.connect_status = 2 # True
            self.ConnAct.setIcon(QIcon(DisConnICON))
            self.ConnAct.setToolTip(DisConn_Label)
            self.RunAct.setIcon(QIcon(StartICON))
            # self.StopAct.setIcon(QIcon(StopICON))
            self.top.info.setConnectText(Qt.black, "Connected")
            if (ESI_Mode):
                self.ESIAct.setIcon(QIcon(ESIoffICON))
        else:
            self.readyRun = False
            self.connect_status = 0 # False
            self.ConnAct.setIcon(QIcon(ConnICON))
            self.ConnAct.setToolTip(Conn_Label)
            self.RunAct.setIcon(QIcon(StartICON_g))
            self.StopAct.setIcon(QIcon(StopICON_g))
            if (ESI_Mode):
                self.ESIAct.setIcon(QIcon(ESIoffICON_g))

    def doConnAct(self):
        self.act.run_type = "stop"
        self.RunAct.setToolTip(Start_Label)
        if (self.connect_status == 0):
            usbStatus = self.act.usbConnect()
            # print("usbStatus = " + str(usbStatus))
            if (usbStatus == 0):
                self.act.getHWversion()
            elif (usbStatus == 1):
                self.top.info.setConnectText(Qt.red, "Device not found")
            else:
                self.top.info.setConnectText(Qt.red, "Connect failed")
        elif (self.connect_status > 0): # 1 == Connecting , 2 == Connected
            self.closeAllAction()
            # sherry++ 2022.11.15, add usb status to dis-connect
            self.act.usbStatus = -1
            # sherry++ 2022.5.3, close device when dis-connect
            if (TEST_MODE == False):
                self.act.device.close()
            self.changeToolBarIcon(False)
            self.top.info.setConnectText(Qt.red, "Dis-connect")
        # print(self.connect_status)

    def doModeAct(self):
        self.act.userPreset = UI.msDialog.getParameter(self.act.userPreset, self.act.engPreset, self.act.tv_data, self.act.abs_minMass, self.act.abs_maxMass)
        self.act.saveUserPreset(self.act.userLastFile[0])
        self.act.updatePlotMass()
        self.act.updateXicMass()
        self.setInfoText()

    def doRunAct(self):
        if (self.readyRun == False):
            return
        if (self.act.run_type != "run"):
            if (self.act.run_type == "stop"):
                self.select_path = QFileDialog.getExistingDirectory(self, "Save Raw Data", "./")
            self.act.setParameterFlag = True
            self.act.run_type = "run"
            self.act.save_path = self.select_path
            self.RunAct.setIcon(QIcon(PauseICON))
            self.RunAct.setToolTip(Pause_Label)

        else:
            self.act.run_type = "pause"
            self.RunAct.setIcon(QIcon(StartICON))
            self.RunAct.setToolTip(Start_Label)

        # can press stop
        self.StopAct.setIcon(QIcon(StopICON))
        # print(self.act.run_type)

    def doStopAct(self):
        if (self.connect_status == 0):
            return
        if (self.act.run_type != "stop"):
            # print(self.act.run_type)
            self.act.run_type = "stop"
            self.act.rawfileindex = 0
            self.act.totalData = np.zeros(CONST.MAX_SAMPLE_COUNT)

            self.accuTime = np.zeros(CONST.MAX_SAMPLE_COUNT)
            self.ticData = np.zeros(CONST.MAX_SAMPLE_COUNT)
            self.xicData = np.zeros(CONST.MAX_SAMPLE_COUNT)

            self.RunAct.setIcon(QIcon(StartICON))
            self.RunAct.setToolTip(Start_Label)
            # can NOT press stop
            self.StopAct.setIcon(QIcon(StopICON_g))

            #-Analysis Fig Clearn---------------------------------
            M1Peak_withT.clear()
            M2Peak_withT.clear()
            M3Peak_withT.clear()
            M4Peak_withT.clear()
            T.clear()
            ST.clear()
            DATETIME.clear()

            self.top.inf.targetTable1.clearContents()      # 清除表格內容
            #-----------------------------------------------------

    def doCalibAct(self):
        calib_data = {}
        calib_data['threshold'] = self.act.userPreset['threshold'] #self.act.engPreset['threshold']
        calib_data['noise'] = self.act.userPreset['noise'] #self.act.engPreset['noise']
        calib_data['Calib_A'] = self.act.userPreset['Calib_A']
        calib_data['Calib_B'] = self.act.userPreset['Calib_B']
        calib_data = UI.calibDialog.getParameter(calib_data, self.act.singleData, self.act.massCalibed, self.loggername)
        self.act.userPreset['threshold'] = calib_data['threshold']
        # print("threshold = " + str(self.act.userPreset['threshold']))
        self.act.userPreset['noise'] = calib_data['noise']
        self.act.userPreset['Calib_A'] = calib_data['Calib_A']
        self.act.userPreset['Calib_B'] = calib_data['Calib_B']
        self.act.saveUserPreset(self.act.userLastFile[0])
        self.act.updatePlotMass()
        # print("doCalibAct massTheory = ", self.act.massTheory[0])
        # print("doCalibAct massCalibed = ", self.act.massCalibed[0])
        self.setInfoText()


    def doLayoutAct(self):
        layout_data = UI.plotDialog.getParameter(self.act.layout_data)
        self.act.saveUserPreset(self.act.userLastFile[0])
        self.changePlotType()

    def changePlotType(self):
        type1 = int(self.act.layout_data['layout_type1'])
        type2 = int(self.act.layout_data['layout_type2'])
        type3 = int(self.act.layout_data['layout_type3'])
        type4 = int(self.act.layout_data['layout_type4'])
        layout_type = [type1, type2, type3, type4]
        layout_grid = int(self.act.layout_data['layout_grid'])
        if (layout_grid == 4):
            self.top.mainPlot1.setVisible(False)
            self.top.mainPlot2.setVisible(False)
            self.top.mainPlot3.setVisible(False)
            self.top.mainPlot4.setVisible(True)
            self.top.mainPlot4.setPlotLabel(layout_type)
        elif (layout_grid == 3):
            self.top.mainPlot1.setVisible(False)
            self.top.mainPlot2.setVisible(False)
            self.top.mainPlot4.setVisible(False)
            self.top.mainPlot3.setVisible(True)
            self.top.mainPlot3.setPlotLabel(layout_type)
        elif (layout_grid == 2):
            self.top.mainPlot1.setVisible(False)
            self.top.mainPlot3.setVisible(False)
            self.top.mainPlot4.setVisible(False)
            self.top.mainPlot2.setVisible(True)
            self.top.mainPlot2.setPlotLabel(layout_type)
        else:
            self.top.mainPlot2.setVisible(False)
            self.top.mainPlot3.setVisible(False)
            self.top.mainPlot4.setVisible(False)
            self.top.mainPlot1.setVisible(True)
            self.top.mainPlot1.setPlotLabel(type1)

    def doAnaAct(self):
        ana_data = {}
        ana_data['threshold'] = self.act.userPreset['threshold'] #self.act.engPreset['threshold']
        ana_data['noise'] = self.act.userPreset['noise'] #self.act.engPreset['noise']
        ana_data['xic_center'] = self.act.userPreset['ana_xic_center']
        ana_data['xic_range'] = self.act.userPreset['ana_xic_range']
        ana_data = UI.analyzeDialog.getParameter(ana_data, self.loggername)
        self.act.userPreset['threshold'] = ana_data['threshold']
        self.act.userPreset['noise'] = ana_data['noise']
        self.act.userPreset['ana_xic_center'] = ana_data['xic_center']
        self.act.userPreset['ana_xic_range'] = ana_data['xic_range']
        self.act.saveUserPreset(self.act.userLastFile[0])

    def doAvgAct(self):
        # 2022-11-14 sherry++, ask user to select folder before save average data
        self.select_path = QFileDialog.getExistingDirectory(self, "Save Average Data", "./")
        if (self.select_path != ""):
            self.act.save_path = self.select_path
            self.act.saveAvgData()

    def doESIAct(self):
        if (self.act.dacValue[2] == 0):
            self.act.setESIDacValue(reset = False)
            self.ESIAct.setIcon(QIcon(ESIoffICON))
            self.ESIAct.setToolTip(ESIoff_Label)
        else:
            self.act.setESIDacValue(reset = True)
            self.ESIAct.setIcon(QIcon(ESIonICON))
            self.ESIAct.setToolTip(ESIon_Label)

    def update_ESI(self):
        esi_text = str(self.act.dacValue[2])
        self.top.info.esi_text.setText(esi_text)

    def addAccesoryFlag(self, loggername):
        Qlogger.QuConsolelogger(loggername, logging.DEBUG)
        #Qlogger.QuFilelogger(loggername, logging.WARNING, "log.txt")

    def engSetting(self):
        filename,_ = QFileDialog.getOpenFileName(self, "Load " + CONST.Engineer_File_Text, "./" + DEF.USER_SET_FILEPATH, CONST.Engineer_File_Text + " (*.eng)")
        if (filename != ""):
            print("engSetting", filename)
            self.act.userLastFile[1] = filename
            self.act.saveUserLastFile()
            self.act.loadEngPreset(filename)
            self.act.saveEngPreset(filename)
            self.act.updatePlotMass()
            self.setInfoText()
            self.top.info.setEngFile(filename)

    def loadSetting(self):
        filename,_ = QFileDialog.getOpenFileName(self, "Load " + CONST.User_File_Text, "./" + DEF.USER_SET_FILEPATH, CONST.User_File_Text + " (*.user)")
        if (filename != ""):
            print("loadSetting", filename)
            self.act.userLastFile[0] = filename
            self.act.loadUserPreset(filename)
            self.top.info.setUserFile(filename)

    def saveSetting(self):
        self.act.saveUserPreset(self.act.userLastFile[0])
        self.save_flag = True

    def newSetting(self):
        filename,_ = QFileDialog.getSaveFileName(self, "Save User Setting as New File", "./" + DEF.USER_SET_FILEPATH, "User Setting Files (*.user)")
        if (filename != ""):
            print("newSetting", filename)
            self.act.userLastFile[0] = filename
            self.act.saveUserLastFile()
            self.act.saveUserPreset(filename)
            self.top.info.setUserFile(filename)
            self.save_flag = True

    def connected(self, connect_result):
        if connect_result :
            print("Connect OK")
            self.connect_status = 1 # True
            self.top.info.setConnectText(Qt.black, "Connecting")
            # connect success , but can NOT run
            # self.changeToolBarIcon(True)
            self.ConnAct.setIcon(QIcon(DisConnICON))
            self.ConnAct.setToolTip(DisConn_Label)
            self.act.runFlag = True
            self.thread.start()
        elif (self.connect_status > 0): # 1 == Connecting , 2 == Connected
            self.connect_status = 0 # False
            self.top.info.setConnectText(Qt.black, "Connection Failed")
            self.changeToolBarIcon(False)

    # def showGaugeError(self, error):
    #   if self.act.runFlag:
    #       print("showGaugeError = " + str(error))
    #       gauge_text = "Gauge Error" + str(error)
    #       pe = QPalette()
    #       pe.setColor(QPalette.WindowText, Qt.red)
    #       self.top.info.gauge_text.setPalette(pe)
    #       self.top.info.gauge_text.setText(gauge_text)

    def gaugePumpUpdate(self, gauge, pump):
        # print("gaugePumpUpdate")
        if self.act.runFlag:
            pe = QPalette()
            # print("gauge = " + gauge)
            # if (gauge == "Error"):
            #   self.showFt232ErrorBox(ft232_error)
            if (gauge < 0):
                gauge_text = "Gauge Error " + str(gauge)
                pe.setColor(QPalette.WindowText, Qt.red)
                self.top.info.gauge_text.setPalette(pe)
            else:
                gauge_text = "%4.5f" % gauge
                pe.setColor(QPalette.WindowText, Qt.black)
                self.top.info.gauge_text.setPalette(pe)

            if (pump < 0):
                pump_text = "Pump Error " + str(pump)
                pe.setColor(QPalette.WindowText, Qt.red)
                self.top.info.pump_text.setPalette(pe)
            else:
                pump_text = str(pump) + " rpm"
                pe.setColor(QPalette.WindowText, Qt.black)
                self.top.info.pump_text.setPalette(pe)

            self.top.info.gauge_text.setText(gauge_text)
            self.top.info.pump_text.setText(pump_text)

    def updateSignalData(self, signal_data, avg_data, st_index):
        if (st_index == 1):
            self.timeOffset = time.time()
            # print(self.timeOffset)

        # print("updateSignalData")
        self.top.info.scanTime_text.setText(str(st_index))

        # new added accu fuction
        if (int(self.act.userPreset['check_ticXic']) == 1):
            # threshold = float(self.act.engPreset['threshold'])
            threshold = float(self.act.userPreset['threshold'])
            # noise = int(self.act.engPreset['noise'])
            noise = int(self.act.userPreset['noise'])
            peaks, peak_list = FUNC.findPeakList(threshold, noise, self.act.massCalibed, signal_data)
            peak_num = len(peak_list)
            # print("peak_num = " + str(peak_num) )
            if (peak_num > 0):  
                # print(self.act.rawfileindex)
                t_diff = time.time() - self.timeOffset
                # print("t_diff = " + str(t_diff))
                self.accuTime = np.append(self.accuTime, t_diff)
                temp = np.array(peak_list).transpose()
                self.ticData = np.append(self.ticData, sum(temp[1]))
                singletemp = 0
                for i in range(0, peak_num):
                    if (temp[0][i] > self.act.xicMinMass) and (temp[0][i] < self.act.xicMaxMass):
                        singletemp = singletemp + temp[1][i]
                self.xicData = np.append(self.xicData, singletemp)

        type1 = int(self.act.layout_data['layout_type1'])
        type2 = int(self.act.layout_data['layout_type2'])
        type3 = int(self.act.layout_data['layout_type3'])
        type4 = int(self.act.layout_data['layout_type4'])
        layout_type = [type1, type2, type3, type4]
        # print(layout_type)

        plot_data = [ [self.act.massCalibed, signal_data], [self.act.massCalibed, avg_data], [self.accuTime, self.ticData], [self.accuTime, self.xicData] ]
        data1 = plot_data[type1]
        data2 = plot_data[type2]
        data3 = plot_data[type3]
        data4 = plot_data[type4]

        layout_grid = int(self.act.layout_data['layout_grid'])
        # print(layout_grid)
        if (layout_grid == 4):
            self.top.mainPlot4.setPlotLabel(layout_type)
            self.top.mainPlot4.setPlotData(data1, data2, data3, data4)
        elif (layout_grid == 3):
            self.top.mainPlot3.setPlotLabel(layout_type)
            self.top.mainPlot3.setPlotData(data1, data2, data3)
        elif (layout_grid == 2):
            self.top.mainPlot2.setPlotLabel(layout_type)
            self.top.mainPlot2.setPlotData(data1, data2)
        else:
            self.top.mainPlot1.setPlotLabel(type1)
            self.top.mainPlot1.setPlotData(data1)


        #---GuanBo----2023/2/3---------------------------------------
    def analysis1(self, signal_data, avg_data, st_index):

        #--Sacn 60 次後,Counter 重置---------------------------------
        global HVCOUNT
        HVCOUNT=HVCOUNT+1

        if HVCOUNT==60:
            HVCOUNT=0 
        #print(HVCOUNT)
        
        #--Show information in the page 2---------------------------
        self.top.target.select.label12.setText(str(st_index))
        #-----------------------------------------------------------

        #--Take mass and adc data; data type numpy array------------
        mass=self.act.massCalibed
        data=signal_data

        # 1. Peak1:MEK----------------------------------------------
        Molecular=MEK_START
        Start_Index=MIndex(Molecular,RANGE,mass,data)
        End_Index=Start_Index+RANGE
        #LocalM=MLocal(Molecular,RANGE,mass,data)
        LocalData=MData(Molecular,RANGE,mass,data)
             
        MEK.append(LocalData)

        # 把數次的 data 合併並轉成 dataframe
        df=pd.DataFrame(MEK)
        df=df.T
        #print(df)
        #---變成一維 Array--------------
        df_avg=df.mean(axis=1)
        #MaxNumber=df.max()       
        AveData=[]
        AveData=df_avg
        #--------------------------------
        M1_Peak=AveData.max()
        M1_Peak=int(M1_Peak)
        self.top.target.select.label4.setText(str(M1_Peak))

        #-y=ax+b Calibrition Curve information; x=abs(y-b)/a-------------------------
        a1=0.1
        b1=0 # baseline
        Concentration1=abs(M1_Peak-b1)/a1
        Concentration1=int(Concentration1)
        self.top.target.select.label13.setText(str(Concentration1))
        #-----------------------------------------------------------------------------

        #--畫圖--Tab2 Fig.2, 先固定在MEK----------------------------------------------
        x=mass[Start_Index:End_Index]
        y1=AveData[0:RANGE]
        self.top.TargetPlot.setPlotData(x,y1)
        #-----------------------------------------------------------------------------


        # 2. Peak2--23/03/17---ACETONE------------------------------------------------
        Molecular=ACETONE_START
        Start_Index=MIndex(Molecular,RANGE,mass,data)
        End_Index=Start_Index+RANGE
        #LocalM=MLocal(Molecular,RANGE,mass,data)
        LocalData=MData(Molecular,RANGE,mass,data)
             
        ACETONE.append(LocalData)

        # 把數次的 data 合併並轉成 dataframe
        df=pd.DataFrame(ACETONE)
        df=df.T
        #print(df)
        #---變成一維 Array--------------
        df_avg=df.mean(axis=1)
        #MaxNumber=df.max()       
        AveData=[]
        AveData=df_avg
        #--------------------------------
        M2_Peak=AveData.max()
        M2_Peak=int(M2_Peak)
        self.top.target.select.label2.setText(str(M2_Peak))

        #-y=ax+b Calibrition Curve information; x=abs(y-b)/a--------------------------
        a2=0.1
        b2=0 # baseline
        Concentration2=abs(M2_Peak-b2)/a2
        Concentration2=int(Concentration2)
        self.top.target.select.label14.setText(str(Concentration2))
        #-----------------------------------------------------------------------------

        # 3. Peak3--23/03/21---EA-----------------------------------------------------
        Molecular=EA_START
        Start_Index=MIndex(Molecular,RANGE,mass,data)
        End_Index=Start_Index+RANGE
        #LocalM=MLocal(Molecular,RANGE,mass,data)
        LocalData=MData(Molecular,RANGE,mass,data)
             
        EA.append(LocalData)

        # 把數次的 data 合併並轉成 dataframe
        df=pd.DataFrame(EA)
        df=df.T
        #print(df)
        #---變成一維 Array--------------
        df_avg=df.mean(axis=1)
        #MaxNumber=df.max()       
        AveData=[]
        AveData=df_avg
        #--------------------------------
        M3_Peak=AveData.max()
        M3_Peak=int(M3_Peak)
        self.top.target.select.label6.setText(str(M3_Peak))

        #-y=ax+b Calibrition Curve information; x=abs(y-b)/a--------------------------
        a3=0.1
        b3=0 # baseline
        Concentration3=abs(M3_Peak-b3)/a3
        Concentration3=int(Concentration3)
        self.top.target.select.label15.setText(str(Concentration3))
        #-----------------------------------------------------------------------------

        # 4. Peak4--23/03/22---Toluene------------------------------------------------
        Molecular=TOLUENE_START
        Start_Index=MIndex(Molecular,RANGE,mass,data)
        End_Index=Start_Index+RANGE
        #LocalM=MLocal(Molecular,RANGE,mass,data)
        LocalData=MData(Molecular,RANGE,mass,data)
             
        TOLUENE.append(LocalData)

        # 把數次的 data 合併並轉成 dataframe
        df=pd.DataFrame(TOLUENE)
        df=df.T
        #print(df)
        #---變成一維 Array--------------
        df_avg=df.mean(axis=1)
        #MaxNumber=df.max()       
        AveData=[]
        AveData=df_avg
        #--------------------------------
        M4_Peak=AveData.max()
        M4_Peak=int(M4_Peak)
        self.top.target.select.label8.setText(str(M4_Peak))

        #-y=ax+b Calibrition Curve information; x=abs(y-b)/a--------------------------
        a4=0.1
        b4=0 # baseline
        Concentration4=abs(M4_Peak-b4)/a4
        Concentration4=int(Concentration4)
        self.top.target.select.label16.setText(str(Concentration4))
        #-----------------------------------------------------------------------------


        #--畫圖--Tab2 Fig.1-------------------------------------
        if int(st_index)%AVE_RESET_TIMES==0:
            #---------------------------------------------------
            M1Peak_withT.append(Concentration1)
            M2Peak_withT.append(Concentration2)
            M3Peak_withT.append(Concentration3)
            M4Peak_withT.append(Concentration4)
            T.append(st_index)
            
            now = datetime.datetime.now().strftime("%H:%M:%S")
            
            DATETIME.append(now)
            ST.append(st_index)
            #print(ST)
            #print(DATETIME)
            #---------------------------------------------------
            x=T
            y1=M1Peak_withT
            y2=M2Peak_withT
            y3=M3Peak_withT
            y4=M4Peak_withT
            self.top.TargetPlot_WithT.setPlotData(x,y1,y2,y3,y4)

            #--23/03/20--Table Data to dataframe, and to a excel file---
            df1=pd.DataFrame(DATETIME)
            df2=pd.DataFrame(y1)
            df3=pd.DataFrame(y2)
            df4=pd.DataFrame(y3)
            df5=pd.DataFrame(y4)
            df6=pd.concat([df1,df2,df3,df4,df5],axis=1)
            # rename Index
            df7=df6.set_axis(['Time','Acetone/IPA','MEK','EA','Toluene'], axis=1, inplace=False)
            #print(df7)


            if self.top.inf.check2.isChecked():
                filename=self.top.inf.filenameinput.text()
                if filename=='':
                    filename='OutputData'
                else:
                    filename=filename+'.xlsx'
                
                #print(filename)
                df7.to_excel(filename)
            
            #-添加數據進 Analysis Table---------------------------------
            for i in range(len(ST)):
                #1. MEK-------------------------------------------------
                ScanTimes_newItem=QTableWidgetItem(str(ST[i]))
                ScanTimes_newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.top.inf.targetTable1.setItem(i,0, ScanTimes_newItem)

                DateTime_newItem=QTableWidgetItem(str(DATETIME[i]))
                #DateTime_newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.top.inf.targetTable1.setItem(i,1, DateTime_newItem)

                m1_newItem=QTableWidgetItem(str(M1Peak_withT[i]))
                m1_newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.top.inf.targetTable1.setItem(i,3, m1_newItem)
                #------------------------------------------------------

                #2. ACETONE-------------------------------------
                m2_newItem=QTableWidgetItem(str(M2Peak_withT[i]))
                m2_newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.top.inf.targetTable1.setItem(i,2, m2_newItem)
                #-----------------------------------------------

                #3. EA------------------------------------------
                m3_newItem=QTableWidgetItem(str(M3Peak_withT[i]))
                m3_newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.top.inf.targetTable1.setItem(i,4, m3_newItem)
                #-----------------------------------------------

                #4. Toluene------------------------------------------
                m4_newItem=QTableWidgetItem(str(M4Peak_withT[i]))
                m4_newItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.top.inf.targetTable1.setItem(i,5, m4_newItem)
                #----------------------------------------------------


        #-平均幾次後重置 
        if (HVCOUNT%AVE_RESET_TIMES==0):   
            #self.top.target.targetTable.clearContents()    
            #self.top.inf.targetTable1.clearContents()      # 清除表格內容
            #self.top.target.targetTable.setRowCount(0)    # 將行數設置為0

            # 清空累積的 Data.
            MEK.clear()
            ACETONE.clear()
            EA.clear()
            TOLUENE.clear()
            #print(TotalLocalData)

            # Turn Off High Voltage
            #---------------------------------------------------------------------------
                #self.act.setDacValue(reset = True)             # reset DAC and see command
                #self.act.sendResetCmd()
                #print('Turn Off High Voltage')
            #---------------------------------------------------------------------------

            # Turn On High Voltage
            #if (HVCOUNT==40):
                #self.act.setDacValue(reset = False)           #  set DAC and see command
                #self.act.sendResetCmd()
                #print('Turn On High Voltage')

    def signalClose(self):
        self.thread.quit()
        self.thread.wait()
        # print("signal close")

    def aboutBox(self):
        versionBox = QMessageBox()
        print(self.act.ver_text)
        ver_text = VERSION_TEXT + "\n\n HW version : "
        ver_text += self.act.ver_text
        versionBox.about(self, "Version", ver_text)

    def errorBox(self, msg):
        msgBox = QMessageBox()
        msgBox.about(self, "Message", msg)

    def closeAllAction(self):
        if (self.connect_status > 0):
            self.act.setDacValue(reset = True) # reset DAC
            # sherry++ 2022.4.1
            self.act.sendResetCmd()
        #self.pumpClose()
        #self.actHK.gauge_turn(False)
        self.act.runFlag = False
        self.connect_status = 0 # False
        self.changeToolBarIcon(False)

    def showFt232ErrorBox(self, type):
        self.closeAllAction()
        self.top.info.setConnectText(Qt.red, "Connect failed")

        if (TEST_MODE == False):
            self.act.device.close()

        Error_Msg = FT232H_ERROR1 + str(type) + FT232H_ERROR2
        self.errorBox(Error_Msg)

    def closeEvent(self, event):
        # print("window close")
        self.closeAllAction()
        # sherry++ 2022.5.9
        if (self.save_flag == False):
            title = self.tr(CONST.Save_Label)
            saveText = self.tr(CONST.save_text)
            reply = QMessageBox.question(self, title, saveText, QMessageBox.Yes, QMessageBox.No)
            if (reply == QMessageBox.Yes):
                # print("save file before close")
                self.newSetting()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = mainWindow()
    main.show()
    os._exit(app.exec_())

