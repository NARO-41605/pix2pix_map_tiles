# LANDSAT2Vegetatin

LANDSAT7および地理院標高PNGタイルを学習データとし、環境省植生図を分類したサンプル。ズームレベルは12。

LANDSAT7：産総研landbrowser http://landbrowser.geogrid.org/landbrowser/index.html

地理院PNG標高タイル：https://maps.gsi.go.jp/development/demtile.html

環境省植生図：エコリス地図タイル　http://map.ecoris.info/

実行したコマンドは以下の通り

~~~
python DataSetMake_tfwiter.py 3635 3648 1600 1613 12 --outputPath train --inputJson jsonVege.txt
python pix2pix_multi.py --mode train --max_epochs 200 --input_dir train --input_ch 20 --target_ch 4 --output_dir classify --GPUdevice 0
python pix2pix_multi.py --mode test --output_dir output --input_dir train --checkpoint classify --input_ch 20 --target_ch 4
~~~
