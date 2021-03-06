# coding: utf-8

import argparse
import ais
import pymap3d as pm
import json
import csv
import time
import datetime

def main():
    parser = argparse.ArgumentParser (
        prog='AIS, GPS Timestamp Matching',
        usage='AISデータとGPSデータのタイムスタンプを一致させるプログラム',
        description='python3 TimestampMatching.py [input AIS filepath] [input GPS filepath] [output filepath]',
        epilog='Copyright 2018 Daisuke Zenju',
        add_help=True
        )

    parser.add_argument('-a', '--ais', help='AIS filepath')
    parser.add_argument('-g', '--gps', help='GPS filepath')
    parser.add_argument('-o', '--output', help='Output filepath')
    parser.add_argument('-d', '--day', help='Offset day; ex. 2 (+2day)')
    parser.add_argument('-j', '--json', help='AIS Decode for JSON', action='store_true')
    parser.add_argument('-c', '--csv', help='AIS Decode for CSV', action='store_true')
    parser.add_argument('-l', '--lerp', help='Calc linear interpolation for positions "lat,lng,alt"', action='store_true')
    parser.add_argument('-r', '--range', help='Calc distance between the two points, input lattitude, longitude, altitude. ex. 35,135,0')
    args = parser.parse_args()

    # 引数読込(AISファイル名, GPSファイル名)
    if args.ais and args.gps and args.output:
        input_ais_file = args.ais
        input_gps_file = args.gps

        print('AIS Filepath : ' + input_ais_file)
        print('GPS Filepath : ' + input_gps_file)

        # AIS, GPSデータファイル読込
        ais_file = open(input_ais_file, 'r')
        gps_file = open(input_gps_file, 'r')
        ais_row = ais_file.readlines()
        gps_row = gps_file.readlines()

        # AIS, GPS Timestamp Matching
        output_data = timestamp_matching(ais_row, gps_row)

        # 日時補正
        if args.day:
            offset_day = int(args.day)
        else:
            offset_day = 0

        # TimestampをGPS Time(UTC)に置換
        output_data = replace_utc(output_data, offset_day)
            
        # 引数読込(OUTPUTファイル名)
        output_file = args.output

        # AIS Decode & Output
        if args.csv:
            print('OUTPUT(CSV) Filepath : ' + output_file + '_type[number].csv')
            ais_data = ais_decode(output_data)
            ais_decode_output(output_file, ais_data, 'csv')
        else:
            print('OUTPUT(JSON) Filepath : ' + output_file + '[_types] and [_mmsi].json')
            ais_data = ais_decode(output_data)
            ais_decode_output(output_file, ais_data, 'json')
        
        # Calc linear interpotion for positoins
        if args.lerp:
            lerp = calc_lerp(ais_data)
            lerp_flag = False
            if args.range:
                base = args.range.split(',')
                lerp = calc_distance(lerp, float(base[0]), float(base[1]), float(base[2]))
                lerp_flag = True
            if args.csv:
                lerp_output(output_file, lerp, 'csv', lerp_flag)
            else:
                lerp_output(output_file, lerp, 'json', lerp_flag)
            
            if args.range:
                base = args.range.split(',')
                dist = calc_distance(lerp, float(base[0]), float(base[1]), float(base[2]))


# AIS, GPS Timestamp Matching
def timestamp_matching(ais_row, gps_row):
    # AIS list
    ais_list = []
    for ais_line in ais_row:
        ais_split = ais_line.split(' ')
        msg = ais_split[2].split(',')
        timestamp = ais_split[0].replace('[', '') + ' ' + ais_split[1].replace(']', '')
        ais_split = [timestamp + ' ' + msg[0] , msg]
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
    flag = 0
    for ais_l in ais_list:
        if ais_l[1][0] != '!AIVDM':
            if ais_l[0] in gps_data.keys():
                ais_l[1] = gps_data[ais_l[0]]
                flag += 1
        if flag != 0:
            output_data.append([ais_l[0], ais_l[1]])

    return output_data


# Replace UTC Time and Offset day
def replace_utc(datas, offset_day):
    output_data = []
    timestamp = datetime.datetime(
        int(datas[0][0][:4]),
        int(datas[0][0][5:7]),
        int(datas[0][0][8:10]),
        int(datas[0][0][11:13]),
        int(datas[0][0][14:16]),
        int(datas[0][0][17:19])
    )
    diff_time = 0
    diff_day = datetime.timedelta(days=offset_day)

    for data in datas:
        if diff_time == 0:
            if data[1][0] == '$GPRMC' or data[1][0] == '$GPGGA':
                utc_time = datetime.datetime(
                    int(data[0][:4]),
                    int(data[0][5:7]),
                    int(data[0][8:10]),
                    int(data[1][1][:2]),
                    int(data[1][1][2:4]),
                    int(data[1][1][4:6])
                )
                stamp_time = datetime.datetime(
                    int(data[0][:4]),
                    int(data[0][5:7]),
                    int(data[0][8:10]),
                    int(data[0][11:13]),
                    int(data[0][14:16]),
                    int(data[0][17:19])
                )
                diff_time = utc_time - stamp_time
        else:
            if data[1][0] == '$GPRMC' or data[1][0] == '$GPGGA':
                stamp_time = datetime.datetime(
                    int(data[0][:4]),
                    int(data[0][5:7]),
                    int(data[0][8:10]),
                    int(data[0][11:13]),
                    int(data[0][14:16]),
                    int(data[0][17:19])
                )
                timestamp = stamp_time + diff_time + diff_day
            data[0] = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            output_data.append(data)
    output_data = sorted(output_data)
    return output_data


# Offset Date
def offset_date(datas, date_offset):
    output_data = []
    diff_time = date_offset - stamp_time
    print(diff_time)
    for data in datas:
        stamp_time = datetime.datetime(
            int(data[0][:4]),
            int(data[0][5:7]),
            int(data[0][8:10]),
            int(data[0][11:13]),
            int(data[0][14:16]),
            int(data[0][17:19])
        )
        timestamp = stamp_time + diff_time
        data[0] = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        output_data.append(data)
    output_data = sorted(output_data)
    return output_data


# AIS, GPS Output (to File)
def aisgps_output(output_file, output_data):
    output = open(output_file + '.nmea', 'w')
    for out in output_data:
        msg = str(out[1])
        msg = msg.replace('[', '')
        msg = msg.replace(']', '')
        msg = msg.replace(' ', '')
        output.write(str(out[0]) + ' ' + msg + '\n')
    output.close()


# AIS Decode (dict : key[Message Type], value[Message])
def ais_decode(output_data):
    utc = ''
    msg = ''
    flag = 0
    length = 0
    ais_data = {}

    station_types = {
        0: 'All types of mobiles',
        1: 'Reserved for future use',
        2: 'All types of Class B mobile stations',
        3: 'SAR airborne mobile station',
        4: 'Aid to Navigation station',
        5: 'Class B shipborne mobile station (IEC62287 only)',
        6: 'Regional use and inland waterways',
        7: 'Regional use and inland waterways',
        8: 'Regional use and inland waterways',
        9: 'Regional use and inland waterways',
        10: 'Reserved for future use',
        11: 'Reserved for future use',
        12: 'Reserved for future use',
        13: 'Reserved for future use',
        14: 'Reserved for future use',
        15: 'Reserved for future use'}

    aton_types = {
        0: 'Default, Type of Aid to Navigation not specified',
        1: 'Reference point',
        2: 'RACON (radar transponder marking a navigation hazard)',
        3: 'Fixed structure off shore, such as oil platforms, wind farms, rigs.',
        4: 'Spare, Reserved for future use.',
        5: 'Light, without sectors',
        6: 'Light, with sectors',
        7: 'Leading Light Front',
        8: 'Leading Light Rear',
        9: 'Beacon, Cardinal N',
        10: 'Beacon, Cardinal E',
        11: 'Beacon, Cardinal S',
        12: 'Beacon, Cardinal W',
        13: 'Beacon, Port hand',
        14: 'Beacon, Starboard hand',
        15: 'Beacon, Preferred Channel port hand',
        16: 'Beacon, Preferred Channel starboard hand',
        17: 'Beacon, Isolated danger',
        18: 'Beacon, Safe water',
        19: 'Beacon, Special mark',
        20: 'Cardinal Mark N',
        21: 'Cardinal Mark E',
        22: 'Cardinal Mark S',
        23: 'Cardinal Mark W',
        24: 'Port hand Mark',
        25: 'Starboard hand Mark',
        26: 'Preferred Channel Port hand',
        27: 'Preferred Channel Starboard hand',
        28: 'Isolated danger',
        29: 'Safe Water',
        30: 'Special Mark',
        31: 'Light Vessel / LANBY / Rigs'}

    fix_types = {
        0: 'Undefined',
        1: 'GPS',
        2: 'GLONASS',
        3: 'Combined GPS/GLONASS',
        4: 'Loran-C',
        5: 'Chayka',
        6: 'Integrated navigation system',
        7: 'Surveyed',
        8: 'Galileo'}

    # Match the output of gpsd 3.11.
    nav_statuses = {
        0: 'Under way using engine',
        1: 'At anchor',
        2: 'Not under command',
        3: 'Restricted manoeuverability',  # Maneuverability.
        4: 'Constrained by her draught',
        5: 'Moored',
        6: 'Aground',
        7: 'Engaged in fishing',
        8: 'Under way sailing',
        # Reserved for future amendment of navigational status for ships
        # carrying DG, HS, or MP, or IMO hazard or pollutant category C,
        # high speed craft (HSC).
        9: 'Reserved for HSC',
        # Reserved for future amendment of navigational status for ships
        # carrying dangerous goods (DG), harmful substances (HS) or marine
        # pollutants (MP), or IMO hazard or pollutant category A, wing in
        # ground (WIG).
        10: 'Reserved for WIG',
        # Power-driven vessel towing astern (regional use).
        11: 'Reserved',
        # Power-driven vessel pushing ahead or towing alongside (regional use).
        12: 'Reserved',
        # Reserved for future use.
        13: 'Reserved',
        # AIS-SART (active), MOB-AIS, EPIRB-AIS,
        14: 'Reserved',
        # Default (also used by AIS-SART, MOB-AIS and EPIRB-AIS under test).
        15: 'Not defined'}

    ship_types = {
        0: 'Not available',
        1: 'Reserved for future use',
        2: 'Reserved for future use',
        3: 'Reserved for future use',
        4: 'Reserved for future use',
        5: 'Reserved for future use',
        6: 'Reserved for future use',
        7: 'Reserved for future use',
        8: 'Reserved for future use',
        9: 'Reserved for future use',
        10: 'Reserved for future use',
        11: 'Reserved for future use',
        12: 'Reserved for future use',
        13: 'Reserved for future use',
        14: 'Reserved for future use',
        15: 'Reserved for future use',
        16: 'Reserved for future use',
        17: 'Reserved for future use',
        18: 'Reserved for future use',
        19: 'Reserved for future use',
        20: 'Wing in ground (WIG), all ships of this type',
        21: 'Wing in ground (WIG), Hazardous category A',
        22: 'Wing in ground (WIG), Hazardous category B',
        23: 'Wing in ground (WIG), Hazardous category C',
        24: 'Wing in ground (WIG), Hazardous category D',
        25: 'Wing in ground (WIG), Reserved for future use',
        26: 'Wing in ground (WIG), Reserved for future use',
        27: 'Wing in ground (WIG), Reserved for future use',
        28: 'Wing in ground (WIG), Reserved for future use',
        29: 'Wing in ground (WIG), Reserved for future use',
        30: 'Fishing',
        31: 'Towing',
        32: 'Towing: length exceeds 200m or breadth exceeds 25m',
        33: 'Dredging or underwater ops',
        34: 'Diving ops',
        35: 'Military ops',
        36: 'Sailing',
        37: 'Pleasure Craft',
        38: 'Reserved',
        39: 'Reserved',
        40: 'High speed craft (HSC), all ships of this type',
        41: 'High speed craft (HSC), Hazardous category A',
        42: 'High speed craft (HSC), Hazardous category B',
        43: 'High speed craft (HSC), Hazardous category C',
        44: 'High speed craft (HSC), Hazardous category D',
        45: 'High speed craft (HSC), Reserved for future use',
        46: 'High speed craft (HSC), Reserved for future use',
        47: 'High speed craft (HSC), Reserved for future use',
        48: 'High speed craft (HSC), Reserved for future use',
        49: 'High speed craft (HSC), No additional information',
        50: 'Pilot Vessel',
        51: 'Search and Rescue vessel',
        52: 'Tug',
        53: 'Port Tender',
        54: 'Anti-pollution equipment',
        55: 'Law Enforcement',
        56: 'Spare - Local Vessel',
        57: 'Spare - Local Vessel',
        58: 'Medical Transport',
        59: 'Noncombatant ship according to RR Resolution No. 18',
        60: 'Passenger, all ships of this type',
        61: 'Passenger, Hazardous category A',
        62: 'Passenger, Hazardous category B',
        63: 'Passenger, Hazardous category C',
        64: 'Passenger, Hazardous category D',
        65: 'Passenger, Reserved for future use',
        66: 'Passenger, Reserved for future use',
        67: 'Passenger, Reserved for future use',
        68: 'Passenger, Reserved for future use',
        69: 'Passenger, No additional information',
        70: 'Cargo, all ships of this type',
        71: 'Cargo, Hazardous category A',
        72: 'Cargo, Hazardous category B',
        73: 'Cargo, Hazardous category C',
        74: 'Cargo, Hazardous category D',
        75: 'Cargo, Reserved for future use',
        76: 'Cargo, Reserved for future use',
        77: 'Cargo, Reserved for future use',
        78: 'Cargo, Reserved for future use',
        79: 'Cargo, No additional information',
        80: 'Tanker, all ships of this type',
        81: 'Tanker, Hazardous category A',
        82: 'Tanker, Hazardous category B',
        83: 'Tanker, Hazardous category C',
        84: 'Tanker, Hazardous category D',
        85: 'Tanker, Reserved for future use',
        86: 'Tanker, Reserved for future use',
        87: 'Tanker, Reserved for future use',
        88: 'Tanker, Reserved for future use',
        89: 'Tanker, No additional information',
        90: 'Other Type, all ships of this type',
        91: 'Other Type, Hazardous category A',
        92: 'Other Type, Hazardous category B',
        93: 'Other Type, Hazardous category C',
        94: 'Other Type, Hazardous category D',
        95: 'Other Type, Reserved for future use',
        96: 'Other Type, Reserved for future use',
        97: 'Other Type, Reserved for future use',
        98: 'Other Type, Reserved for future use',
        99: 'Other Type, no additional information'}

    for data in output_data:
        if data[1][0] == '!AIVDM':
            if data[1][1] == '1':
                msg = data[1][5]
                length = 0
                flag = 0
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
                    decode['utc'] = data[0]
                    if 'station_type' in decode:
                        decode['station_type_text'] = station_types[decode['station_type']]

                    if 'aton_type' in decode:
                        decode['aton_type_text'] = aton_types[decode['aton_type']]

                    if 'fix_type' in decode:
                        decode['epfd_text(fix_type)'] = fix_types[decode['fix_type']]
                    
                    if 'nav_status' in decode:
                        decode['nav_status_text'] = nav_statuses[decode['nav_status']]
                    
                    if 'type_and_cargo' in decode:
                        decode['shiptype_text(type_and_cargo)'] = ship_types[decode['type_and_cargo']]

                    # Message Type ID
                    if decode['id'] < 4:
                        decode['type'] = 123
                    else:
                        decode['type'] = decode['id']
                    
                    if len(utc) > 0:
                        if decode['type'] in ais_data:
                            if utc in ais_data[decode['type']]:
                                ais_data[decode['type']][utc].append(decode)
                            else:
                                ais_data[decode['type']].update({utc : [decode]})
                        else:
                            ais_data[decode['type']] = {utc : [decode]}
                except:
                    continue
        else:
            # '$GPGGA, $GPRMC --> UTC Time'
            utc = data[0]
    
    return ais_data


# AIS Decode Output
def ais_decode_output(output_file, ais_data, filetype):
    # CSV
    if filetype == 'csv':
        
        for msgtype in ais_data.keys():
            output_file_csv = output_file + '_type' + str(msgtype) + '.csv'
            output = open(output_file_csv, 'w')
            writer = csv.writer(output)

            utc = ais_data[msgtype].keys()
            data = ais_data[msgtype].items()

            header = []
            for dat in data:
                for d in dat[1]:
                    header.extend(d.keys())
            header = sorted(list(set(header)))
            writer.writerow(header)

            for dat in data:
                for d in dat[1]:
                    row = []
                    for h in header:
                        if h in d:
                            row.append(d.get(h))
                        else:
                            row.append('')
                    
                    writer.writerow(row)

            output.close()

    # JSON
    else:
        # Types - Timestamp - Ships
        output_file_jsn = output_file + '_types.json'
        output = open(output_file_jsn, 'w')
        json.dump(ais_data, output)
        output.close()

        # MMSI - Types - Timestamp
        output_file_jsn = output_file + '_mmsi.json'
        output = open(output_file_jsn, 'w')

        mmsi = {}
        for msgtype in ais_data.keys():
            data = ais_data[msgtype].items()
            for dat in data:
                for d in dat[1]:
                    if 'mmsi' in d:
                        if not mmsi.get(d['mmsi']):
                            mmsi.update({d['mmsi']:{msgtype:{d['utc']:d}}})
                        else:
                            if msgtype in mmsi[d['mmsi']]:
                                mmsi[d['mmsi']][msgtype].update({d['utc']:d})
                            else:
                                mmsi[d['mmsi']].update({msgtype:{d['utc']:d}})
        
        json.dump(mmsi, output)
        output.close()

def calc_lerp(ais_data):
    ships = {}
    data = ais_data[123].items()
    for dat in data:
        for d in dat[1]:
            if 'mmsi' in d:
                position = {
                    'lat' : d['y'],
                    'lng' : d['x']
                }
                if not ships.get(d['mmsi']):
                    ships.update({d['mmsi']:{d['utc']:position}})
                else:
                    ships[d['mmsi']].update({d['utc']:position})
    result = {}
    for mmsi in ships.items():
        utcdatas = list(mmsi[1].keys())
        len_utc = len(utcdatas)
        if len_utc > 1:
            for i in range(len_utc - 1):
                start_time = datetime.datetime.strptime(utcdatas[i], '%Y-%m-%dT%H:%M:%SZ')
                end_time = datetime.datetime.strptime(utcdatas[i+1], '%Y-%m-%dT%H:%M:%SZ')
                start_unix = int(time.mktime(start_time.timetuple()))
                end_unix = int(time.mktime(end_time.timetuple()))
                sub_second = end_unix - start_unix
                for sec in range(sub_second):
                    now_unix = start_unix + sec
                    now_time = datetime.datetime.fromtimestamp(now_unix).strftime('%Y-%m-%dT%H:%M:%SZ')
                    lat0 = mmsi[1][utcdatas[i]]['lat']
                    lat1 = mmsi[1][utcdatas[i+1]]['lat']
                    lng0 = mmsi[1][utcdatas[i]]['lng']
                    lng1 = mmsi[1][utcdatas[i+1]]['lng']
                    lat = lat0 + (lat1 - lat0) * sec / sub_second
                    lng = lng0 + (lng1 - lng0) * sec / sub_second
                    if not result.get(mmsi[0]):
                        result[mmsi[0]] = {now_time:{'lat':lat, 'lng':lng}}
                    else:
                        result[mmsi[0]].update({now_time:{'lat':lat, 'lng':lng}})
            result[mmsi[0]].update({utcdatas[-1]:mmsi[1][utcdatas[-1]]})
        else:
            result[mmsi[0]] = mmsi[1]
    return result


def lerp_output(output_file, lerp_data, filetype, distance_flag):
    if filetype == 'csv':
        output_file_csv = output_file + '_lerp.csv'
        output = open(output_file_csv, 'w')
        writer = csv.writer(output)
        if distance_flag == True:
            header = ['MMSI', 'UTC Time', 'Latitude', 'Longitude', 'Azimuth(deg)', 'Elevation(deg)', 'Slant Range(m)']
        else:
            header = ['MMSI', 'UTC Time', 'Latitude', 'Longitude']
        writer.writerow(header)
        for dat in lerp_data.items():
            for d in dat[1]:
                if distance_flag == True:
                    line = [dat[0], d, dat[1][d]['lat'], dat[1][d]['lng'], dat[1][d]['az'], dat[1][d]['el'], dat[1][d]['range']]
                else:
                    line = [dat[0], d, dat[1][d]['lat'], dat[1][d]['lng']]
                writer.writerow(line)
        output.close()

    else:
        # MMSI - Time - Position
        output_file_jsn = output_file + '_lerp_mmsi.json'
        output = open(output_file_jsn, 'w')
        json.dump(lerp_data, output)
        output.close()

        # Time - MMSI - Position
        output_file_jsn = output_file + '_lerp_time.json'
        output = open(output_file_jsn, 'w')
        times = {}
        for dat in lerp_data.items():
            for d in dat[1]:
                if not times.get(d):
                    times.update({d:{dat[0]:{'lat':dat[1][d]['lat'], 'lng':dat[1][d]['lng']}}})
                else:
                    if dat[0] in times[d]:
                        times[d][dat[0]].update({'lat':dat[1][d]['lat'], 'lng':dat[1][d]['lng']})
                    else:
                        times[d].update({dat[0]:{'lat':dat[1][d]['lat'], 'lng':dat[1][d]['lng']}})
        json.dump(times, output)
        output.close()


def calc_distance(lerp_data, latitude, longitude, altitude):
    for dat in lerp_data.items():
        for d in dat[1]:
            az, el, dst = pm.geodetic2aer(dat[1][d]['lat'], dat[1][d]['lng'], 0, latitude, longitude, altitude)
            lerp_data[dat[0]][d].update({'az':az, 'el':el, 'range':dst})
    return lerp_data


if __name__ == '__main__':
    main()