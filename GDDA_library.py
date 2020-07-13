"""
(*) ~ ---------------------------------------------------
p.wagner@unsw.edu.au - gaze data assessment recorded with pupil, pupil-labs.com, Berlin, Germany with Camboard
pico flexx, PMD Technologies, Siegen, Germany as world camera using pico flexx plugin for pupil.

pupil version tested - 1.21-5
pico flexx plugin version -

    - time matching between lED timings and pupil gaze depth data
    - data selection from gaze_depth.csv
    - display data within field of view of pico flexx
    - display depth data at gaze point over time and present with LED distances

all times are referenced to recording start time in 'info.old_style.csv'
--------------------------------------------------------~(*)
"""

from datetime import datetime, timedelta, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, json, sys, glob


def check_source_f(folder):
    # check if all source files are available
    fns = [folder + '\\info.player.json',
           folder + '\\LED_timings.txt',
           folder + r'\exports\000\gaze_positions.csv',
           folder + r'\exports\000\pupil_positions.csv',
           folder + r'\gaze_depth.csv']

    if not all([os.path.isfile(fn) for fn in fns]):

        for fn in fns:
            if not os.path.isfile(fn):
                print(fn)

        sys.exit("Source files missing ")
    # else:
    #     print("Check_Source_f: All source files present")


def get_PL_info_old_style(folder):
    # get info for time synchronisation LED_timings, gaze_positions, point_cloud
    # # get time info of pupil labs
    # info_file = pd.read_csv(rec_folder + '\\info.old_style.csv')
    with open(folder + '\\info.player.json') as json_file:
        info_data = json.load(json_file)
        recording_start_date = datetime.strptime(info_data["recording_name"], '%Y_%m_%d')
        recording_start_time_system = float(info_data["start_time_system_s"])
        recording_start_time_synced = float(info_data["start_time_synced_s"])

             # = info_data.loc[idx, 'value'], '%d.%m.%Y')
            # if value.loc["key"] == "Start Time":
            #     recording_start_time = datetime.strptime(info_file.loc[idx, 'value'], '%H:%M:%S')
            # if value.loc["key"] == ("start_time_system_s"):
            #     recording_start_time_system = float(info_data.loc[idx, 'value'])
            # if value.loc["key"] == ("start_time_synced_s"):
            #     recording_start_time_synced = float(info_data.loc[idx, 'value'])
    return recording_start_date, recording_start_time_system, recording_start_time_synced


# get all recording locations of accuracy tests from participant_logbook
def get_acc_rec_fps(participant_logbook, participant_ID, recordings_location, accs ):
    # create data frame with acc_recs and rec_pf to get data form summary

    # accs = ['acc_rec_initial', 'acc_rec_5min', 'acc_rec_1hour']
    acc_rec_fps = pd.DataFrame(columns=['px_id', 'acc_id', 'acc_rec_fp'])
    for acc in accs:
        # if recording fp is recorded in excel, add to acc_rec_fps
        if not pd.isnull(participant_logbook.loc[acc, participant_ID]):
            for folder in participant_logbook.loc[acc, participant_ID].split(','):
                new_rec_fp = os.path.join(recordings_location, participant_logbook.loc['date', participant_ID]) + folder.strip()
                new_rec = {'px_id': participant_ID, 'acc_id': acc, 'acc_rec_fp': new_rec_fp}
                acc_rec_fps = acc_rec_fps.append(new_rec, ignore_index=True)
        else:
            continue
    return acc_rec_fps


def led_timings_in_PL_time(fp, target_distances):
    recording_start_date, recording_start_time_system, recording_start_time_synced = get_PL_info_old_style(fp);

    # # get times of LED_timings
    f = open(fp + '\\LED_timings.txt')
    lines = f.readlines()
    f.close()
    # matrix of LED timings
    led_timings = pd.DataFrame(
        columns=['time', 'led_id', 'duration', 'relative_time', 'rel_time_dec', 'target_distance'])
    # target distances top left to bottom right; index 0 not allocated
    # target_distances = pd.DataFrame(
    #     {'distance': [0, 1.00, 1.50, .70, .70, .30, .50, 1.50, .50, .50, .30, 1.00, 3.7, 2.1]})

    # record time and LED id into pd.DataFrame
    for idx, line in enumerate(lines):
        # find experiment start time
        if not line.find('Test start') == -1:
            led_timings.loc[idx, 'time'] = line.split(' ->')[0]
            led_timings.loc[idx, 'led_id'] = 13
        # find led number and start time
        if not line.find('LED') == -1:
            led_timings.loc[idx, 'time'] = line.split(' ->')[0]
            led_timings.loc[idx, 'led_id'] = int(line.split(':')[-1])
        # find end time
        if not line.find('Test end') == -1:
            led_timings.loc[idx, 'time'] = line.split(' ->')[0]
            led_timings.loc[idx, 'led_id'] = 13
        # find all control target start times
        if not line.find('Control') == -1:
            led_timings.loc[idx, 'time'] = line.split(' ->')[0]
            led_timings.loc[idx, 'led_id'] = 13

    for idx, time in led_timings.iterrows():
        # change string to datetime value
        led_timings.loc[idx, "time"] = datetime.strptime(led_timings.loc[idx, "time"], '%H:%M:%S.%f')
        led_timings.loc[idx, "time"] = led_timings.loc[idx, "time"].replace(year=recording_start_date.year)
        led_timings.loc[idx, "time"] = led_timings.loc[idx, "time"].replace(month=recording_start_date.month)
        led_timings.loc[idx, "time"] = led_timings.loc[idx, "time"].replace(day=recording_start_date.day)
        # sorting target distances to LED numbering
        led_timings.loc[idx, "target_distance"] = (target_distances.loc[led_timings.loc[idx, "led_id"], 'distance'])
    # # # time durations of LED on
    for idx, time in led_timings[:-1].iterrows():
        led_timings.loc[idx, "duration"] = led_timings.loc[idx + 1, "time"] - led_timings.loc[idx, "time"]
    # print((led_timings.loc[1, "time"]))

    # !! for observational control, match time with video timestamps from pupil player (recording start time as reference)!!
    # # relative time to LED start time
    delta_start_time = led_timings.loc[1, "time"] - datetime.fromtimestamp(recording_start_time_system)

#         delta_start_time = led_timings.loc[1, "time"] - led_timings.loc[1, "time"].replace(minute=22, second=0)

    # print(type(led_timings.loc[1, "time"]))
    led_timings.loc[:, "relative_time"] = (led_timings.loc[:, "time"]
                                           - pd.DataFrame.min(led_timings.loc[:, "time"])
                                           + delta_start_time)
    for idx, time in led_timings.iterrows():
        led_timings.loc[idx, "rel_time_dec"] = (led_timings.loc[idx, "relative_time"].total_seconds())

    return led_timings


def basic_meta_data(fp, gaze_depth_data):
    test_start_time, test_end_time, recording_start_time_synced = test_start_end_time(fp)
    # # check for missing timestamps
    # # # world_timestamps.npy vs unique ts from gaze_depth_data

    depth_data_frame_timestamps = pd.unique(gaze_depth_data["frame_timestamp"])

    world_timestamps = np.load(os.path.join(fp, 'world_timestamps.npy'))

    world_timestamps = world_timestamps - recording_start_time_synced
    world_timestamps = world_timestamps.round(6)

    # gaze_depth_data in LED presentation interval only
    world_timestamps = world_timestamps[world_timestamps > test_start_time]
    world_timestamps = world_timestamps[world_timestamps < test_end_time]

    idx_missing_ts = ~np.in1d(world_timestamps, depth_data_frame_timestamps)
    world_ts_missing_in_depth_data = world_timestamps[idx_missing_ts]

    # find high confi depth data
    gaze_depth_data_high_confi = gaze_depth_data.loc[(gaze_depth_data["priority"] == 1) &
                                                     (gaze_depth_data["gaze_confidence"] > 0.8),
                                 :]

    # find low confi depth data
    gaze_depth_data_low_confi = gaze_depth_data.loc[(gaze_depth_data["priority"] == .5) &
                                                    (gaze_depth_data["gaze_confidence"] < 0.8),
                                :]

    # check if overexposure is dominant in depth data, enlarge point inclusion radius
    gaze_depth_data_overexp = gaze_depth_data.loc[(gaze_depth_data["priority"] == 1) &
                                                  (gaze_depth_data["point_overexposed"]), :]

    # output_str = ('point cloud frames in test interval: ' + str(world_timestamps.size) +
    #               ', missing frames in depth data: '+ str(world_ts_missing_in_depth_data.size) +
    #               ', depth data with high gaze confidence: ' + str(len(gaze_depth_data_high_confi.index))+
    #               ', including overexposed data: ' + str(len(gaze_depth_data_overexp.index))+
    #               ', depth data with low gaze confidence: ' + str(len(gaze_depth_data_low_confi.index)))

    # plt.text(-0.1, .9, 'point cloud frames in test interval:  ' + str(world_timestamps.size), fontsize=15)
    # plt.text(-0.1, .7, "missing frames in depth data:         " + str(world_ts_missing_in_depth_data.size), fontsize=15)
    # plt.text(-0.1, .5, "depth data with high gaze confidence: " + str(len(gaze_depth_data_high_confi.index)), fontsize=15)
    # plt.text(-0.1, .3, "including overexposed data:           " + str(len(gaze_depth_data_overexp.index)), fontsize=15)
    # plt.text(-0.1, .1, "depth data with low gaze confidence:  " + str(len(gaze_depth_data_low_confi.index)), fontsize=15)
    # plt.axis('off')

    return world_timestamps.size, \
           world_ts_missing_in_depth_data.size, \
           len(gaze_depth_data_high_confi.index), \
           len(gaze_depth_data_overexp.index), \
           len(gaze_depth_data_low_confi.index)


def plot_gaze_and_depth_gaze(rec_folder, target_distances):
    # plotting gaze_data and gaze_depth_data with high confidence in field of view pico flexx during testing
    recording_start_date, recording_start_time_system, recording_start_time_synced = get_PL_info_old_style(
        rec_folder)
    # led_timings
    # get LED timings for display purpose
    led_timings = led_timings_in_PL_time(rec_folder, target_distances);
    # load gaze data
    gaze_data = pd.read_csv(rec_folder + r'\exports\000\gaze_positions.csv')

    # set gaze_timestamps to relative time to time_synced
    gaze_data.loc[:, "gaze_timestamp"] = (gaze_data.loc[:, "gaze_timestamp"] - recording_start_time_synced)
    gaze_data.loc[:, "gaze_timestamp"] = gaze_data.loc[:, "gaze_timestamp"].round(6)

    # gaze data in interval (LED start time - LED end time)
    gaze_data = gaze_data.loc[gaze_data.loc[:, "gaze_timestamp"] > (led_timings.loc[1, "rel_time_dec"]), :]
    gaze_data = gaze_data.loc[gaze_data.loc[:, "gaze_timestamp"] < (led_timings["rel_time_dec"].iloc[-1]), :]

    # load gaze depth data
    gaze_depth_data = pd.read_csv(rec_folder + r'\gaze_depth.csv')

    # set gaze_ts relative to recording_start_time_system by deducting recording_start_time_synced
    gaze_depth_data["gaze_ts"] = (gaze_depth_data["gaze_ts"] - recording_start_time_synced)
    gaze_depth_data["gaze_ts"] = gaze_depth_data["gaze_ts"].round(6)

    # gaze_depth_data in LED presentation interval only
    gaze_depth_data = gaze_depth_data.loc[gaze_depth_data.loc[:, "gaze_ts"] > (led_timings.loc[1, "rel_time_dec"]),
                      :]
    gaze_depth_data = gaze_depth_data.loc[
                      gaze_depth_data.loc[:, "gaze_ts"] < (led_timings["rel_time_dec"].iloc[-1]), :]

    # # check if matching gaze confidence is high, if not exclude and record low confidence

    depth_data_timestamps = pd.unique(gaze_depth_data["gaze_ts"])
    gaze_data_depth_index = gaze_data.index[gaze_data["gaze_timestamp"].isin(depth_data_timestamps)].tolist()
    gaze_data_depth = gaze_data.loc[gaze_data_depth_index, :]
    for index in gaze_data_depth.index:
        # find timestamp match in gaze data and gaze depth data
        match_index = gaze_depth_data.index[
            gaze_depth_data["gaze_ts"] == (gaze_data_depth.loc[index, "gaze_timestamp"])].tolist()
        gaze_depth_data.loc[match_index, "gaze_confidence"] = gaze_data_depth.loc[index, "confidence"]

    gaze_depth_data = gaze_depth_data.loc[gaze_depth_data["gaze_confidence"] > .8, :]
    unique_ts_high_confi_depth_data = pd.unique(gaze_depth_data["gaze_ts"])
    gaze_data_index_depth_high_confi = gaze_data.index[
        gaze_data["gaze_timestamp"].isin(unique_ts_high_confi_depth_data)].tolist()

    high_confi_index = gaze_data.index[gaze_data.loc[:, "confidence"] > 0.8]
    # print(gaze_data.size)
    # print(gaze_depth_data.size)
    # # fig = plt.figure(figsize=(10, 7), dpi=80, facecolor='w', edgecolor='k')
    # plt.scatter(gaze_data.loc[high_confi_index, "norm_pos_x"], gaze_data.loc[high_confi_index, "norm_pos_y"],
    #             s=5, alpha=0.2)

    plt.scatter(gaze_data.loc[gaze_data_index_depth_high_confi, "norm_pos_x"],
                gaze_data.loc[gaze_data_index_depth_high_confi, "norm_pos_y"],
                s=50, alpha=0.3, marker='+', color="red", linewidth=1, )
    plt.title('Gaze directions pico flexx grid 224x171')
    plt.text(0, 1.05, rec_folder)
    plt.text(0, 0, '*gaze directions of depth data with > 0.8 confidence only')
    plt.text(0, -0.05, 'high confidence:')
    plt.xlim([-0.1, 1.1])
    plt.ylim([-0.1, 1.1])
    plt.grid()


def blinks_duration_hist(fp):
    # visualize blinks duration in histogram
    plt.title('blink durations histogram y-scale[log], bins=40')
    if not os.path.isfile(os.path.join(fp, 'exports\\000\\blinks.csv')):
        plt.text(.1, 0.1, 'No Blink data available')
    else:
        blinks_data = pd.read_csv(os.path.join(fp, 'exports\\000\\blinks.csv'))
        plt.hist(blinks_data.duration, bins=40)
        plt.grid()
        plt.yscale('log')


def test_start_end_time(fp):
    # aquire start and end time from led_testings
    f = open(os.path.join(fp, 'LED_timings.txt'))
    lines = f.readlines()
    f.close()
    for idx, line in enumerate(lines):
        # find experiment start time
        if not line.find('Test start') == -1:
            test_start_time = line.split(' ->')[0]
        if not line.find('Test end') == -1:
            test_end_time = line.split(' ->')[0]
    del line, lines

    with open(os.path.join(fp, 'info.player.json')) as json_file:
        info_data = json.load(json_file)
        recording_start_date = datetime.strptime(info_data["recording_name"], '%Y_%m_%d')
        recording_start_time_system = float(info_data["start_time_system_s"])
        recording_start_time_synced = float(info_data["start_time_synced_s"])

    test_start_time = datetime.strptime(test_start_time, '%H:%M:%S.%f')
    test_start_time = test_start_time.replace(year=recording_start_date.year,
                                              month=recording_start_date.month,
                                              day=recording_start_date.day)
    test_start_time = test_start_time.timestamp() - recording_start_time_system

    test_end_time = datetime.strptime(test_end_time, '%H:%M:%S.%f')
    test_end_time = test_end_time.replace(year=recording_start_date.year,
                                          month=recording_start_date.month,
                                          day=recording_start_date.day)
    test_end_time = test_end_time.timestamp() - recording_start_time_system
    return test_start_time, test_end_time, recording_start_time_synced


def gaze_data_confidence_hist(gaze_data):
    # # gaze confidence distribution
    plt.hist(gaze_data.confidence, bins=20)
    plt.title('gaze confidence histogram')
    # plt.yscale('log')
    plt.grid()


def depth_confidence_hist(depth_data, gaze_data):
    # # depth data gaze confidence distribution
    gaze_data = gaze_data.set_index('gaze_timestamp')
    plt.hist(gaze_data.loc[pd.unique(depth_data.gaze_ts), 'confidence'], bins=20)
    plt.title('point cloud related gaze timestamps confidence histogram')
    # plt.yscale('log')
    plt.grid()


def distance_to_point_of_regard_in_testing_interval(gaze_depth_data, led_timings):

    plt.grid(which='both', color='grey', alpha=.5)
    # implement filters here
    # # disregard low confidence depth data
    # # check for over exposure

    for idx, rel_time_dec in led_timings[:-1].iterrows():
        plt.fill_between([led_timings.loc[idx, "rel_time_dec"], led_timings.loc[idx + 1, "rel_time_dec"]],
                         [led_timings.loc[idx, "target_distance"] - .05,
                          led_timings.loc[idx, "target_distance"] - .05],
                         [led_timings.loc[idx, "target_distance"] + .05,
                          led_timings.loc[idx, "target_distance"] + .05],
                         facecolor="green", alpha=.6
                         )

    # set different filter

    selection = gaze_depth_data.loc[(gaze_depth_data['priority'] == 1) &
                                    (gaze_depth_data['radius'] == 2) &
                                    (gaze_depth_data['gaze_confidence'] > .8),
                :]

    plt.scatter(selection["gaze_ts"], selection["depth_mean"],
                       marker=".",
                       s=(selection['radius']),
                       c="black"
                       )

    selection2 = gaze_depth_data.loc[(gaze_depth_data['priority'] == 1) &
                                     (gaze_depth_data['radius'] == 4) &
                                     (gaze_depth_data['gaze_confidence'] > .8),
                 :]

    plt.scatter(selection2["gaze_ts"], selection2["depth_mean"],
                       marker=".",
                       s=(selection2['radius']) ** 2,
                       c="blue",
                       alpha=.7
                       )

    # selection3 = gaze_depth_data.loc[(gaze_depth_data['priority']==.5) &
    #                                 (gaze_depth_data['gaze_confidence'] < .8 ),
    #                                  :]

    # plt.scatter(selection3["gaze_ts"], selection3["depth_mean"],
    #             marker=".",
    #             s=(selection3['radius'])**2,
    #             c="red",
    #             alpha = .7
    #             )
    plt.title('Distance to point of regard over time [min percent point inclusion 20% radius 2 otherwise radius 4]',
              fontsize=20)
    plt.xlabel('time [s]')
    plt.ylabel('distnace to point of regard [m]')
    plt.xlim([min(gaze_depth_data["gaze_ts"]), max(gaze_depth_data["gaze_ts"])])
    plt.ylim([0, 4.9])


def distance_to_point_of_regard_basics(fp, target_distances):
    check_source_f(fp)
    test_start_time, test_end_time, recording_start_time_synced = test_start_end_time(fp)
    led_timings = led_timings_in_PL_time(fp, target_distances)
    # testing the depth data
    # #load gaze_depth.csv
    gaze_depth_data = pd.read_csv(os.path.join(fp, r'gaze_depth.csv'))

    # set gaze_ts relative to recording_start_time_system by deducting recording_start_time_synced
    gaze_depth_data[["gaze_ts", "frame_timestamp"] ] = gaze_depth_data[["gaze_ts", "frame_timestamp"]] \
                                                     - recording_start_time_synced
    gaze_depth_data[["gaze_ts", "frame_timestamp"]] = gaze_depth_data[["gaze_ts", "frame_timestamp"]].round(6)

    # gaze_depth_data in LED presentation interval only
    gaze_depth_data = gaze_depth_data.loc[gaze_depth_data.loc[:, "gaze_ts"] > test_start_time, :]
    gaze_depth_data = gaze_depth_data.loc[gaze_depth_data.loc[:, "gaze_ts"] < test_end_time, :]

    # # check if matching gaze confidence is high, if not exclude and record low confidence
    gaze_data = pd.read_csv(os.path.join(fp, r'exports\000\gaze_positions.csv'))

    # # set gaze_data relative to recording_start_time_system by deducting recording_start_time_synced
    gaze_data["gaze_timestamp"] = gaze_data["gaze_timestamp"] - recording_start_time_synced
    gaze_data["gaze_timestamp"] = gaze_data["gaze_timestamp"].round(6)

    depth_data_timestamps = pd.unique(gaze_depth_data["gaze_ts"])
    gaze_depth_data_index = gaze_data.index[gaze_data["gaze_timestamp"].isin(depth_data_timestamps)].tolist()
    gaze_data_depth = gaze_data.loc[gaze_depth_data_index, :]

    for index in gaze_data_depth.index:
        # find timestamp match in gaze data and gaze depth data
        match_index = gaze_depth_data.index[gaze_depth_data["gaze_ts"] ==
                                            (gaze_data_depth.loc[index, "gaze_timestamp"])].tolist()
        gaze_depth_data.loc[match_index, "gaze_confidence"] = gaze_data_depth.loc[index, "confidence"]

    gaze_depth_data_high_confi = pd.unique(gaze_depth_data[gaze_depth_data["gaze_confidence"] > 0.8].gaze_ts)

    gaze_depth_data_low_confi = pd.unique(gaze_depth_data[gaze_depth_data["gaze_confidence"] < 0.8].gaze_ts)

    # # in  gaze_depth_data unique timestamps for low confidence set  ["q_of_data", "priority"] = 0
    for uniqueTS in gaze_depth_data_low_confi:
        uniqueTS_index = gaze_depth_data.index[gaze_depth_data["gaze_ts"] == uniqueTS]
        gaze_depth_data.loc[uniqueTS_index[0], "depth_confidence"] = 0
        gaze_depth_data.loc[uniqueTS_index[0], "priority"] = .5

    # # set filters in high gaze_confidence data
    for uniqueTS in gaze_depth_data_high_confi:

        # find index for data with same unique timestamp in gaze_depth_data
        uniqueTS_index = gaze_depth_data.index[gaze_depth_data["gaze_ts"] == uniqueTS]

        # find overexposure in smalest radius and set priority to 1
        perc_over_exp = gaze_depth_data.loc[uniqueTS_index[0], "point_overexposed"] / gaze_depth_data.loc[
            uniqueTS_index[0], "total_point_count"]
        if perc_over_exp > 0.5:
            gaze_depth_data.loc[uniqueTS_index, "depth_confidence"] = (
                        gaze_depth_data.loc[uniqueTS_index, "point_overexposed"] /
                        gaze_depth_data.loc[uniqueTS_index, "total_point_count"] /
                        gaze_depth_data.loc[uniqueTS_index, "depth_stddev"]
                        )
            gaze_depth_data.loc[idxmax(gaze_depth_data.loc[uniqueTS_index, "depth_confidence"]), "priority"] = 1

        # radius 2 / 4 no depth data - set to distant data
        elif gaze_depth_data.loc[uniqueTS_index[0], "radius"] > 4:
            # add row in dataframe and copy
            gaze_depth_data = gaze_depth_data.append(
                {"frame_timestamp": gaze_depth_data.loc[uniqueTS_index[0], "frame_timestamp"],
                 "gaze_ts": gaze_depth_data.loc[uniqueTS_index[0], "gaze_ts"],
                 "frame_idx": gaze_depth_data.loc[uniqueTS_index[0], "frame_idx"],
                 "tag": gaze_depth_data.loc[uniqueTS_index[0], "tag"],
                 "radius": 2,
                 "mask_size_pixels": 13,
                 "point_percentage": 1,
                 "point_overexposed": 0,
                 "point_missing": 0,
                 "depth_mean": 4.8,
                 "gaze_confidence": gaze_depth_data.loc[uniqueTS_index[0], "gaze_confidence"],
                 "depth_confidence": 1,
                 "priority": 1},
                ignore_index=True)

        # data points with high point inclusions > .2 take smalest radius
        elif gaze_depth_data.loc[uniqueTS_index[0], "point_percentage"] > .3:
            gaze_depth_data.loc[uniqueTS_index[0], "priority"] = 1
        else:
            gaze_depth_data.loc[uniqueTS_index[1], "priority"] = 1

    # depth data within range 0.14- 4.8 m
    gaze_depth_data.loc[gaze_depth_data['depth_mean'] >= 4.7, 'depth_mean'] = 4.7

    return gaze_depth_data, gaze_data, led_timings


def distance_to_point_of_regard_radii_selected_hist(gaze_depth_data):
    # gaze_depth_data, led_timings = distance_to_point_of_regard_basics(fp, target_distances)
    # in gaze_depth_data flag times to target looked at
    selection3 = gaze_depth_data.loc[(gaze_depth_data['priority'] == 1) &
                                     (gaze_depth_data['gaze_confidence'] > .8), :]
    plt.hist(selection3["radius"])
    plt.title('radius of pixel inclusion to calculate depth at point of regard')
    plt.grid()


def boxplot_targets_distance_m(gaze_depth_data, led_timings, target_distances):
    # gaze_depth_data, led_timings = distance_to_point_of_regard_basics(fp, target_distances)
    gaze_depth_data['led_id'] = np.nan
    for idx in led_timings.index[1:-1]:
        gaze_depth_data.loc[(gaze_depth_data['gaze_ts'] >= led_timings.loc[idx, 'rel_time_dec'] + .6) &
                            (gaze_depth_data['gaze_ts'] <= led_timings.loc[idx + 1, 'rel_time_dec']), ['led_id']] = \
        led_timings.loc[idx, 'led_id']

    boxplot_data = list(range(1, 15, 1))
    pos = np.array(range(1, 14, 1))

    for i in range(1, 14, 1):
        boxplot_data[i] = (gaze_depth_data.loc[(gaze_depth_data['led_id'] == i) &
                                               (gaze_depth_data['priority'] == 1), "depth_mean"])
    plt.boxplot([boxplot_data[1],
                 boxplot_data[2],
                 boxplot_data[3],
                 boxplot_data[4],
                 boxplot_data[5],
                 boxplot_data[6],
                 boxplot_data[7],
                 boxplot_data[8],
                 boxplot_data[9],
                 boxplot_data[10],
                 boxplot_data[11],
                 boxplot_data[12],
                 boxplot_data[13]])

    for led_id in range(1, 14, 1):
        #     print(led_id, '->', [target_distances.loc[led_id, 'distance'] -.05])
        #     print(type(led_id))
        plt.fill_between([led_id - 0.5, led_id + 0.5],
                         [target_distances.loc[led_id, 'distance'] - .05,
                          target_distances.loc[led_id, 'distance'] - .05],
                         [target_distances.loc[led_id, 'distance'] + .05,
                          target_distances.loc[led_id, 'distance'] + .05],
                         facecolor="green", alpha=.6
                         )
    for idx in range(1, 14, 1):
        plt.text(idx - 0.5, -0.4, 'n='+ str(len(boxplot_data[idx])), fontsize=8)
    plt.title('Distance to point of regard for individual targets / onset time + 0.6')
    plt.ylabel('distnace to point of regard [m]')
    plt.text(0.6, 4.65, 'target distances with error margines +/- 0.05m', fontsize=8)
    plt.ylim([0, 4.9])


def boxplot_targets_distance_dpt(gaze_depth_data, led_timings, target_distances):
    gaze_depth_data['led_id'] = np.nan
    for idx in led_timings.index[1:-1]:
        gaze_depth_data.loc[(gaze_depth_data['gaze_ts'] >= led_timings.loc[idx, 'rel_time_dec'] + .6) &
                            (gaze_depth_data['gaze_ts'] <= led_timings.loc[idx + 1, 'rel_time_dec']), ['led_id']] = \
        led_timings.loc[idx, 'led_id']

    boxplot_data = list(range(1, 15, 1))
    pos = np.array(range(1, 14, 1))

    for i in range(1, 14, 1):
        boxplot_data[i] = 1/ (gaze_depth_data.loc[(gaze_depth_data['led_id'] == i) &
                                               (gaze_depth_data['priority'] == 1), "depth_mean"])
    plt.boxplot([boxplot_data[1],
                 boxplot_data[2],
                 boxplot_data[3],
                 boxplot_data[4],
                 boxplot_data[5],
                 boxplot_data[6],
                 boxplot_data[7],
                 boxplot_data[8],
                 boxplot_data[9],
                 boxplot_data[10],
                 boxplot_data[11],
                 boxplot_data[12],
                 boxplot_data[13]])

    for led_id in range(1, 14, 1):
        #     print(led_id, '->', [target_distances.loc[led_id, 'distance'] -.05])
        #     print(type(led_id))
        plt.fill_between([led_id - 0.5, led_id + 0.5],
                         [1/ (target_distances.loc[led_id, 'distance'] * .95),
                          1/ (target_distances.loc[led_id, 'distance'] * .95)],
                         [1/ (target_distances.loc[led_id, 'distance'] *1.05),
                          1/ (target_distances.loc[led_id, 'distance'] *1.05)],

                         facecolor="green", alpha=.6
                         )
    for idx in range(1, 14, 1):
        plt.text(idx - 0.5, -0.4, 'n='+ str(len(boxplot_data[idx])), fontsize=8)
    plt.title('Distance to point of regard for individual targets / onset time + 0.6')
    plt.ylabel('distnace to point of regard [dpt]')
    plt.text(0.6, 4.65, 'target distances with 5% error margines', fontsize=8)
    plt.ylim([0, 4.9])


def get_ttd_and_meta(fp, target_distances):

    if not os.path.isfile(os.path.join(fp, 'pointcloud_all_found_targetall.csv')):
        merge_all_target_pos_csvs(fp)
        # sys.exit('pointcloud_all_found_targetall.csv missing')
    ttd = pd.read_csv(os.path.join(fp, 'pointcloud_all_found_targetall.csv'))
    # change all 0 values to nan
    ttd[ttd < .1] = np.nan
    # round ts to 6 decimales
    ttd.loc[:, 'world_ts_test_interval'] = round(ttd.loc[:, 'world_ts_test_interval'], 6)

    # average x,y r and plot
    ttd_meta = pd.DataFrame(columns=['r', 'x', 'y', 'nan_count'])
    for idx2, col_idx in enumerate(range(1, 34, 3)):
        # extract radii means

        ttd_meta.loc[idx2, 'r'] = ttd.iloc[:, col_idx].mean(skipna=True)
        # extract x_pos mean
        ttd_meta.loc[idx2, 'x'] = ttd.iloc[:, col_idx + 1].mean(skipna=True)
        # extract y_pos mean
        ttd_meta.loc[idx2, 'y'] = ttd.iloc[:, col_idx + 2].mean(skipna=True)
        # count values
        ttd_meta.loc[idx2, 'nan_count'] = ttd.iloc[:, col_idx].isna().sum()

    # for each target, if availabel calculate variance to average position and record in ttd
    t_pos = pd.DataFrame(columns=['delta_x', 'delta_y'])
    for row_idx in ttd.index:
        for t_idx, col_idx in enumerate(range(2, 34, 3)):
            t_pos.loc[t_idx, 'delta_x'] = ttd_meta.loc[t_idx, 'x'] - ttd.iloc[row_idx, col_idx]
            t_pos.loc[t_idx, 'delta_y'] = ttd_meta.loc[t_idx, 'y'] - ttd.iloc[row_idx, col_idx + 1]

        ttd.loc[row_idx, 'delta_x_mean'] = t_pos.loc[:, 'delta_x'].mean(skipna=True)
        ttd.loc[row_idx, 'delta_y_mean'] = t_pos.loc[:, 'delta_y'].mean(skipna=True)
        ttd.loc[row_idx, 'delta_x_std'] = t_pos.loc[:, 'delta_x'].std(skipna=True)
        ttd.loc[row_idx, 'delta_y_std'] = t_pos.loc[:, 'delta_y'].std(skipna=True)

    # match ts with ts from gaze data
    gaze_depth_data, gaze_data, led_timings = distance_to_point_of_regard_basics(fp, target_distances)

    idx = gaze_depth_data.frame_timestamp.drop_duplicates().index.to_list()
    gaze_depth_data = gaze_depth_data.loc[idx, ['frame_timestamp', 'gaze_ts']].reset_index(drop=True)

    for idx in ttd.index:
        # # find ts in depth data
        world_ts = ttd.loc[idx, 'world_ts_test_interval']
        gaze_ts_s = gaze_depth_data.gaze_ts[gaze_depth_data.frame_timestamp == world_ts].reset_index(drop=True)
        if not gaze_ts_s.empty:
            ttd.loc[idx, 'gaze_ts'] = gaze_ts_s[0]
            # from gaze_ts find in gaze_timestamp and record norm_pos_x and norm_pos_y
            norm_pos_x_s = gaze_data.norm_pos_x[gaze_data.gaze_timestamp == gaze_ts_s[0]].reset_index(drop=True)
            if not norm_pos_x_s.empty:
                ttd.loc[idx, 'norm_pos_x'] = norm_pos_x_s[0]
            norm_pos_y_s = gaze_data.norm_pos_y[gaze_data.gaze_timestamp == gaze_ts_s[0]].reset_index(drop=True)
            if not norm_pos_y_s.empty:
                ttd.loc[idx, 'norm_pos_y'] = norm_pos_y_s[0]
            gaze_confidence_s = gaze_data.confidence[gaze_data.gaze_timestamp == gaze_ts_s[0]].reset_index(
                drop=True)
            if not gaze_confidence_s.empty:
                ttd.loc[idx, 'gaze_confidence'] = gaze_confidence_s[0]
    ttd.loc[:, 'pos_x_cc'] = ttd.loc[:, 'norm_pos_x'] * 224 - ttd.loc[:, 'delta_x_mean']
    ttd.loc[:, 'pos_y_cc'] = ttd.loc[:, 'norm_pos_y'] * 171 - ttd.loc[:, 'delta_y_mean']
    # merge led_timeings with ttd

    # print()
    for idx in led_timings.index[2:]:
        start = led_timings.rel_time_dec[idx - 1] + .6
        end = led_timings.rel_time_dec[idx]
        interval = ttd
        interval = interval.loc[interval.world_ts_test_interval > start, :]
        interval = interval.loc[interval.world_ts_test_interval < end, :]
        ttd.loc[interval.index, 'led_id'] = led_timings.loc[idx - 1, 'led_id']
        ttd.loc[interval.index, 'led_time_idx'] = idx

    ttd.led_id = ttd.led_id.fillna(0).astype(int)
    # point inclusion per target
    for idx_t in ttd_meta.index:
        ttd_meta.loc[idx_t, 'gaze_per_t_high_confi'] = \
        ttd.pos_x_cc[(ttd.gaze_confidence >= .8) & (ttd.led_id == idx_t + 1)].shape[0]

    return ttd, ttd_meta


def merge_all_target_pos_csvs(fp):
    if not os.path.isfile(os.path.join(fp, 'pointcloud.rrf.csv')):
        sys.exit('pointcloud.rrf.csv missing')
    else:
        target_data = pd.read_csv(os.path.join(fp, 'pointcloud.rrf.csv'))

    fp_n = os.path.join(fp, 'pointcloud_*.rrf.csv')
    for fn in glob.glob(fp_n):
        target_data_new = pd.read_csv(fn)
        target_data = target_data.append(target_data_new, ignore_index=True)

    # for each merged .csv match ts form world_timestamps.npy
    world_timestamps = np.load(os.path.join(os.path.join(fp, 'world_timestamps.npy')))

    if len(world_timestamps) < target_data.shape[0]:
        target_data.loc[0:len(world_timestamps) - 1, 'world_timestamp'] = world_timestamps
    elif len(world_timestamps) > target_data.shape[0]:
        target_data['world_timestamp'] = world_timestamps[:target_data.shape[0]]
    else:
        target_data['world_timestamp'] = world_timestamps

    # cut down data to led_timings interval
    test_start_time, test_end_time, recording_start_time_synced = test_start_end_time(fp)

    target_data["world_timestamp"] = target_data["world_timestamp"] - recording_start_time_synced
    target_data["world_timestamp"] = target_data["world_timestamp"].round(6)

    # gaze data in interval ( test start time - test end time)
    target_data = target_data.loc[target_data.loc[:, "world_timestamp"] > test_start_time]
    target_data = target_data.loc[target_data.loc[:, "world_timestamp"] < test_end_time]

    target_data = target_data.rename(columns={"world_timestamp": "world_ts_test_interval"})

    # save all target data to csv
    target_data = target_data.drop('world_cam_frame_idx', axis=1)
    cols = list(target_data)
    cols = [cols[-1]] + cols[:-1]
    target_data = target_data[cols]

    target_data.to_csv(os.path.join(fp, 'pointcloud_all_found_targetall.csv'),
                       index=False)


# # # https://matplotlib.org/3.1.1/gallery/statistics/confidence_ellipse.html#sphx-glr-gallery-
#       statistics-confidence-ellipse-py
def confidence_ellipse(x, y, ax, n_std=3.0, facecolor='none', **kwargs):
    from matplotlib.patches import Ellipse
    import matplotlib.transforms as transforms

    """
    Create a plot of the covariance confidence ellipse of `x` and `y`

    Parameters
    ----------
    x, y : array_like, shape (n, )
        Input data.

    ax : matplotlib.axes.Axes
        The axes object to draw the ellipse into.

    n_std : float
        The number of standard deviations to determine the ellipse's radii.

    Returns
    -------
    matplotlib.patches.Ellipse

    Other parameters
    ----------------
    kwargs : `~matplotlib.patches.Patch` properties
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensionl dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0),
                      width=ell_radius_x * 2,
                      height=ell_radius_y * 2,
                      facecolor=facecolor,
                      **kwargs)

    # Calculating the standard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)

    # calculating the standard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf = transforms.Affine2D() \
        .rotate_deg(45) \
        .scale(scale_x, scale_y) \
        .translate(mean_x, mean_y)

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)

