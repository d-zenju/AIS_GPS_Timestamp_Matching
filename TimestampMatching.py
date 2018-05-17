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
    parser.add_argument('-n', '--nmea', help='Input NMEA(AIS and GPS) filepath')
    parser.add_argument('-o', '--output', help='Output filepath')
    parser.add_argument('-t', '--timestamp', help='(Option) Insert Timestamp', action='store_true')
    parser.add_argument('-j', '--json', help='(Option) AIS Decode for JSON', action='store_true')
    parser.add_argument('-c', '--csv', help='(Option) AIS Decode for CSV', action='store_true')
    args = parser.parse_args()

    # 引数読込(AISファイル名, GPSファイル名)
    if args.ais and args.gps:
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

    # 引数読込(NMEAファイル名)
    if args.nmea:
        input_nmea_file = args.nmea
        print('NMEA Filepath : ' + input_nmea_file)
        nmea_file = open(input_nmea_file, 'r')
        nmea_data = nmea_file.readlines()
        output_data = []
        for ndat in nmea_data:
            msg = ndat.split(',')
            ins = ['', msg]
            output_data.append(ins)
            
    # 引数読込(OUTPUTファイル名)
    output_file = args.output

    # AIS Decode & Output
    if args.json:
        print('OUTPUT(JSON) Filepath : ' + output_file + '[_types] and [_mmsi].json')
        ais_data = ais_decode(output_data)
        ais_decode_output(output_file, ais_data, 'json')
    elif args.csv:
        print('OUTPUT(CSV) Filepath : ' + output_file + '_type[number].csv')
        ais_data = ais_decode(output_data)
        ais_decode_output(output_file, ais_data, 'csv')
    else:
        if not args.nmea:
            if args.timestamp:
                print('OUTPUT(Timestamp, NMEA) Filepath : ' + output_file + '_t.txt')
            else:
                print('OUTPUT(NMEA) Filepath : ' + output_file + '.nmea')
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
    if timestamp_flag:
        output_file += '_t.txt'
    else:
        output_file += '.nmea'

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
    utc = 'xxxxxx'
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
            utc = data[1][1][:6]
    
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


if __name__ == '__main__':
    main()