#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/alibaba-damo-academy/FunClip). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

import os
import re
import numpy as np  

PUNC_LIST = ['，', '。', '！', '？', '、', ',', '.', '?', '!']

def pre_proc(text):
    res = ''
    for i in range(len(text)):
        if text[i] in PUNC_LIST:
            continue
        if '\u4e00' <= text[i] <= '\u9fff':
            if len(res) and res[-1] != " ":
                res += ' ' + text[i]+' '
            else:
                res += text[i]+' '
        else:
            res += text[i]
    if res[-1] == ' ':
        res = res[:-1]
    return res

def proc(raw_text, timestamp, dest_text, lang='zh'):
    # simple matching
    ld = len(dest_text.split())
    mi, ts = [], []
    offset = 0
    while True:
        fi = raw_text.find(dest_text, offset, len(raw_text))
        ti = raw_text[:fi].count(' ')
        if fi == -1:
            break
        offset = fi + ld
        mi.append(fi)
        ts.append([timestamp[ti][0]*16, timestamp[ti+ld-1][1]*16])
    return ts
            

def proc_spk(dest_spk, sd_sentences):
    ts = []
    for d in sd_sentences:
        d_start = d['timestamp'][0][0]
        d_end = d['timestamp'][-1][1]
        spkid=dest_spk[3:]
        if str(d['spk']) == spkid and d_end-d_start>999:
            ts.append([d_start*16, d_end*16])
    return ts

def generate_vad_data(data, sd_sentences, sr=16000):
    assert len(data.shape) == 1
    vad_data = []
    for d in sd_sentences:
        d_start = round(d['ts_list'][0][0]/1000, 2)
        d_end = round(d['ts_list'][-1][1]/1000, 2)
        vad_data.append([d_start, d_end, data[int(d_start * sr):int(d_end * sr)]])
    return vad_data

def write_state(output_dir, state):
    for key in ['/recog_res_raw', '/timestamp', '/sentences']:#, '/sd_sentences']:
        with open(output_dir+key, 'w') as fout:
            fout.write(str(state[key[1:]]))
    if 'sd_sentences' in state:
        with open(output_dir+'/sd_sentences', 'w') as fout:
            fout.write(str(state['sd_sentences']))

def load_state(output_dir):
    state = {}
    with open(output_dir+'/recog_res_raw') as fin:
        line = fin.read()
        state['recog_res_raw'] = line
    with open(output_dir+'/timestamp') as fin:
        line = fin.read()
        state['timestamp'] = eval(line)
    with open(output_dir+'/sentences') as fin:
        line = fin.read()
        state['sentences'] = eval(line)
    if os.path.exists(output_dir+'/sd_sentences'):
        with open(output_dir+'/sd_sentences') as fin:
            line = fin.read()
            state['sd_sentences'] = eval(line)
    return state

def convert_pcm_to_float(data):
    if data.dtype == np.float64:
        return data
    elif data.dtype == np.float32:
        return data.astype(np.float64)
    elif data.dtype == np.int16:
        bit_depth = 16
    elif data.dtype == np.int32:
        bit_depth = 32
    elif data.dtype == np.int8:
        bit_depth = 8
    else:
        raise ValueError("Unsupported audio data type")

    # Now handle the integer types
    max_int_value = float(2 ** (bit_depth - 1))
    if bit_depth == 8:
        data = data - 128
    return (data.astype(np.float64) / max_int_value)

def convert_time_to_millis(time_str):
    # 格式: [小时:分钟:秒,毫秒]
    hours, minutes, seconds, milliseconds = map(int, re.split('[:,]', time_str))
    return (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds

def extract_timestamps(input_text):
    # 使用正则表达式查找所有时间戳
    timestamps = re.findall(r'\[(\d{2}:\d{2}:\d{2},\d{2,3})\s*-\s*(\d{2}:\d{2}:\d{2},\d{2,3})\]', input_text)
    times_list = []
    print(timestamps)
    # 循环遍历找到的所有时间戳，并转换为毫秒
    for start_time, end_time in timestamps:
        start_millis = convert_time_to_millis(start_time)
        end_millis = convert_time_to_millis(end_time)
        times_list.append([start_millis, end_millis])
    
    return times_list

def convert_time_to_srt_format(time_in_milliseconds):
    hours = time_in_milliseconds // 3600000
    time_in_milliseconds %= 3600000
    minutes = time_in_milliseconds // 60000
    time_in_milliseconds %= 60000
    seconds = time_in_milliseconds // 1000
    time_in_milliseconds %= 1000

    return f"{hours:02}:{minutes:02}:{seconds:02},{time_in_milliseconds:03}"

def text_to_srt(idx, speaker_id, msg, start_microseconds, end_microseconds) -> str:
    start_time = convert_time_to_srt_format(start_microseconds)
    end_time = convert_time_to_srt_format(end_microseconds)

    msg = f"发言人 {speaker_id}: {msg}"
    srt = """%d %s --> %s %s """ % (
        idx,
        start_time,
        end_time,
        msg,
    )
    return srt


if __name__ == '__main__':

    # 示例输入文本
    text = [{'text': '是开始这个呃实时的一个转写。', 'start': 1010, 'end': 4865, 'timestamp': [[1010, 1250], [1750, 1990], [1990, 2230], [2410, 2510], [2510, 2750], [3450, 3690], [3830, 3990], [3990, 4170], [4170, 4250], [4250, 4330], [4330, 4430], [4430, 4570], [4570, 4865]], 'raw_text': '是开始这个呃实时的一个转写', 'spk': 0}, {'text': '对，', 'start': 6040, 'end': 6280, 'timestamp': [[6040, 6280]], 'raw_text': '对', 'spk': 0}, {'text': '然后是转写的一个效果，', 'start': 6640, 'end': 8660, 'timestamp': [[6640, 6800], [6800, 7040], [7360, 7600], [7660, 7820], [7820, 8000], [8000, 8080], [8080, 8160], [8160, 8260], [8260, 8420], [8420, 8660]], 'raw_text': '然后是转写的一个效果', 'spk': 0}, {'text': '大概大概就是这个样子。', 'start': 8680, 'end': 10280, 'timestamp': [[8680, 8760], [8760, 9000], [9160, 9300], [9300, 9480], [9480, 9600], [9600, 9740], [9740, 9840], [9840, 9960], [9960, 10080], [10080, 10280]], 'raw_text': '大概大概就是这个样子', 'spk': 0}, {'text': '然后的话那个在这里边你也可以去给他那个加一个人。', 'start': 10280, 'end': 14500, 'timestamp': [[10280, 10380], [10380, 10500], [10500, 10600], [10600, 10800], [10800, 10900], [10900, 11140], [11180, 11380], [11380, 11500], [11500, 11620], [11620, 11860], [12260, 12400], [12400, 12580], [12580, 12760], [12760, 12980], [12980, 13180], [13180, 13280], [13280, 13480], [13480, 13580], [13580, 13820], [13900, 14080], [14080, 14180], [14180, 14260], [14260, 14500]], 'raw_text': '然后的话那个在这里边你也可以去给他那个加一个人', 'spk': 0}]
    subtitles = []
    for idx, sentence in enumerate(text):
        sub = text_to_srt(idx=idx, speaker_id=sentence['spk'], msg=sentence['text'], start_microseconds=sentence['start'], end_microseconds=sentence['end'])
        subtitles.append(sub)
    print("\n".join(subtitles))

    text = ("0 00:00:01,010 --> 00:00:04,865 发言人 0: 是开始这个呃实时的一个转写。"
            "1 00:00:06,040 --> 00:00:06,280 发言人 0: 对，"
            "2 00:00:06,640 --> 00:00:08,660 发言人 0: 然后是转写的一个效果，"
            "3 00:00:08,680 --> 00:00:10,280 发言人 0: 大概大概就是这个样子。"
            "4 00:00:10,280 --> 00:00:14,500 发言人 0: 然后的话那个在这里边你也可以去给他那个加一个人。"
            "5 00:00:14,660 --> 00:00:19,665 发言人 0: 比如说是嗯我随便给他取一个名字，"
            "6 00:00:20,440 --> 00:00:23,200 发言人 1: 就是连云端的还是自己算的连云端的吧。"
            "7 00:00:23,240 --> 00:00:25,340 发言人 0: 不用连看能调吧。"
            "8 00:00:29,120 --> 00:00:31,480 发言人 2: 这个还有对呀，"
            "9 00:00:32,130 --> 00:00:33,885 发言人 0: 然后这里边可以给他加格。")

    print(extract_timestamps(text))