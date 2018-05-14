# coding: utf-8

import argparse

def main():
    parser = argparse.ArgumentParser (
        prog='AIS, GPS Timestamp Matching',
        usage='AISデータとGPSデータのタイムスタンプを一致させるプログラム',
        description='python3 TimestampMatching.py [input AIS filepath] [input GPS filepath] [output filepath]',
        epilog='Copyright 2018 Daisuke Zenju',
        add_help=True
        )

    parser.add_argument('-a', '--ais', help='Input AIS filepath')
    parser.add_argument('-g', '--gps', help='Input GPS filepath')
    parser.add_argument('-o', '--output', help='Output filepath')
    parser.add_argument('-t', '--timestamp', help='(Option) Insert Timestamp', action='store_true')
    args = parser.parse_args()

    # 引数読込(AISファイル名, GPSファイル名, 出力ファイル名)
    input_ais_file = args.ais
    input_gps_file = args.gps
    output_file = args.output

    # AIS, GPSデータファイル読込
    ais_file = open(input_ais_file, 'r')
    gps_file = open(input_gps_file, 'r')
    ais_row = ais_file.readlines()
    gps_row = gps_file.readlines()

    # AIS list
    ais_list = []
    for ais_line in ais_row:
        ais_split = ais_line.split(' ')
        msg = ais_split[2].split(',')
        timestamp = ais_split[0].replace('[', '') + ' ' + ais_split[1].replace(']', '')
        ais_split = [timestamp + ' ' + msg[0] , msg, timestamp]
        ais_list.append(ais_split)
    
    # GPS dict
    gps_data = {}
    for gps_line in gps_row:
        gps_split = gps_line.split(' ')
        msg = gps_split[2].split(',')
        timestamp = gps_split[0].replace('[', '') + ' ' + gps_split[1].replace(']', '')
        gps_data[timestamp + ' ' + msg[0]] = msg

    # Output list & AIS, GPS Match
    output_data = []
    for ais_l in ais_list:
        if ais_l[1][0] != '!AIVDM':
            if ais_l[0] in gps_data.keys():
                ais_l[1] = gps_data[ais_l[0]]
        output_data.append([ais_l[0], ais_l[1], ais_l[2]])
    
    output = open(output_file, 'w')
    for out in output_data:
        txt = ''
        for t in out[1]:
            txt += t + ','
        txt = txt[:-1]

        ## どちらか
        if args.timestamp:
            output.write('[' + out[2] + '] ' + txt)
        else:
            output.write(txt)
    output.close()
        


if __name__ == '__main__':
    main()