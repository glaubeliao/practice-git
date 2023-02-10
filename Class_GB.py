



class Counter(QThread):

    start_signal = pyqtSignal()
    run_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    HVoff_signal = pyqtSignal()
    HVon_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()

        self.flag = True

    def run(self):
        i=0
        self.flag = True
        while self.flag:
            i=i+1 
            time.sleep(1)

            print('Threads:' + str(i))
           
            #if Run_Status=="True":
                #print("Now is Run")
                #self.start_signal.emit()


            #if Stop_Status=="True":
                #print("STOP")
                #self.stop_signal.emit()

            if i==5:
                
                #--Connect-------------------
                self.start_signal.emit()
                #----------------------------

            if i==30:
                
                #--run-----------------------
                self.run_signal.emit()
                #----------------------------

            if i==40:
                
                #--Stop ---------------------
                self.stop_signal.emit()
                #----------------------------

            if i==50:
                
                #--Disconncet ---------------
                self.HVoff_signal.emit()
                #----------------------------
                i=0

    def stop(self):
        self.flag = False
        




