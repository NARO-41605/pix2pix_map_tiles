# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QPix2pixDialog
                                 A QGIS plugin
 test
                             -------------------
        begin                : 2017-09-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by nss
        email                : kobayashi@nssv.co.jp
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import re
import shutil
import math

from PyQt4 import QtGui, QtCore, uic
from __builtin__ import str

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qpix2pix_dialog_base.ui'))

from pix2pixRun import pix2pixRun
from pix2pixThread import pix2pixThread

from qgis.core import *
from qgis.gui import *


class QPix2pixDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface=None, parent=None):
        """Constructor."""
        super(QPix2pixDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface

        self.layersList = self.iface.legendInterface().layers()

        self.rectSelect_btn.clicked.connect(self.rectSelect)
        self.getLayers_btn.clicked.connect(self.layersListSet)
        self.pix2pixModel_btn.clicked.connect(self.dirSelect_pix2pixModel)
        self.outputPath_btn.clicked.connect(self.dirSelect_outputPath)


    def reject(self):
        QtGui.QDialog.reject(self)

    def accept(self):
        self.messLabel.setText('')

        maxLon = self.maxLonInput.text()
        minLon = self.minLonInput.text()
        maxLat = self.maxLatInput.text()
        minLat = self.minLatInput.text()

        zoomLevel = self.zoomLevelInput.text()

        GPUdevice = self.GPUdeviceInput.text()

        pix2pixModel = self.pix2pixModelInput.text()
        outputPath = self.outputPathInput.text()
        layerName = self.layerNameInput.text()

        selectLayersList = self.LayersSelectList.selectedItems()

        self.__restoreGui(setval=False)
        self.progressBar.show()

        errorFlg = False
        Mess = ''
        if not(self.__floatCheck(maxLon) and self.__floatCheck(minLon) and
               self.__floatCheck(maxLat) and self.__floatCheck(minLat) ):
            errorFlg = True
            Mess = 'Error : Extent is incorrect.'
        elif float(maxLon) < float(minLon):
            errorFlg = True
            Mess = 'Error : maxLon or minLon is incorrect.'
        elif float(maxLat) < float(minLat):
            errorFlg = True
            Mess = 'Error : maxLat or minLat is incorrect.'
        elif not zoomLevel.isdigit() or int(zoomLevel) < 1:
            errorFlg = True
            Mess = 'Error : zoomLevel is incorrect.'
        elif not GPUdevice.isdigit() or int(GPUdevice) < 0:
            errorFlg = True
            Mess = 'Error : GPU device number is incorrect.'
        elif pix2pixModel == '':
            errorFlg = True
            Mess = 'Error : pix2pix model is incorrect.'
        elif outputPath == '':
            errorFlg = True
            Mess = 'Error : output path is incorrect.'
        elif layerName == '':
            errorFlg = True
            Mess = 'Error : layer name is incorrect.'
        elif len(selectLayersList) < 1:
            errorFlg = True
            Mess = 'Error : layer no select.'

        if not errorFlg:
            self.workThread = pix2pixThread(maxLon, minLon, maxLat, minLat, zoomLevel, pix2pixModel, outputPath, layerName, self.iface,
                                            GPUdevice, selectLayersList, self.layersIdList)

            self.workThread.addLayer.connect(self.addLayer_thread)
            self.workThread.processFinished.connect(self.processFinished)
            self.workThread.rangeChanged.connect(self.setProgressRange)
            self.workThread.updateProgress.connect(self.updateProgress)

            self.workThread.start()

        else:
            self.__restoreGui(setval=True)
            self.messLabel.setText(Mess)

    def rectSelect(self):
        canvas = self.iface.mapCanvas()
        extent = canvas.extent()
        extent = QgsCoordinateTransform(canvas.mapRenderer().destinationCrs(), QgsCoordinateReferenceSystem('EPSG:4326')).transform(extent)
        self.maxLonInput.setText(str(extent.xMaximum()))
        self.minLonInput.setText(str(extent.xMinimum()))
        self.maxLatInput.setText(str(extent.yMaximum()))
        self.minLatInput.setText(str(extent.yMinimum()))


    def layersListSet(self):
        layer_list = []
        layer_list2 = {}

        self.LayersSelectList.clear()
        self.layersIdList = {}
        layers = self.iface.legendInterface().layers()
        layerNum = 0
        for layer in layers:
            layer_list.append(unicode(str(layerNum) + ':') + unicode(layer.name()))
            layer_list2[unicode(str(layerNum) + ':') + unicode(layer.name())] = layer.id()
            layerNum += 1

        if not len(layer_list) == 0:
            self.LayersSelectList.addItems(layer_list)
            self.layersIdList = layer_list2

    def dirSelect_pix2pixModel(self):
        dirname = QtGui.QFileDialog.getExistingDirectory(self, 'Open Directory', os.path.expanduser('~') + '/Desktop')
        self.pix2pixModelInput.setText(dirname)

    def dirSelect_outputPath(self):
        dirname = QtGui.QFileDialog.getExistingDirectory(self, 'Open Directory', os.path.expanduser('~') + '/Desktop')
        self.outputPathInput.setText(dirname)

    def addLayer_thread(self, imagePath, layerName):
        layer = QgsRasterLayer(imagePath, layerName)

        if not layer.isValid():
            Mess = "can not add layer."
        else:
            Mess = 'all clear'
            layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

            QgsMapLayerRegistry.instance().addMapLayer(layer, False)
            layer_tree = QgsProject.instance().layerTreeRoot()
            layer_tree.insertChildNode(0, QgsLayerTreeLayer(layer))
            self.updateProgress()

        self.messLabel.setText(Mess)

    def addLayer(self, imagePath, layerName):
        layer = QgsRasterLayer(imagePath, layerName)

        if not layer.isValid():
            return False

        QgsMapLayerRegistry.instance().addMapLayer(layer, False)
        layer_tree = QgsProject.instance().layerTreeRoot()
        layer_tree.insertChildNode(0, QgsLayerTreeLayer(layer))

        return True

    def setProgressRange(self, message, value):
        self.progressBar.setFormat(message)
        self.progressBar.setRange(0, value)
        self.progressBar.setValue(0)

    def updateProgress(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    def processFinished(self, status, Mess):
        self.stopProcessing()
        self.__restoreGui(setval=True)
        if not status:
            self.messLabel.setText(Mess)

    def stopProcessing(self):
        if self.workThread is not None:
            self.workThread.stop()
            self.workThread = None

    def setupGui(self):
        self.__restoreGui()
        self.rectSelect()
        self.layersListSet()
        self.setProgressRange('pix2pix run : (%p%)', 5)

        self.zoomLevelInput.setText('')
        self.GPUdeviceInput.setText('0')
        self.pix2pixModelInput.setText('')
        self.outputPathInput.setText('')
        self.layerNameInput.setText('')

        self.messLabel.setText('')

        self.progressBar.hide()


    def __restoreGui(self, setval=True):
        self.maxLonInput.setEnabled(setval)
        self.minLonInput.setEnabled(setval)
        self.maxLatInput.setEnabled(setval)
        self.minLatInput.setEnabled(setval)
        self.zoomLevelInput.setEnabled(setval)
        self.GPUdeviceInput.setEnabled(setval)
        self.pix2pixModelInput.setEnabled(setval)
        self.outputPathInput.setEnabled(setval)
        self.layerNameInput.setEnabled(setval)
        self.LayersSelectList.setEnabled(setval)
        self.rectSelect_btn.setEnabled(setval)
        self.getLayers_btn.setEnabled(setval)
        self.pix2pixModel_btn.setEnabled(setval)
        self.outputPath_btn.setEnabled(setval)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(setval)
        self.buttonBox.button(QtGui.QDialogButtonBox.Close).setEnabled(setval)


    def __floatCheck(self, value):
        result = bool(re.compile("^\d+(\.\d+)?\Z").match(str(value)))

        return result











