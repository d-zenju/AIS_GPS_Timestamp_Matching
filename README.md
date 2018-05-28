# AIS GPS Timestamp Matching
## Daisuke ZENJU

### AISのログデータに含まれるGPSデータを、別のGPSのログデータと置き換えるプログラム.

---

## 前提条件
* AISのログデータにGPSの信号($GPRMC, $GPGGA)が受信できていない.
* GPSのログデータを別途受信している.
* AIS, GPS, 共にタイムスタンプを記録している. (フォーマットは "minicom" のタイムスタンプ)

## やってること
AISの受信を開始するとAISの信号と共に, 1秒ごとに適当なGPSの信号が出力される.  これだとAISを受信した時刻が分からなくなる為, 別のGPSを受信しておき, AISとGPSのデータにタイムスタンプを記録しておく.  後ほどAISログに含まれるGPSデータを, タイムスタンプをもとに本物のGPSデータと置き換える.

## Raspberry Piでログを取得しよう
### 事前準備
1. Raspberry Piをインターネットに接続して起動する.
2. ```sudo apt-get install minicom screen```を実行する.
3. AIS, GPSのシリアルケーブル(USB)をRaspberry Piに挿し込む. なお, 入れる順番でポート名が変わるので注意. ここではAISのUSBポートを "/dev/ttyUSB0", GPSのUSBポートを "/dev/ttyUSB1"とする.
4. ```sudo minicom -s```で minicomを起動する.
5. "画面とキーボード", "コマンドのためのキー" を選択し, "^B"と入力する. これをしないと ```screen``` を使った時に支障が出る.
6. "シリアルポート" を選択し, 下記の通りに設定して, 設定を保存する. どちらか, もしくはどちらも名前をつけて保存すること.

| - | AIS | GPS |
| --- | --- | --- |
| シリアルデバイス | /dev/ttyUSB0 | /dev/ttyUSB1 |
| 速度/パリティ/ビット | 38400 8N1 | 4800 8N1 |
* 使用デバイス(AIS): AMEC CYPHO-101 G AIS RECEIVER
* 使用デバイス(GPS): G-STAR IV BR-366S4


### ログの取り方 (USBメモリ推奨)
1. Raspberry Piを起動する.
2. Raspberry PiにLANケーブル, USBメモリをつなげる.
3. Windowsなら"TeraTerm", Mac等なら"Terminal"から, 次のコマンドを実行する.   
```ssh pi@raspberrypi.local```   
パスワードは初期設定の場合は```raspberry```である.
4. ```cd /media/pi/[USBメモリのパス]```を入力し, USBメモリのディレクトリに移動する.
5. ```screen```コマンドを実行し, そのままEnterキーを押す.
6. AISのUSBポートを接続後, ```sudo minicom [AISの設定名]```を実行する.
7. "Ctrl-B + Z" を押し, "N" を押す.
8. 再び "Ctrl-B + Z" を押し, "L" を押す. AISのログのファイル名を指定する.
9. "Ctrl-A + D" を押し, Screenを移動する.
10. ```screen```コマンドを実行し, そのままEnterキーを押す.
11. GPSのUSBポートを接続後, ```sudo minicom [GPSの設定名]```を実行する.
12. "Ctrl-B + Z" を押し, "N" を押す.
13. 再び "Ctrl-B + Z" を押し, "L" を押す. GPSのログのファイル名を指定する.
14. "Ctrl-A + D" を押し, Screenを移動する.
15. "Ctrl-A + D" でログアウトする.

### ログの止め方
1. ある程度ログが取得できたら, 3を参考にRaspberry Piにログインする.
2. ```srceen -ls```を実行して, 実行中のscreenを確認する.
3. ```screen -r [仮想番号]```を実行して, AIS受信かGPS受信のどちらかに移動する.
4. "Ctrl-B Q" を押して, minicomを終了する.
5. "Ctrl-A K"を押したのち, "Y"を押す. これでscreenをkillできる.
6. ```screen -r```を実行して, 18〜20を実行する. 
7. ```sudo halt```を実行して, Raspberry Piの電源を切る.

## AIS・GPSのログを一つにまとめよう
### はじめに
以下のライブラリを```pip3```でインストールする.
* ```pip3 install libais```
* ```pip3 install pymap3d```
* ```pip3 install argparse```
### コマンド
```python3 TimestampMatching.py [Options]```   
#### Options
* ```-a [AISファイルパス]``` : AISファイルパス(必須)
* ```-g [GPSファイルパス]``` : GPSファイルパス(必須)
* ```-o [出力ファイルパス]``` : 出力ファイルパス（拡張子は書かないこと・必須）
* ```-j``` : JSONで出力する
* ```-c``` : CSVで出力する(指定しない場合はJSONとなる)
* ```-d [スライドする日数]``` : AIS, GPSのタイムスタンプをスライドする日数. 2日後なら"-d 2", 3日前なら"-d -3"と入力する.
* ```-l``` : AIS(Type1,2,3)の緯度経度を1秒毎に補間する.
* ```-r [緯度],[経度],[高度]``` : 指定した緯度経度高度からAIS(Type1,2,3)の緯度経度までの方位(deg),仰角(deg),距離(m)を計算する. カンマ区切り, スペースなしで緯度経度高度を指定する. (```-l```が必須)
#### 例
##### AISをデコードして, JSONで出力する
```pyhton3 TimestampMatching.py -a [AISファイルパス] -g [GPSファイルパス] -o [出力ファイルパス] -j```
##### AISの緯度経度を補間して, 距離を求めて, CSVで出力する
```python3 TimestampMatching.py -a [AISファイルパス] -g [GPSファイルパス] -o [出力ファイルパス] -c -l -r 35.313034,139.783935,0```
### 注意
AIS, GPSのファイル形式は下記のようになる. ログの最初と最後が中途半端になることが多いので, よく確認すること.
```
[2018-05-11 03:50:03] !AIVDM,1,1,,B,16K2N?P001awhp`DHtka1`Nt08Av,0*03
[2018-05-11 03:50:03] !AIVDM,1,1,,B,36K2:g@00Bb0P5hDDAA=G0:t0001,0*5C
[2018-05-11 03:50:03] $GPGGA,120939.000,0000.0000,N,00000.0000,E,0,00,0.0,0.0,M,,,,0000*0E
[2018-05-11 03:50:03] $GPRMC,120939.000,V,0000.0000,N,00000.0000,E,000.0,000.0,280606,,,N*7C
```

## 別の方法でデコードしよう
Windowsの場合, [AIS_DECODER](https://www.vector.co.jp/soft/winnt/business/se508058.html)というソフトウェアがある.   
これを使うと, CSVファイルとして出力される.