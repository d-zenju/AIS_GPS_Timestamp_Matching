# coding: utf-8

import argparse
import ais
import json
import csv

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
    parser.add_argument('-d', '--decode', help='(Option) AIS Decode', action='store_true')
    parser.add_argument('-c', '--csv', help='(Option) Output Format CSV [AIS Decode]', action='store_true')
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

    # AIS, GPS Timestamp Matching
    output_data = timestamp_matching(ais_row, gps_row)

    # AIS Decode & Output
    if args.decode:
        ais_data = ais_decode(output_data)
        ais_decode_output(output_file, ais_data, args.csv)
    else:
        aisgps_output(output_file, output_data, args.timestamp)


# AIS, GPS Timestamp Matching
def timestamp_matching(ais_row, gps_row):
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
    
    return output_data


# AIS, GPS Output (to File)
def aisgps_output(output_file, output_data, timestamp_flag):
    output = open(output_file, 'w')
    for out in output_data:
        txt = ''
        for t in out[1]:
            txt += t + ','
        txt = txt[:-1]

        ## どちらか
        if timestamp_flag:
            output.write('[' + out[2] + '] ' + txt)
        else:
            output.write(txt)
    output.close()


# AIS Decode (dict : key[Message Type], value[Message])
def ais_decode(output_data):
    utc = '120000'
    msg = ''
    flag = 0
    length = 0
    ais_data = {}
    for data in output_data:
        if data[1][0] == '!AIVDM':
            if data[1][1] == '1':
                msg = data[1][5]
                length = 0
            else:
                if flag == 0:
                    msg = data[1][5]
                    flag = 1
                else:
                    msg += data[1][5]
                    flag = 0
                    length = 2
            if flag == 0:
                try:
                    decode = ais.decode(msg, length)
                    decode['utc'] = utc
                    # Message Type ID
                    if decode['id'] < 4:
                        decode['type'] = 123
                    else:
                        decode['type'] = decode['id']
                    
                    if decode['type'] in ais_data:
                        ais_data[decode['type']].append(decode)
                    else:
                        ais_data[decode['type']] = [decode]
                except:
                    continue
        else:
            # '$GPGGA, $GPRMC --> UTC Time'
            utc = data[1][1][:6]
    
    return ais_data


# AIS Decode Output
def ais_decode_output(output_file, ais_data, csv_flag):
    if csv_flag:
        if 123 in ais_data:
            output_file += '_type123.csv'
            header = []

    else:
        output_file += '.json'
        output = open(output_file, 'w')
        json.dump(ais_data, output)
        output.close()


if __name__ == '__main__':
    main()