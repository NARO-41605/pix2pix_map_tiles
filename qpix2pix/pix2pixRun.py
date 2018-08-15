# -*- coding: utf-8 -*

from PIL import Image
import os
import json
import commands
import glob
import re
import shutil
import codecs

TILE_SIZE = 256

class pix2pixRun:
    def  __init__(self, maxLon, minLon, maxLat, minLat, zoomLevel, start_x, end_x, start_y, end_y,
                    pix2pixModel, outputPath, layerName, workspace, input_ch, target_ch, tilePathList,
                    start_dif, end_dif, param):

        self.maxLon = maxLon
        self.minLon = minLon
        self.maxLat = maxLat
        self.minLat = minLat
        self.start_x = start_x
        self.end_x = end_x
        self.start_y = start_y
        self.end_y = end_y
        self.zoomLevel = zoomLevel

        self.input_ch = input_ch
        self.target_ch = target_ch

        self.pix2pixModel = pix2pixModel
        self.outputPath = outputPath
        self.layerName = layerName
        self.workspace = workspace

        self.tilePathList = tilePathList

        self.start_dif = start_dif
        self.end_dif = end_dif

        self.param = param

        self.mypath = os.path.dirname(os.path.abspath(__file__))


    def _datasetMake(self, bsFlg=False):

        json_dict = {"targetURL" : None, "inputURL" : self.tilePathList}

        jsonPath = os.path.join(self.workspace, 'jsonData.txt')
        with codecs.open(jsonPath,'w','utf-8') as json_fp:
            json_str = json.dumps(json_dict, ensure_ascii=False)
            json_fp.write(json_str)
            json_fp.close()

        datasetPath = os.path.join(self.workspace, 'dataset')
        os.makedirs(datasetPath)

        if not bsFlg:
            cmd = ('python ' + os.path.join(self.mypath, './pix2pix/DataSetMake_tfwiter_result.py ' +
                    str(self.start_x) + ' ' + str(self.end_x) + ' ' + str(self.start_y) + ' ' + str(self.end_y) + ' ' + str(self.zoomLevel) +
                    ' --inputJson ' + jsonPath + ' --outputPath ' + datasetPath))
        else:
            cmd = ('python ' + os.path.join(self.mypath, './pix2pix/DataSetMake_tfwiter_result_bs.py ' +
                    str(self.start_x) + ' ' + str(self.end_x) + ' ' + str(self.start_y) + ' ' + str(self.end_y) + ' ' + str(self.zoomLevel) +
                    ' --inputJson ' + jsonPath + ' --outputPath ' + datasetPath))

        out = commands.getstatusoutput(cmd)

        datasetsList = glob.glob(os.path.join(datasetPath, "*.tfrecords"))

        outMess = cmd + '\n\n' + out[1]

        return outMess, len(datasetsList), datasetPath

    def pix2pixOutput_datasetMake(self):
        os.chdir(self.workspace)
        out, datasets_num, datasetPath = self._datasetMake()
        if datasets_num == 0:
            return {"status": False, "errorMess": 'Error : dataset is none.', "out":out}
        else:
            self.datasetPath = datasetPath
            return {"status": True, "errorMess": ''}

    def pix2pixOutput_pix2pixRun(self):
        os.chdir(self.workspace)
        outputPath = os.path.join(self.workspace, 'result')
        cmd = ('python ' + os.path.join(self.mypath, './pix2pix/pix2pix_multi_result.py --mode test --input_dir ' + self.datasetPath +
                                        ' --output_dir ' + outputPath + ' --checkpoint ' + self.pix2pixModel +
                                        ' --input_ch ' + str(self.input_ch) + ' --target_ch ' + str(self.target_ch) +
                                        ' --GPUdevice ' + str(self.param['GPUdevice'])))
        out = commands.getstatusoutput(cmd)
        outputImgList = glob.glob(os.path.join(outputPath, "images/*-outputs.png"))

        outMess = cmd + '\n\n' + out[1]

        if len(outputImgList) == 0:
            return {"status": False, "errorMess": 'Error : pix2pix no output.\noutput "outlog.log" in output directory.', "out":outMess}
        else:
            self.outputImgList = outputImgList
            return {"status": True, "errorMess": ''}

    def pix2pixOutput_imageOutput(self):
        os.chdir(self.workspace)
        imageSize_x = (self.end_x - self.start_x + 1) * TILE_SIZE
        imageSize_y = (self.end_y - self.start_y + 1) * TILE_SIZE
        resultImage = Image.new('RGBA', (imageSize_x, imageSize_y), (0, 0, 0, 0))
        for outputImg in self.outputImgList:
            imagename = os.path.basename(outputImg)
            r = re.compile("(\d+)_(\d+)_(\d+)_(\d+)-outputs\.png")
            m = r.search(imagename)

            outputImg_p = Image.open(outputImg)
            resultImage.paste(outputImg_p, ((int(m.group(2)) - self.start_x) * TILE_SIZE, (int(m.group(3)) - self.start_y) * TILE_SIZE))

            tileDir = os.path.join(self.outputPath, 'tileImages', m.group(4), m.group(2))
            if not os.path.isdir(tileDir):
                os.makedirs(tileDir)
            outputImg_p.save(os.path.join(tileDir, m.group(3) + '.png'))

        resultImagePath = os.path.join(self.outputPath, self.layerName + '.tif')
        imageSize_x_re = imageSize_x + ((self.end_dif[0] - 1.0) * TILE_SIZE) - (self.start_dif[0] * TILE_SIZE)
        imageSize_y_re = imageSize_y + ((self.end_dif[1] - 1.0) * TILE_SIZE) - (self.start_dif[1] * TILE_SIZE)
        resultImage = resultImage.crop((int(self.start_dif[0] * TILE_SIZE), int(self.start_dif[1] * TILE_SIZE),
                                        int(imageSize_x_re + (self.start_dif[0] * TILE_SIZE)), int(imageSize_y_re + (self.start_dif[1] * TILE_SIZE))))
        resultImage.save(resultImagePath)

        tfw_p = open(os.path.join(self.outputPath, self.layerName + '.tfw'), 'w')
        tfw_p.write(str((self.maxLon - self.minLon) / imageSize_x_re) + '\n')
        tfw_p.write(str(0) + '\n')
        tfw_p.write(str(0) + '\n')
        tfw_p.write(str((self.minLat - self.maxLat) / imageSize_y_re) + '\n')
        tfw_p.write(str(self.minLon) + '\n')
        tfw_p.write(str(self.maxLat) + '\n')
        tfw_p.close()

        return {"status": True, "errorMess": '', "imagePath" : resultImagePath}












