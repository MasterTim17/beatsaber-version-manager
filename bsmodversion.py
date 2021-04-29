import json
import os
import sys
import re  # regex
import time  # sleep
import shutil  # copy
import psutil  # programm beenden

from bs4 import BeautifulSoup
import requests
import webbrowser
import subprocess

from pynput.keyboard import Key, Controller


from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi, compileUiDir
compileUiDir("UI")

config = {}


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("ui/main.ui", self)
        self.pathButton.clicked.connect(self.openPath)
        self.updateButton.clicked.connect(self.openUpdate)
        self.revertButton.clicked.connect(self.openRevert)

        self.pathLabel.setText(config["installPath"])
        self.modVersionLabel.setText(config["modVersion"])
        self.beatsaberVersionLabel.setText(config["beatsaberVersion"])

        self.updateW = UpdateWindow()
        self.revertW = RevertWindow()

    def openPath(self):
        dir = QFileDialog.getExistingDirectory()
        if(dir):
            config["installPath"] = dir.replace("/", "\\")

    def openUpdate(self):
        path = os.path.join(config["installPath"],
                            "..\\..", "appmanifest_620980.acf")
        with open(path, "r") as f:
            lines = f.readlines()
            for l in lines:
                # check stateflag
                if l.find("StateFlags") >= 0:
                    if l.find("4") >= 0:
                        msg = QMessageBox()
                        msg.setText("No update pending!")
                        msg.exec()
                    else:
                        self.updateW.show()
                    # f.close()
                    break
            f.close()

        # self.updateW.show() #debug comment

    def openRevert(self):
        if config["beatsaberVersion"] == config["modVersion"]:
            msg = QMessageBox()
            msg.setText("Version equal. No revert needed!")
            msg.exec()
        else:
            self.revertW.show()

        # self.revertW.show() #debug comment


# 1. webseite öffnen und manifest kopieren
# 2. manifest in textfeld eintragen
# 3. appmanifest-acf modifizieren
#       stateflag und manifest nummer
class UpdateWindow(QtWidgets.QWidget):
    def __init__(self):
        super(UpdateWindow, self).__init__()
        loadUi("ui/update.ui", self)
        self.websiteButton.clicked.connect(self.openWebsite)
        self.finishButton.clicked.connect(self.finish)

    def openWebsite(self):
        self.update()

    def update(self):
        webbrowser.open("https://steamdb.info/depot/620981/manifests/")
        self.manifestEdit.setEnabled(True)
        self.finishButton.setEnabled(True)

    def finish(self):
        # replace manifest id and stateflag
        if len(self.manifestEdit.text()) < 18:
            msg = QMessageBox()
            msg.setText("ManifestID too short")
            msg.exec()
            return  # debug comment

        path = os.path.join(config["installPath"],
                            "..\\..", "appmanifest_620980.acf")
        lines = []

        try:
            with open(path, "r") as f:
                m = 0
                lines = f.readlines()
                i = 0
                for l in lines:
                    # replace stateflag
                    if l.find("StateFlags") >= 0:
                        lines[i] = l.replace("6", "4")

                    # replace manifest id
                    if l.find("InstalledDepots") >= 0 and m == 0:
                        m = 1
                    if l.find("620981") >= 0 and m == 1:
                        m = 2
                    if l.find("manifest") >= 0 and m == 2:
                        manifest = re.search("\d{16,19}", l).group()
                        lines[i] = l.replace(
                            manifest, self.manifestEdit.text())
                        break
                    i += 1

                f.close()

            with open(path, "w") as f:
                f.writelines(lines)
                f.close()
        except:
            msg = QMessageBox()
            msg.setText("File Error")
            msg.exec()

        killSteam()
        self.close()


# 1. steam patcher
# 2. steam open console
# 3. revert to old version
#       download depot from old manifest
#       copy depot into folder (and overwrite)


class RevertWindow(QtWidgets.QWidget):
    def __init__(self):
        super(RevertWindow, self).__init__()
        loadUi("ui/revert.ui", self)
        self.steamButton.clicked.connect(self.isOpen)
        self.patchButton.clicked.connect(self.doPatch)
        self.consoleButton.clicked.connect(self.openConsole)
        self.revertButton.clicked.connect(self.doRevert)

    def isOpen(self):
        rpl = QMessageBox.question(
            self, "", "Steam opened?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if rpl == QMessageBox.Yes:
            self.patchButton.setEnabled(True)

    def doPatch(self):
        if not os.path.exists("SteamDepotDownpatcher.exe"):
            r = requests.get(
                "https://github.com/fifty-six/zig.SteamManifestPatcher/releases/download/v3/SteamDepotDownpatcher.exe")
            open("SteamDepotDownpatcher.exe", "wb").write(r.content)
        subprocess.call("SteamDepotDownpatcher.exe")

        self.consoleButton.setEnabled(True)

    def openConsole(self):
        os.system("start steam://open/console")
        time.sleep(2)
        keyboard = Controller()
        keyboard.type("download_depot 620980 620981 " +
                      config["currentManifestId"]+"\n")

        msg = QMessageBox()
        msg.setText("Wait for \"Depot download complete\" in steam console!")
        msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        msg.exec()

        self.revertButton.setEnabled(True)

    def doRevert(self):
        text, okPressed = QInputDialog.getText(
            self, "", "Path correct?", QLineEdit.Normal, "C:\\Program Files (x86)\\Steam\\steamapps\\content\\app_620980\\depot_620981")
        if okPressed and text != '':
            print(text)
            shutil.copytree(text, config["installPath"], dirs_exist_ok=True)
        
        killSteam()
        self.close()


def readConfig():
    global config
    initConfig()
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            f.close()
    except:
        print("error loading config")


def initConfig():
    global config
    if not os.path.exists("config.json"):
        config["modVersion"] = getModVersion()
        config["beatsaberVersion"] = getBeatsaberVersion()
        config["currentManifestId"] = getManifestId()
        config["installPath"] = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Beat Saber"
        saveConfig()


def saveConfig():
    global config
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            f.close()
    except:
        print("error saving config")


def getModVersion():
    try:
        path = os.path.join(config["installPath"],
                            "UserData", "Beat Saber IPA.json")
        with open(path, "r") as f:
            js = json.load(f)
            # config["modVersion"] = js["LastGameVersion"]
            return js["LastGameVersion"]
            f.close()
    except:
        print("error getting mod version")


def getBeatsaberVersion():
    # beatsaber version auslesen
    try:
        path = os.path.join(config["installPath"],
                            "Beat Saber_Data", "globalgamemanagers")
        with open(path, "rb") as f:
            content = f.read().decode("ascii", "ignore")
            i = content.index("public.app-category.games")
            vers = content[i+50:i+300]
            # config["beatsaberVersion"] = vers.rstrip('\x00')
            # config["beatsaberVersion"] = re.findall("\d{1,2}.\d{1,3}.\d{1,3}", vers)[0]
            return re.findall("\d{1,2}.\d{1,3}.\d{1,3}", vers)[0]
            f.close()
    except:
        print("error getting beatsaber version")


def getManifestId():
    # manifest id speichern
    try:
        path = os.path.join(config["installPath"],
                            "..\\..", "appmanifest_620980.acf")
        with open(path, "r") as f:
            m = 0
            for l in f.readlines():
                if l.find("InstalledDepots") >= 0 and m == 0:
                    m = 1
                if l.find("620981") >= 0 and m == 1:
                    m = 2
                if l.find("manifest") >= 0 and m == 2:
                    manifest = re.search("\d{16,19}", l).group()
                    return manifest
            f.close()
    except:
        print("error getting manifest id")


def killSteam():
    # steam.exe beenden
    for process in psutil.process_iter():
        if process.name() == "steam.exe":
            process.kill()

    msg = QMessageBox()
    msg.setText("Success! Please restart steam")
    msg.exec()


def checkVersion():
    mV = getModVersion()
    if mV != config["modVersion"]:
        if mV == getBeatsaberVersion():
            config["modVersion"] = mV
            config["currentManifestId"] = getManifestId()
            saveConfig()
        else:
            webbrowser.open(
                "https://steamcommunity.com/sharedfiles/filedetails/?id=1805934840")
            text, okPressed = QInputDialog.getText(
                self, "", "ManifestID not detectable. Please copy ManifestID from version"+mV+" and paste", QLineEdit.Normal)
            if okPressed and len(text) >= 18:
                config["modVersion"] = mV
                config["currentManifestId"] = text
                saveConfig()

    bsV = getBeatsaberVersion()
    if bsV != config["beatsaberVersion"]:
        config["beatsaberVersion"] = bsV
        saveConfig()


def main():
    app = QApplication(sys.argv)

    readConfig()
    checkVersion()

    mainW = MainWindow()
    mainW.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
