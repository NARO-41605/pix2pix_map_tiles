# pix2pix for Map tiles
In this repository, we release various programs for image conversion using [pix2pix-tensorflow](https://github.com/affinelayer/pix2pix-tensorflow) for map tile images published on the web .

## Operating environment
The operating environment is below. 

| Category | version |
----|---- 
| OS | Ubuntu 16.04 LTR 64bit |
| Framework | Python 2.7.12 |
|  | tensorflow 1.0.0 |
|  | CUDA 8.0.61 (for GPU Environment) |
|  | CuDNN V5.1 (for GPU Environment) |

## Installation
1. Install required packages

~~~
sudo apt-get update
sudo apt-get install python-pip python-dev libfreetype6-dev pkg-config liblapack-dev gfortran libtiff5-dev libjpeg8-dev zlib1g-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk python-scipy

sudo pip install \
    appdirs==1.4.0 \
    funcsigs==1.0.2 \
    google-api-python-client==1.6.2 \
    google-auth==0.7.0 \
    google-auth-httplib2==0.0.2 \
    google-cloud-core==0.22.1 \
    google-cloud-storage==0.22.0 \
    googleapis-common-protos==1.5.2 \
    httplib2==0.10.3 \
    mock==2.0.0 \
    numpy==1.12.0 \
    oauth2client==4.0.0 \
    packaging==16.8 \
    pbr==1.10.0 \
    protobuf==3.2.0 \
    pyasn1==0.2.2 \
    pyasn1-modules==0.0.8 \
    pyparsing==2.1.10 \
    rsa==3.4.2 \
    six==1.10.0 \
    uritemplate==3.0.0 \
    requests\
    cython\
    pandas\
    scikit-image\
    pillow
~~~

2. Install Tensorflow

* No GPU Environment
~~~
sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow-1.0.0-cp27-none-linux_x86_64.whl
~~~

* With GPU Environment
~~~
sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-1.0.0-cp27-none-linux_x86_64.whl
~~~

3. Coty `DataSetMake_tfwiter.py` and `pix2pix_multi.py` to 

Then, you can use programes. 

## How to use
### Set a Map tile fetching URL

First, You have to create JSON format file whicn include URL of fetching Map tile. A format of JSON file is below. 
~~~
{
 "targetURL": {URL of target map tile}
, 
 "inputURL": [
               {URL of training map tile 1}
              , 
               {URL of training map tile 2}
             ]
}

~~~

| Parameter | Discription |
----|---- 
| "targetURL" | URL of target map tile |
| "inputURL" | URL of training map tile. It is possible to set multipule URL in the "[ ]" divided by "," .　|

Fromat of URL of fetching tile is below.

~~~
{
"url": base URL of fetching tile, 
 "type": type of map tile, 
 "format": format and parameter for fetching tile 
}
~~~

| Parameter | Discription |
----|---- 
| "url" | Base URL of fetching tile |
| "type" | Type of map tile. If you use WMST or "Map tile", set "tile". You can also set "wms" for OGS WMS Standard |
| "format" | Setting for extention, tile address, parapeter for WMTS and WMS. Detail of setting, please refer setting samples in below. |


#### Example for fetching tiled map format (GSI Japanese Aerial Photo (seamless))
~~~
{
"url": "http://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/", 
 "type": "tile", 
 "format": "{z}/{x}/{y}.jpg"
}
~~~
* "format" for map tile type, plese set the tile coordinate oder (for example, {z}/{x}/{y}, {z}/{y}/{x}...), extention of tile, parameter of WMST and other. Please referr discripton of map tile provider.



#### Example for fetching WMS map tile (J-SHIS Land slide map WMS Service)
~~~
{
"url": "http://www.j-shis.bosai.go.jp/map/wms/landslide?", 
"type": "wms", 
"format": "SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={minx},{miny},{maxx},{maxy}&CRS=EPSG:4612&WIDTH={output_width}&HEIGHT={output_height}&LAYERS=L-V3-S300&FORMAT=image/png&TRANSPARENT=FALSE"
}
~~~
* "format" for WMS service, please set WMS request parameter. Please referr discripton of map tile provider.
* BBOX, WIDHT and HEIGHT in WMS request, please set below.
~~~
 BBOX={minx},{miny},{maxx},{maxy}
 WIDTH={output_width}
 HEIGHT={output_height}
~~~

### Make training data set
`DataSetMake_tfwiter.py` is used to create training data set. Parameters are below.

~~~
python DataSetMake_tfwiter.py "images_x_start" "images_x_end" "images_y_start" "images_y_end" "zoom_level"
                              --inputJson "INPUTJSON"
                              --outputPath "OUTPUTPATH"
~~~
| Parameter | Discription |
----|---- 
| "images_x_start" | The address of the x direction of the tile which is the start of the fetching area |
| "images_x_end" | The address of the x direction of the tile which is the end of the fetching area | |
| "images_y_start" | The address of the y direction of the tile which is the start of the fetching area | |
| "images_y_end" | The address of the x direction of the tile which is the end of the fetching area | |
| --inputJson "INPUTJSON" | Specify the json format file with the URL to get the map tile. The default is ". /jsonSample.txt"|
| --outputPath "OUTPUTPATH" | Specify the output directory of the dataset. If there is no directory, it will be generated automatically. The default is "Data". |

* During execution, the original URL of the tile, the number of channels of input data (input channel), the number of channels of supervisor data (target channel), etc. are displayed. The number of each channel is input at the time of executing `pix2pix_multi.py`.
* After execution, the number of tiles in the directory specified by --outputPath will be generated by {sequential number}.tfrecords. Also, input_image{sequential number}.png and target_image{sequential number}.png are generated by connecting the acquired tiles in the directory where the program was executed.

### Implementing the training
The training is performed using `pix2pix_multi.py`. The execution format and main parameters are as follows

~~~
pix2pix_multi.py  --input_dir "INPUT_DIR" 
                  --mode {train,test,export} 
                  --output_dir "OUTPUT_DIR"
                  --checkpoint "CHECKPOINT"
                  --max_steps "MAX_STEPS"
		  --max_epochs "MAX_EPOCHS"
                  --progress_freq "PROGRESS_FREQ"
		  --save_freq "SAVE_FREQ"
		  --ngf "NGF"
                  --input_ch "INPUT_CH"
		  --target_ch "TARGET_CH"
		  --GPUdevice "GPUDEVICE"		  
~~~
| Parameter | Discription |
----|----
| --input_dir| 学習用データセットがあるディレクトリ。 |
| --mode |プログラムの実行モード。学習をする際には、"train"を指定。 |
| --output_dir | モデルの出力先ディレクトリ |
| --checkpoint | 読み込む学習済みモデルがあるディレクトリ。指定しない場合、新規で学習を行なう。 |
| --max_epochs | 学習回数|
| --progress_freq | 学習時に学習状況を表示するステップ数。デフォルトは50 |
| --save_freq | モデルを保存するステップ数。デフォルトは100。 |
| --ngf | 生成器の第一層のフィルター数。デフォルトは64。 |
| --ndf | 判別器の第一層のフィルター数。デフォルトは64。 |
| --input_ch | 入力データのチャンネル数。デフォルトは4。 |
| --target_ch | 教師データのチャンネル数。デフォルトは4。 |
| --GPUdevice | 実行するGPUの番号を指定します。デフォルトは0。複数のGPUがあるマシンを使用する場合に任意のGPUを指定して実行します。GPUがない場合はCPUを使用して実行されます。 |

* 実行中に`--save_freq`で指定したステップごとに指定した保存先に学習モデル `model-{ステップ数}.data -00000-of-00001、model-{ステップ数}.index、model-{ステップ数}.meta` が出力されます。

### Reference
This script is based on [pix2pix-tensorflow](https://github.com/affinelayer/pix2pix-tensorflow). For more information about the  program, see the distribution page of the underlying program.

We have also uploaded a sample study of the Ministry of the Environment's vegetation map to [lad2veg](https://github.com/NARO-41605/pix2pix_map_tiles/tree/master/lad2veg) using images from LANDSAT No. 7 and Geographical Survey map PNG elevation tiles. The results of `--mode test` can be viewed at https://naro-41605.github.io/pix2pix_map_tiles/lad2veg/output/index.html.
