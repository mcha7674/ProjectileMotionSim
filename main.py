from importlib.metadata import files
import sys
import subprocess
import pandas as pd
from PySide6.QtWidgets import QSizeGrip
from PySide6.QtCore import QPropertyAnimation,QEasingCurve
from PySide6.QtWidgets import QMessageBox,QDialog,QFileDialog
from ui_physGUI import * # import GUI file
import animations # custom import
from matplotlib import use
use('Qt5Agg')
import plots # custom import
import os
from os import path
import shutil
from os.path import expanduser
"""
Contains all code and handling for gui interface
"""
class MainWindow(QMainWindow):
    pages = {"home":0,"launch":1,"plots":2,"settings":3,"help":4}
    def __init__(self):
        super().__init__()  # grab inherited constructor
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # from ui file
        # Set Window Icon
        self.setWindowTitle("Projectile Motion Simulator")
        # Remove window title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Set main background to be transparent
        #self.setAttribute(Qt.WA_TranslucentBackground)
        # Add Window Size Grip Feature
        QSizeGrip(self.ui.size_grip)
        # initialize statistics
        self._initStats()
        # Close the Window
        self.ui.closeButton.clicked.connect(lambda:self.close())
        # Restore/ Maximize Window
        self.ui.maximizeButton.clicked.connect(lambda:self.restore_or_maximize_window())
        # Minimize the window
        self.ui.minimizeButton.clicked.connect(lambda:self.showMinimized())
        # Add click event and move event to the top header and footer frames to move window
        self.ui.headerFrame.mouseMoveEvent = self.moveWindow
        self.ui.footerFrame.mouseMoveEvent = self.moveWindow
        # Slide menu side bar if menu button is clicked
        self.ui.menuButton.clicked.connect(lambda: self.slideMenu())
        # Integrate Menu buttons with Stacked widget (main Body)
        # First Set the start up page:
        self.ui.stackedWidget.setCurrentIndex(MainWindow.pages["home"])
        # Integrate Menu buttons here
        self.ui.homeButton.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.launchMenuButton.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.plotsButton.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(2))
        self.ui.settingButton.clicked.connect(lambda : self.settingsPage())
        self.ui.helpButton.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(4))
        ###### Grab Inputs ######
        self.inputs = \
        {   # value is in  [inputObject, value]
            "x0":[self.ui.x0LineEdit,0],
            "y0":[self.ui.y0LineEdit,0],
            "v0":[self.ui.v0LineEdit,0],
            "angle":[self.ui.angleLineEdit,0],
            "finalAngle":[self.ui.finalAngleLineEdit,0],
            "mass":[self.ui.massLineEdit,0],
            "radius":[self.ui.radiusLineEdit,0],
            "C":[self.ui.dragCLineEdit,0],
            "T0":[self.ui.seaTemptLineEdit,0],
            "windV":[self.ui.vWindLineEdit,0],
            "airToggle":[self.ui.dragButton,False],
            "vacToggle":[self.ui.vacButton,False],
            "compareToggle":[self.ui.compareButton,False],
            "dtSlider":[self.ui.timeStepSlider,0],
            "stepAngleSlider":[self.ui.stepAngleSlider,0],
            "stepAngle":[self.ui.stepAngleCounter,0],
            "dt":[self.ui.timeStepCounter,0.1]        
        }
        # STORE Line Edit Inputs and intake signals
        self.inputs["x0"][0].editingFinished.connect(lambda:self.storeLineValue(key="x0"))
        self.inputs["y0"][0].textEdited.connect(lambda:self.storeLineValue(key="y0"))
        self.inputs["v0"][0].textEdited.connect(lambda:self.storeLineValue(key="v0"))
        self.inputs["angle"][0].textEdited.connect(lambda:self.storeLineValue(key="angle"))
        self.inputs["finalAngle"][0].textEdited.connect(lambda:self.storeLineValue(key="finalAngle"))
        self.inputs["mass"][0].textEdited.connect(lambda:self.storeLineValue(key="mass"))
        self.inputs["radius"][0].textEdited.connect(lambda:self.storeLineValue(key="radius"))
        self.inputs["C"][0].textEdited.connect(lambda:self.storeLineValue(key="C"))
        self.inputs["T0"][0].textEdited.connect(lambda:self.storeLineValue(key="T0"))
        self.inputs["windV"][0].editingFinished.connect(lambda:self.storeLineValue(key="windV"))
        # STORE toggle radio button/checkbox Inputs and intake signals
        self.inputs["airToggle"][0].toggled.connect(lambda:self.storeToggle(key="airToggle"))
        self.inputs["vacToggle"][0].toggled.connect(lambda:self.storeToggle(key="vacToggle"))
        self.inputs["compareToggle"][0].toggled.connect(lambda:self.storeToggle(key="compareToggle"))
        # Slider Input signals 
        self.inputs["dtSlider"][0].valueChanged.connect(lambda:self.storeSlider(key="dtSlider",keyLabel = "dt"))
        self.inputs["stepAngleSlider"][0].valueChanged.connect(lambda:self.storeSlider(key="stepAngleSlider",keyLabel = "stepAngle"))
        # Set default radio button for real time toggle
        self.ui.realTimeRadioButton.setChecked(True) 
        # init trajectory type
        self.trajType = "none" # Single, Multi, Compare, and None
        # Inputs gathered, now incorporate the launch button
        self.ui.launchButton.clicked.connect(lambda:self.launch())
        # create Plots button and plot name array
        self.ui.createPlotsButton.clicked.connect(lambda:self._createPlots())
        self.ui.nextPlotButton.clicked.connect(lambda:self._cyclePlots("next"))
        self.ui.prevPlotButton.clicked.connect(lambda:self._cyclePlots("prev"))
        # Show recent animation button
        self.ui.recentAnimButton.clicked.connect(lambda:self._showRecentAnimation())
        # Reset Button
        self.ui.resetButton.clicked.connect(lambda:self._launchReset())
        # Save inputs button
        self.ui.saveInputsButton.clicked.connect(lambda:self._saveInputs())
        # Load Inputs button
        self.ui.loadInputsButton.clicked.connect(lambda:self._loadInputs())
        # Save Data button
        self.ui.saveDataButton.clicked.connect(lambda:self._saveData())
        # Save Stats Button
        self.ui.saveStatsButton.clicked.connect(lambda:self._saveStats())
        # Open Stats Button
        self.ui.openStatsButton.clicked.connect(lambda:self._openStats())
        # Save Plots button
        self.ui.savePlotsButton.clicked.connect(lambda:self._savePlots())
        # Clear Stats and Clear Inputs Buttons
        self.ui.clearInputMemButton.clicked.connect(lambda:self._clearMem("Inputs", self.ui.clearInputMemButton))
        self.ui.clearStatsMemButton.clicked.connect(lambda:self._clearMem("Stats", self.ui.clearStatsMemButton))
        
    def launch(self):
        """ The MOTHER function
        0. Delete all previous data in 'Plots' and 'Data'
        1. Decide what type of trajectory can be conducted based off of inputs
            6 Types:
                Single trajectory - drag, vaccum, adiabatic
                multiTrajectory - drag, vaccum, adiabatic
        2. If no trajectory could be decided, throw error and reset system
        3. If trajectory decided, store all inputs to file (after clearing it) by iterating dictionary
        4. Execute cpp code to calculate trajectory data (external to class) which stores to files
        """
        # delete old data and plots
        self.rmDataAndPlots()
        # initialize pop up msg box:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Input Error")
        errorOccured = False
        # initial conditions - check if v0 and angle inputs made
        # check if mediums toggle even made
        if (not self.inputs["compareToggle"][1]) and (not self.inputs["airToggle"][1]) and (not self.inputs["vacToggle"][1]):
                msg.setText("Choose a Medium!")
                msg.setInformativeText("Make sure to toggle a medium type.")
                msg.exec()
                errorOccured = True
        if self.inputs["v0"][1] == 0 or self.inputs["angle"][1] == 0:
            msg.setText("Initial velocity or angle cannot be zero!")
            msg.setInformativeText("Make sure to not leave these lines empty")
            msg.exec()
            errorOccured = True
        # handle multi trajectory decision
        if self.inputs["stepAngle"][1] == 0 and self.inputs["finalAngle"][1] == 0:
            pass
        elif self.inputs["stepAngle"][1] != 0 and self.inputs["finalAngle"][1] != 0:
            pass
        elif (self.inputs["finalAngle"][1] <= self.inputs["angle"][1]) and  (self.inputs["angle"][1] != 0 ):
            msg.setText("final angle must be greater than initial angle!")
            msg.exec()
            errorOccured = True
        else:
            msg.setText("Step angle and max angle impossible!")
            msg.exec()
            errorOccured = True
        # Wind input
        if (abs(self.inputs["windV"][1]) >= self.inputs["v0"][1]):
            msg.setText("The absolute value of the Wind Velocity must be less than the inital velocity")
            msg.exec()
            errorOccured = True
        # projectile inputs
        if (self.inputs["mass"][1] == 0 or self.inputs["radius"][1] == 0) and (not self.inputs["vacToggle"][1]):
            msg.setText("mass or radius must be greater than 0.")
            msg.setInformativeText("Make sure to not leave these lines empty")
            msg.exec()
            errorOccured = True
        # Toggle inputs
        if self.inputs["airToggle"][1] or self.inputs["compareToggle"][1]:
            if self.inputs["C"][1] == 0:
                msg.setText("Drag was enabled but drag coefficient is 0 or unspecified!")
                msg.setInformativeText("Make sure to not leave this line empty")
                msg.exec()
                errorOccured = True
        if self.inputs["compareToggle"][1]:
            # need T0 now
            if self.inputs["T0"][1] == 0:
                msg.setText("SeaLevel Temperature must be specified!")
                msg.setInformativeText("Make sure to not leave this line empty")
                msg.exec()
                errorOccured = True
        # Error checks completed.
        # Update type label
        self.ui.typeLabel.setText(self.trajType)
        # output inputs to file.
        if not errorOccured:
            self._outputInput()
            print("FIle Output Complete")
            # data sent to file, calc using cpp
            subprocess.call("source.exe")
            # Decide data pathhs and output statistics
            self.dataPath = "Data/"
            if self.trajType == "single":
                self.dataPath += "trajData.csv"
            elif self.trajType == "multi":
                self.dataPath += "trajData2.csv"
            else:
                self.dataPath += "comparisons.csv"
            # output data
            self._outputStats()
            # commence and show trajectory animation
            self._Animation()

    ##############PLOTS########################
    def rmDataAndPlots(self, mother_folder = "data_plots_stats",directories = ("Data","Plots")):
        for directory in directories:
            for filename in os.listdir(directory):
                f = os.path.join(directory, filename)
                if os.path.isfile(f):
                    shutil.copy(f, mother_folder)
                    os.remove(f)

    def _cyclePlots(self, direction):
        # only displaying one plot
        if direction == "next" and len(self.plotNames) != 1:
            self.iCount += 1
        if direction == "prev" and len(self.plotNames) != 1:
            self.iCount -= 1
        index = self.iCount % len(self.plotNames)
        self._addPlotPixmap(self.plotNames[index])
        
    def _addPlotPixmap(self, plotName):
        pixmap = QPixmap("Plots/"+plotName)
        self.ui.plotDisplayLabel.setPixmap(pixmap)
        self.ui.plotDisplayLabel.setScaledContents(True)

    def _createPlots(self):
        """
        Creates and appends plots as png's inside the Plots directory
        """
        self.plotNames = []
        self.iCount = 0
        directory = "Data/"
        plotPath = "Plots/"
        figSize = (12,8)
        if self.trajType == "single":
            dataName = "trajData.csv"
            plotName = "singlePos.png"
            # single Positional trajectory
            xyPlot = plots.trajPlot(figsize=figSize)
            xyPlot.read_data(dataName=dataName)
            xyPlot.newSubplot(xlb=["Position in X (meters)"],
            ylb = ["Position in Y (meters)"],title=["Trajectory of Shell"])
            xyPlot.posTraj()
            print("Plot saved to ", plotPath + plotName)
            xyPlot.saveFig(pName = plotName)
            xyPlot.closePlot()
            self._addPlotPixmap(plotName)
            self.plotNames.append(plotName)
            # single trajectory velocity
            vPlot = plots.trajPlot(figsize=figSize)
            vPlot.read_data(dataName=dataName)
            vPlot.newSubplot(xlb=["Time (seconds)"],
            ylb = ["Projectile Speed (meters/second)"],title=["Speed of projectile vs Time"])
            vPlot.speedTraj(color="blue")
            plotName = "singleSpeed.png"
            print("Plot saved to ", plotPath + plotName)
            vPlot.saveFig(pName = plotName)
            vPlot.closePlot()
            self.plotNames.append(plotName)
            # single positional AND velocity trajectories
            vAndXY_plot = plots.trajPlot(figsize=figSize)
            vAndXY_plot.read_data(dataName=dataName)
            vAndXY_plot.newSubplot(xlb=["Position in X (meters)","Time (seconds)"],
            ylb = ["Position in Y (meters)","Projectile Speed (meters/second)"],
            title=["Trajectory of Shell","Speed of projectile vs Time"],rowCols=[2,1])
            plotName = "singleSpeedAndPos.png"
            vAndXY_plot.speedAndPosTraj(speedColor="blue",posColor="black")
            print("Plot saved to ", plotPath + plotName)
            vAndXY_plot.saveFig(pName = plotName)
            vAndXY_plot.closePlot()
            self.plotNames.append(plotName)
        elif self.trajType == "multi":
            dataName = "trajData2.csv"
            dataName2 = "maxTraj.csv"
            plotName = "manyTraj.png"
            multiPlot = plots.trajPlot(manyTraj=True)
            multiPlot.read_data(dataName=dataName)
            multiPlot.newSubplot(xlb=["Position in X (meters)"],
            ylb = ["Position in Y (meters)"],title=["Trajectory of Shell"])
            multiPlot.posTraj()
            multiPlot.read_data(dataName=dataName2)
            maxAngle = multiPlot.getAngle()
            multiPlot.posTraj(color="orange",
                Label = "Trajectory with max range for angle {} degrees".format(maxAngle))
            multiPlot.setLegend()
            multiPlot.saveFig(plotName)
            multiPlot.closePlot()
            print("Plot saved to ", plotPath + plotName)
            self._addPlotPixmap(plotName)
            self.plotNames.append(plotName)
        elif self.trajType == "compare":
            # JUST DRAG PLOTS
            plotName = "dragComparisons.png"
            comparePlots = plots.trajPlot(comparisons=True)
            comparePlots.read_data(dataName="comparisons.csv",Id="DRAG")
            comparePlots.newSubplot(xlb=["Position in X (meters)"],
            ylb = ["Position in Y (meters)"],title=["Trajectory of Shell"])
            comparePlots.posTraj(Label = "Drag With NO Adiabatic Height Dependence",
            color="blue")
            comparePlots.read_data(dataName="comparisons.csv",Id="HEIGHT_DRAG")
            comparePlots.posTraj(Label = "Drag With Adiabatic Height Dependence",
            color="orange")
            comparePlots.setLegend()
            comparePlots.saveFig(plotName)
            print("Plot with Drag and Height dependent drag comparisons saved to ",
                plotPath + plotName)
            comparePlots.closePlot()
            # add 1st plot to Plots page label and append name
            self._addPlotPixmap(plotName)
            self.plotNames.append(plotName)
            # Plot No DRAG AND DRAG PLOTS
            plotName = "comparisons.png"
            comparePlots.read_data(dataName="comparisons.csv",Id="NO_DRAG")
            comparePlots.posTraj(Label = "Vaccum",color="black")
            comparePlots.setLegend()
            comparePlots.saveFig(plotName)
            print("Plot with Drag and vaccum comparisons saved to ",
                plotPath + plotName)
            self.plotNames.append(plotName)
            comparePlots.closePlot()
    ###########RESET LAUNCH INPUTS AND STATS and Clear#####################################
    def _clearMem(self, directory, buttonObj, mother_folder = "data_plots_stats"):
        for filename in os.listdir(directory):
                f = os.path.join(directory, filename)
                if os.path.isfile(f):
                    shutil.copy(f, mother_folder)
                    os.remove(f)
        buttonObj.setText("Cleared")

    def _launchReset(self):
        """
        Set all inputs to zero,
        Clear Stats
        delete plots and data
        """
        for key, itemArr in self.inputs.items():
            if key == "vacToggle" or key == "airToggle" or key == "compareToggle":
                itemArr[1] = False
            elif key == "dt": 
                itemArr[1] = 0.1
            elif  key=="dtSlider":
                itemArr[0].setValue(0.1)
            elif  key=="stepAngleSlider":
                itemArr[0].setValue(0)
            else: 
                itemArr[1] = 0
                itemArr[0].setText(str("0"))
        # na the stats
        self._initStats()
        # delete old data and plots
        self.rmDataAndPlots()

    ##########################STATS AND INPUTS OUTPUT/SAVING AND LOADING########################################
    def _savePlots(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        if not os.listdir("Plots/"):
            msg.setWindowTitle("Save Error")
            msg.setText("No Plots to save!")
            msg.setInformativeText("Launch a projectile and press the 'create plots' button.")
            msg.exec()
        else:
            home = expanduser("~")
            folderName = QFileDialog.getExistingDirectory(self, 'Select Save Location for Plots', home)
            for filename in os.listdir("Plots"): 
                shutil.copy("Plots/"+filename, folderName)
        

    def _saveStats(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        if not os.listdir("Stats/"):
            msg.setWindowTitle("Save Error")
            msg.setText("No Stats to save!")
            msg.setInformativeText("Launch a projectile first")
            msg.exec()
        else:
            home = expanduser("~")
            folderName = QFileDialog.getExistingDirectory(self, 'Select Save Location', home)
            # create file and copy contents
            shutil.copy("Stats/stats.txt", folderName)     

    def _saveData(self):
        # Open data file
        options = QFileDialog.Options()
        fileName,_ = QFileDialog.getOpenFileName(self,
        caption = "Choose Data",dir = "Data/",filter="CSV Files (*.csv)",options=options)
        # error handling
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        if not os.listdir("Data/"):
            msg.setWindowTitle("Save Error")
            msg.setText("No data to save!")
            msg.setInformativeText("Launch a projectile first")
            msg.exec()
        else: # save data at folder location
            home = expanduser("~") # home directory for user
            folderName = QFileDialog.getExistingDirectory(self, 'Select Save Location', home)
            # create file and copy contents
            shutil.copy(fileName, folderName)               

    def _saveInputs(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        if not os.listdir("Data/"):
            msg.setWindowTitle("Save Error")
            msg.setText("No Inputs to save!")
            msg.setInformativeText("Launch a projectile first")
            msg.exec()
        else:
            options = QFileDialog.Options()
            fileName,_ = QFileDialog.getSaveFileName(self,
            caption = "Save Input",dir = "Inputs/",filter="Text Files (*.txt)",options=options)
            # create file and copy contents
            shutil.copy("inputs.txt", fileName)

    def _openStats(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        if not os.listdir("Stats/"):
            msg.setWindowTitle("Open Error")
            msg.setText("No Stats to Open!")
            msg.setInformativeText("Launch a projectile first")
            msg.exec()
        else:
            # options = QFileDialog.Options()
            # fileName,_ = QFileDialog.getOpenFileName(self,
            # caption = "Open Stats",dir = "Stats/",filter="Text Files (*.txt)",options=options)
            os.startfile(os.path.abspath("Stats/stats.txt"))

    def _loadInputs(self):
        options = QFileDialog.Options()
        fileName,_ = QFileDialog.getOpenFileName(self,
        caption = "Load Input",dir = "Inputs/",filter="Text Files (*.txt)",options=options)
        # load inputs onto main inputs file
        shutil.copy(fileName, "inputs.txt")
        # create file and copy contents
        with open("inputs.txt","r") as file:
            # load inputs onto variables
            for line in file:
                line = tuple(line.split())
                key = line[0]
                val = line[1]
                if key == "trajType": continue
                if val == "True": 
                    self.inputs[key][1] = True
                elif val == "False": 
                    self.inputs[key][1] = False
                else: self.inputs[key][1] = float(val)
            # set sliders
            self.inputs["dtSlider"][1] = self.inputs["dt"][1]
            self.inputs["stepAngleSlider"][1] = self.inputs["stepAngle"][1]
        # set text of inputs
        for key, itemArr in self.inputs.items():
            obj = itemArr[0]
            value = itemArr[1]
            print("Key = ", key, " | val = ",value, "valueType = ",type(value))
            # dont store sliders
            if key == "dtSlider" or key == "stepAngleSlider":
                obj.setValue(value)
            elif key == "airToggle" or key == "vacToggle" or key == "compareToggle":
                if value : obj.setChecked(True)
            else: obj.setText(str(value))

        self._updateTrajType()
        

    def _initStats(self):
        # init all stats to NA
        self.ui.sRangeLE.setText("NA")
        self.ui.sHeightLE.setText("NA")
        self.ui.sTimeLE.setText("NA")
        self.ui.mRangeLE.setText("NA")
        self.ui.mHeightLE.setText("NA")
        self.ui.mTimeLE.setText("NA")
        self.ui.cRangeLE.setText("NA")
        self.ui.cHeightLE.setText("NA")
        self.ui.cTimeLE.setText("NA")
        self.ui.cRangeLE_2.setText("NA")
        self.ui.cHeightLE_2.setText("NA")
        self.ui.cTimeLE_2.setText("NA")
        self.ui.cRangeLE_3.setText("NA")
        self.ui.cHeightLE_3.setText("NA")
        self.ui.cTimeLE_3.setText("NA")

    def _outputStats(self):
        # set all stats to NA
        self._initStats()
        # Fill in relevant stats
        if self.trajType == "single":
            df = pd.read_csv(self.dataPath)
            range = df["x"].max()/1000
            maxHeight = df["y"].max()/1000
            flightTime = df["t"].max()
            self.ui.sRangeLE.setText(str("{:.3f}".format(range))+" km")
            self.ui.sHeightLE.setText(str("{:.3f}".format(maxHeight))+" km")
            self.ui.sTimeLE.setText(str("{:.3f}".format(flightTime))+" s")
        elif self.trajType == "multi":
            df = pd.read_csv(self.dataPath)
            range = df["x"].max()/1000
            maxHeight = df["y"].max()/1000
            flightTime = df["t"].max()
            self.ui.mRangeLE.setText(str("{:.3f}".format(range))+" km")
            self.ui.mHeightLE.setText(str("{:.3f}".format(maxHeight))+" km")
            self.ui.mTimeLE.setText(str("{:.3f}".format(flightTime))+" s")
        elif self.trajType == "compare":
            self.df = pd.read_csv(self.dataPath)
            self.df1 = self.df[self.df["id"] == "DRAG"]
            self.df1.reset_index(inplace=True)
            self.df2 = self.df[self.df["id"] == "NO_DRAG"]
            self.df2.reset_index(inplace=True)
            self.df3 = self.df[self.df["id"] == "HEIGHT_DRAG"]
            self.df3.reset_index(inplace=True)
            range1 = self.df1["x"].max()/1000 # in km
            maxHeight1 = self.df1["y"].max()/1000
            flightTime1 = self.df1["t"].max()
            range2 = self.df2["x"].max()/1000
            maxHeight2 = self.df2["y"].max()/1000
            flightTime2 = self.df2["t"].max()
            range3 = self.df3["x"].max()/1000
            maxHeight3 = self.df3["y"].max()/1000
            flightTime3 = self.df3["t"].max()
            self.ui.cRangeLE.setText(str("{:.3f}".format(range1))+" km")
            self.ui.cHeightLE.setText(str("{:.3f}".format(maxHeight1))+" km")
            self.ui.cTimeLE.setText(str("{:.3f}".format(flightTime1))+" s")
            self.ui.cRangeLE_2.setText(str("{:.3f}".format(range2))+" km")
            self.ui.cHeightLE_2.setText(str("{:.3f}".format(maxHeight2))+" km")
            self.ui.cTimeLE_2.setText(str("{:.3f}".format(flightTime2))+" s")
            self.ui.cRangeLE_3.setText(str("{:.3f}".format(range3))+" km")
            self.ui.cHeightLE_3.setText(str("{:.3f}".format(maxHeight3))+" km")
            self.ui.cTimeLE_3.setText(str("{:.3f}".format(flightTime3))+" s")
         
    def _outputInput(self):
        with open("inputs.txt", "w") as f:
            # write traj type
            typeRow = ["trajType",str(self.trajType)]
            f.writelines(" ".join(typeRow))
            f.write("\n") 
            for key, itemArr in self.inputs.items():
                # dont store sliders
                if key == "dtSlider" or key == "stepAngleSlider":
                    continue
                row = [key,str(itemArr[1])]
                f.writelines(" ".join(row))
                f.write("\n")
    
    ###################ANIMATION###########################
    def _Animation(self):
        # Create Animation
        if self.trajType == "single":
            self.isCompare = False
            self.isMulti = False
            self.legend = False
        elif self.trajType == "multi":
            self.isCompare = False
            self.isMulti = True
            self.legend = True
        elif self.trajType == "compare":
            self.isCompare = True
            self.isMulti = False
            self.legend = True
        
        self.isRealTime = self.ui.realTimeRadioButton.isChecked()
        self.ani = animations.Animation(self.dataPath,figSize=(6,5),
        isComparing=self.isCompare,isMulti=self.isMulti, realTime=self.isRealTime)
        self.ani.decorateGraph(title = "Trajectory", xLabel="X (meters)",
        yLabel= "Y (meters)",setLegend=self.legend)
        self.ani.createAnimation()
        self.ani.showPlot(Block = False)


    def _showRecentAnimation(self):
        """Only show if data Exists (which means there is an animation to show)"""
        if len(os.listdir(os.path.relpath("Data"))) != 0:
            print("Showing Plot...")
            self._Animation()
        else: print("No recent animations available")

############################INPUT HANDLING###################################
    def _updateTrajType(self):
        if self.inputs["compareToggle"][1]:
            self.trajType = "compare"
        elif (self.inputs["finalAngle"][1] != 0) and  (self.inputs["stepAngle"][1] != 0 ):
            self.trajType = "multi"
        elif self.inputs["airToggle"][1] or self.inputs["vacToggle"][1]:
            self.trajType = "single";
        else:
            self.trajType = "single";
        self.ui.typeLabel.setText(self.trajType)
            
    def storeLineValue(self, key):
        errorFound = self.checkLineValue(key)
        if not errorFound:
            value = float(self.inputs[key][0].text())
            self.inputs[key][1]= value
        self._updateTrajType() # update

    def checkLineValue(self,key):
        """
        check for non numerical or negative values. If true,
        then highlight lineEdit red and clear text.
        """
        error = False
        lineEdit = self.inputs[key][0]
        value = self.inputs[key][1]
        try:
            float(lineEdit.text())
            lineEdit.setStyleSheet("border: 0px ")
            error = False
        except ValueError:
            lineEdit.setStyleSheet("border: 1px solid red")
            # change back text to say Error
            lineEdit.clear()
            # set value to default
            self.inputs[key][1] = 0
            error = True
        return error

    def storeToggle(self,key):
        value = self.inputs[key][0].isChecked()
        self.inputs[key][1]= value
        self._updateTrajType() 

    def storeSlider(self, key, keyLabel):
        if (keyLabel == "dt"):
            sliderValue = self.inputs[key][0].value()/100
        elif keyLabel == "stepAngle":
            sliderValue = self.inputs[key][0].value()
        self.inputs[key][1]= sliderValue # store value
        self.inputs[keyLabel][1]= sliderValue # store value
        #print("KEYLABEL = ", )
        # store in label
        self.inputs[keyLabel][0].setText(str(sliderValue))
        self._updateTrajType()
    
    def settingsPage(self):
        self.ui.clearInputMemButton.setText("Clear")
        self.ui.clearStatsMemButton.setText("Clear")
        self.ui.stackedWidget.setCurrentIndex(3)
########################WINDOW FUNCTIONS#############################
    # restore of maximize window method
    def restore_or_maximize_window(self):
        # self is reference our mainwindow class object
        # If window is maxmized
        if self.isMaximized(): 
            self.showNormal()
        else:
            self.showMaximized()

    # Method to move window if mouse drags title bar
    def moveWindow(self,event):
        # First detect if window is no full screen
        if self.isMaximized() == False:
            if event.buttons() == Qt.LeftButton:
                # Move the Window
                self.move(self.pos() + event.globalPos() - self.clickPosition)
                self.clickPosition = event.globalPos()
                event.accept()

    # Add mouse events to the window - overwrites original method
    def mousePressEvent(self,event):
        self.clickPosition = event.globalPos()
    
    # Implement Slide Menu Function
    def slideMenu(self):
        # Get current left menu width
        width = self.ui.menuSideBar.width()
        minWidth = 50
        maxWidth = 117
        duration = 500
        # If minimized, expan.d menu
        if width == minWidth: newWidth = maxWidth
        # If maximized, minimize it again
        else: newWidth = minWidth
        # Animate the transition
        self.animation = QPropertyAnimation(self.ui.menuSideBar, b"maximumWidth")#Animate minimumWidht
        self.animation.setDuration(duration)
        self.animation.setStartValue(width)#Start value is the current menu width
        self.animation.setEndValue(newWidth)#end value is the new menu width
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.start()
         
##########################################################
# Create Necessary Binaries if dont exist
data_exists = path.exists("Data") 
plots_exists = path.exists("Plots")
stats_exists = path.exists("Stats")
inputs_exists = path.exists("Inputs")
motherFolder_exists = path.exists("data_plots_stats")
if (not data_exists):
    os.mkdir("Data")
if (not plots_exists):
    os.mkdir("Plots")
if (not stats_exists):
    os.mkdir("Stats")
if (not inputs_exists):
    os.mkdir("Inputs")
if (not motherFolder_exists):
    os.mkdir("data_plots_stats")
# EXECUTE APP
app = QApplication(sys.argv)
win = MainWindow()
win.show()  # show main window object
# EXIT
try:
    sys.exit(app.exec())
except SystemExit:
    print("Closing Window...")
    win.rmDataAndPlots()
