# -*- coding: utf-8 -*-
import os
import re
import shutil
import math

from PyQt4 import QtGui, QtCore
from pix2pixRun import pix2pixRun

from qgis.core import *
from qgis.gui import *

class pix2pixThread(QtCore.QThread):

    rangeChanged = QtCore.pyqtSignal(str, int)
    updateProgress = QtCore.pyqtSignal()
    addLayer = QtCore.pyqtSignal(str, str)
    processFinished = QtCore.pyqtSignal(bool, str)

    def __init__(self, maxLon, minLon, maxLat, minLat, zoomLevel, pix2pixModel, outputPath, layerName, iface,
                  GPUdevice, selectLayersList, layersIdList):

        QtCore.QThread.__init__(self, QtCore.QThread.currentThread())
        self.mutex = QtCore.QMutex()
        self.stopMe = 0

        self.maxLon = float(maxLon)
        self.minLon = float(minLon)
        self.maxLat = float(maxLat)
        self.minLat = float(minLat)

        self.zoomLevel = int(zoomLevel)

        self.pix2pixModel = pix2pixModel.encode("utf-8")
        self.outputPath = outputPath.encode("utf-8")
        self.layerName = layerName.encode("utf-8")

        self.pix2pixParam = {'GPUdevice':int(GPUdevice)}

        self.iface = iface
        self.selectLayersList = selectLayersList
        self.layersIdList = layersIdList

        self.workspace = os.path.join(self.outputPath, 'pix2pixTmp/')


    def run(self):
        self.mutex.lock()
        self.stopMe = 0
        self.mutex.unlock()

        self.rangeChanged.emit(self.tr('pix2pix run : (%p%)'), 5)

        if not os.path.isdir(self.workspace):
            os.makedirs(self.workspace)
        else:
            shutil.rmtree(self.workspace)
            os.makedirs(self.workspace)


        self.tileLeftTop, tileLeftTop_tmp = self.__latlon2tile(self.minLon, self.maxLat, self.zoomLevel, roundType=0)
        self.tileRightBottom, tileRightBottom_tmp = self.__latlon2tile(self.maxLon, self.minLat, self.zoomLevel, roundType=1)

        tilePathList = self.__layer2Tile()

        self.updateProgress.emit()

        input_ch = 4 * len(tilePathList)
        target_ch = 4

        pix2pix = pix2pixRun(self.maxLon, self.minLon, self.maxLat, self.minLat, self.zoomLevel,
                             self.tileLeftTop[0], self.tileRightBottom[0], self.tileLeftTop[1], self.tileRightBottom[1],
                             self.pix2pixModel, self.outputPath, self.layerName, self.workspace, input_ch, target_ch, tilePathList,
                             tileLeftTop_tmp, tileRightBottom_tmp, self.pix2pixParam)

        Mess = ''

        re1 = pix2pix.pix2pixOutput_datasetMake()
        if re1["status"]:
            self.updateProgress.emit()
            re2 = pix2pix.pix2pixOutput_pix2pixRun()
        else:
            re2 = re1

        if re2["status"]:
            self.updateProgress.emit()
            re3 = pix2pix.pix2pixOutput_imageOutput()
        else:
            re3 = re2

        if re3["status"]:
            self.updateProgress.emit()
            self.addLayer.emit(re3["imagePath"].decode("utf-8"), self.layerName.decode("utf-8"))

        else:
            Mess = re3["errorMess"]
            log_p = open(os.path.join(self.outputPath, 'outlog.log'), 'w')
            log_p.write(re3["out"])
            log_p.close()


        shutil.rmtree(self.workspace)

        self.processFinished.emit(re3["status"], Mess)

    def stop(self):
        self.mutex.lock()
        self.stopMe = 1
        self.mutex.unlock()
        QtCore.QThread.wait(self)

    def __tile2latlon(self, x, y, z):
        lon = (x / 2.0**z) * 360 - 180 # 経度（東経）
        mapy = (y / 2.0**z) * 2 * math.pi - math.pi
        lat = 2 * math.atan(math.e ** (- mapy)) * 180 / math.pi - 90 # 緯度（北緯）
        return [lon,lat]

    def __latlon2tile(self, lon, lat, z, roundType=0):
        x_tmp = ((lon / 180 + 1) * 2**z / 2) # x座標
        y_tmp = (((-math.log(math.tan((45 + lat / 2) * math.pi / 180)) + math.pi) * 2**z / (2 * math.pi))) # y座標
        if roundType == 0:
            x = int(math.floor(x_tmp))
            y = int(math.floor(y_tmp))
        elif roundType == 1:
            x = int(math.ceil(x_tmp))
            y = int(math.ceil(y_tmp))

        return [x,y], [x_tmp-x, y_tmp-y]

    def __layer2Tile(self):
        selectLayersList = self.selectLayersList

        tilePathList = []
        for layerNum, selectLayer in enumerate(selectLayersList):
            layerId = self.layersIdList[selectLayer.text()]
            layer = QgsMapLayerRegistry.instance().mapLayer(layerId)

            if not os.path.isdir(os.path.join(self.workspace, 'inputTiles', str(layerNum))):
                os.makedirs(os.path.join(self.workspace, 'inputTiles', str(layerNum)))

            tilePathFormat = {'path':os.path.join(self.workspace, 'inputTiles', str(layerNum)).decode("utf-8"),
                              'type':'localTile',
                              'format':'{z}/{x}/{y}.png'
                              }
            tilePathList.append(tilePathFormat)

            for i in range(self.tileLeftTop[0], self.tileRightBottom[0]+1):
                for j in range(self.tileLeftTop[1], self.tileRightBottom[1]+1):
                    tileLeftTop_lonlat = self.__tile2latlon(i, j, self.zoomLevel)
                    tileRightBottom_lonlat = self.__tile2latlon(i+1, j+1, self.zoomLevel)

                    tileExtent = QgsRectangle(tileLeftTop_lonlat[0], tileRightBottom_lonlat[1], tileRightBottom_lonlat[0], tileLeftTop_lonlat[1])
                    tileOutputPath = os.path.join(self.workspace, 'inputTiles', str(layerNum),  str(self.zoomLevel), str(i), str(j) + '.png').decode("utf-8")

                    self.__tileOutput(layer, tileOutputPath, tileExtent)


        return tilePathList

    def __tileOutput(self, layer, tileOutputPath, tileExtent):
        #self.iface.actionHideAllLayers().trigger() # make all layers invisible
        #self.iface.legendInterface().setLayerVisible(layer, True)
        # create image

        if not os.path.isdir(os.path.dirname(tileOutputPath)):
            os.makedirs(os.path.dirname(tileOutputPath))

        img = QtGui.QImage(QtCore.QSize(256,256), QtGui.QImage.Format_ARGB32_Premultiplied)

        # set image's background color
        color = QtGui.QColor(255,255,255, 0)
        img.fill(color.rgba())

        # create painter
        p = QtGui.QPainter()
        p.begin(img)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        render = QgsMapRenderer()

        # set layer set
        lst = [ layer.id() ]  # add ID of every layer
        render.setLayerSet(lst)

        # Set destination CRS to match the CRS of the first layer
        destCrs = QgsCoordinateReferenceSystem(3857, QgsCoordinateReferenceSystem.EpsgCrsId)
        render.setDestinationCrs(destCrs)
        # Enable OTF reprojection
        render.setProjectionsEnabled(True)

        # set extent
        rect = tileExtent
        rect.scale(1)
        srcCrs = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
        rect = QgsCoordinateTransform(srcCrs, destCrs).transform(rect)
        render.setExtent(rect)

        # set output size
        render.setOutputSize(img.size(), img.logicalDpiX())

        # do the rendering
        render.render(p)

        p.end()

        # save image
        img.save(tileOutputPath,"png")


