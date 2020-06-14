import os
import re
import glob
import csv

#This is for going through the document and searching for start time, endtime, and speaker
def line_search(lines):
    start = re.search('starttime=(.*)end', lines).group(1)
    start = start.split()[0]
    end = re.search('endtime=(.*) ', lines).group(1)
    end = end.split()[0]
    speaker = re.search('participant=(.*)>', lines)
    if speaker != None:
        return start, end, speaker.group(1)
    else:
        pass

def dial_acts(file_location):
    print(file_location)
    with open(file_location, 'r') as t:
        text = t.read()

    #locate data after the href= value
    hits = []
    for lines in text.split('\n'):
        hit = re.search('href=(.*)$',lines)
        if hit != None:
            hits.append(hit.group(1).strip('"/>'))

    #split the data based off of the '#' delimeter
    file = [0] * len(hits)
    dial = [0] * len(hits)
    for i, phrase in enumerate(hits):
        file[i], dial[i] = phrase.split('#')
        dial[i] = dial[i].replace('id(', '').replace(')', '').strip()


    #Extend out the dialgoue act, i.e. 209..214 becomes 209, 210, 211, 212, 213, 214
    for i, acts in enumerate(dial):
        if '..' in acts:
            act_beg, act_end = acts.split('..')
            splits = act_beg.partition('act')
            act = splits[0] + splits[1]
            begin = int(splits[2])
            end = int(act_end.partition('act')[2])
            dial[i] = act + str(begin)
            for j in range(begin+1, end+1):
                dial.append(act + str(j))

    #print(file)
    key = list(set(file))
    file_name = key[0].split('.')[0]

    #key.sort() #Not necessary but makes the data a lot easier to read
    info = dict.fromkeys(key, 1)

    for keys in key:
        temp = []
        split_one = keys.split('.dial')[0]
        for items in dial:
            if split_one in items:
                temp.append(items)
        info.update({keys : temp})

    return info, file_name

def data_search(data_file):
    for key in data_file:
        file_location = '/home/alex/Downloads/ICSI_plus_NXT/ICSIplus/DialogueActs/' + key

        with open(file_location, 'r') as t:
            text = t.read()

        #In a few of the examples the data was appended differently, this code ensures
        #that the data is split correctly between files to prevent a case where
        #when doing a line search, we replace act23 with act230
        for i in range(len(data_file[key])):
            if data_file[key][i][-1] != '"':
                data_file[key][i] = data_file[key][i] + '"'

        #Here we create a nested dictionary, its output will look like
        #file_name{dialogue_act {start time, end time, speaker}}
        act_info = {}
        for lines in text.split('\n'):
            for i in range(len(data_file[key])):
                #Data was annotated slightly different between files
                if data_file[key][i] in lines:
                #if data_file[key][i] + '"' in lines:
                    start, end, speaker = line_search(lines)
                    act_info.update({data_file[key][i] : {'start' : start.replace('"', ''),
                                                          'end' : end.replace('"', ''),
                                                          'speaker' : speaker}})
        data_file.update({key : act_info})

    return(data_file)

def data_match(file_name, data):
    location = '/home/alex/Downloads/annotated transcripts/' + file_name + '.mrt'
    #location = '/home/alex/Downloads/ICSI_original_transcripts/transcripts/' + file_name + '.mrt'
    with open(location, 'r') as t:
        text = t.read()

    #The goal here is to remove all un-needed tags
    tags = []
    for item in text.split('\n'):
        if '<S' not in item:
            if '<' in item:
                a = re.findall('<[^>]+>', item)
                for i in range(len(a)):
                    tags.append(a[i])

    # Here we remove the Segment tags from the list of un-needed tags
    tags = list(set(tags))
    if '</Segment>' in tags: tags.remove('</Segment>')
    if '<Segment>' in tags: tags.remove('<Segment>')
    if '<Jargon>' in tags: tags.remove('<Jargon>')
    if '</Jargon>' in tags: tags.remove('</Jargon>')
    if '<jargon>' in tags: tags.remove('<jargon>')
    if '</jargon>' in tags: tags.remove('</jargon>')
    for emphasis_tag in tags:
        text = text.replace(emphasis_tag, '')
        text = text.replace('</j','</J')
        text = text.replace('<j', '<J')
        text = text.replace(' </Jargon>', '</Jargon>')
        text = text.replace('<Jargon> ', '<Jargon>')

    text = text.replace('<Jargon>', '--Jargon--')
    text =text.replace('</Jargon>', '--/Jargon--')
            #if file_name == 'Bdb001':
                #print(item)
                #print(word)


    #Here we will go through and pull out every dialogue piece,
    #and set the ground truth label to 0
    full_data = []
    for lines in text.split('\n'):
        #labels vary between the two files, to create uniformity, the tags are all
        #changed to lower case. In addition to this an additional tag is present
        #that must be stripped from the document
        lines = lines.lower()
        if ('participant=' in lines) and ('closemic=' not in lines):
            start, end, speaker = line_search(lines)
            full_data.append([start, end, speaker, 0])
        if ('participant=' in lines) and ('closemic=' in lines):
            lines = lines.replace(' closemic="false"', '')
            start, end, speaker = line_search(lines)
            full_data.append([start, end, speaker, 0])


    #Here we get the items that will be used for generating positive labels
    dial_data = []
    for _, elem in data.items():
        for _, items in elem.items():
            dial_data.append([float(items['start']),
                             float(items['end']),
                             items['speaker']])

    #Here the values are checked to see if the info in dial_data is present
    #in the full data, and to see if it meets the requirements to be positive
    #in that there should be an overlap, like in the text below
    #           all_data_ST <dial_data_ST < all_data_ET
    #                           or
    #           all_data_ST <dial_data_ET < all_data_ET
    for i in range(len(dial_data)):
        for j in range(len(full_data)):
            if full_data[j][2] == dial_data[i][2]:
                fds_time = float(full_data[j][0].replace('"', ''))
                fde_time = float(full_data[j][1].replace('"', ''))
                fds_time_int = int(round(fds_time))
                fde_time_int = int(round(fde_time))
                #This gathers the time from the data we are itnerested in
                dial_range = set(range(int(dial_data[i][0]), int(dial_data[i][1])))
                all_range = range(fds_time_int, fde_time_int)
                #This sees if there is overlap
                overlap = bool(dial_range.intersection(all_range))
                #if overlap == True:
                if (fds_time <= dial_data[i][0] <= fde_time) or \
                        (fds_time <= dial_data[i][1] <= fde_time) or \
                        overlap == True:
                    full_data[j][3] = 1


    #Now we will go through the document and locate the text file
    #associated with it
    ground_truth = []
    for i in full_data:
        segment = 'StartTime=' +i[0] +' EndTime='+i[1] +' Participant='+ i[2]
        seg_find = re.search(segment+'[^<]*', text)
        if seg_find != None and seg_find != '':
            #print(segment)
            seg_find =seg_find.group().strip(segment)
            #print(seg_find)
            seg_find =seg_find.strip('CloseMic="false">')
            seg_find = seg_find.strip()
            if seg_find != '':
                min_word = len(seg_find.split())
                if file_name == "Bmr002":
                    print(seg_find.split())
                    print(min_word)
                if min_word > 4:
                    ground_truth.append([seg_find, i[3]])

    #for lines in ground_truth:
        #print(lines)
    return ground_truth


def create_file(file_name, ground_truth):
    f = open('/home/alex/place_holder/' + file_name + '.tsv', 'w+')
    #f = open(file_name +'test' + '.tsv', 'w+')
    for i in range(len(ground_truth)):
        f.write(str(ground_truth[i][0]) + '\t' + str(ground_truth[i][1]) + '\n')

def statistics(ground_truth, file_name):

    segments, labels = map(list, zip(*ground_truth))

    #Segment Statistic
    num_of_seg = len(segments)
    num_of_words = 0
    for text in segments:
        words = text.split()
        num_of_words =num_of_words + len(words)

    print('number of segments:', num_of_seg)
    avg_seg_len = num_of_words/len(segments)
    print('average segment length:', avg_seg_len)

    #positive and negative labels
    num_of_pos = 0
    num_of_neg = 0
    pos_seg_len = 0
    neg_seg_len = 0
    for seg, num in ground_truth:
        if num == 1:
            num_of_pos = num_of_pos+1
            pos_seg_len = pos_seg_len + len(seg.split())
        if num == 0:
            num_of_neg = num_of_neg+1
            neg_seg_len = neg_seg_len + len(seg.split())
    neg_lab_len = neg_seg_len/num_of_neg
    pos_lab_len = pos_seg_len/num_of_pos
    print('Negative label average length:', neg_lab_len)
    print('Positive label average length:', pos_lab_len)
    print('Number of Positive Labeels:', num_of_pos)
    print('Number of Negative Labels: ', num_of_neg)

    data = [file_name, num_of_seg, avg_seg_len,
            num_of_pos, num_of_neg, pos_lab_len, neg_lab_len]

    with open('stats.csv', 'a+') as f:
        w = csv.writer(f)
        w.writerow(data)

def run_time(file_list):
    for files in file_list:
        print("file:", files)
        initial_data, file_name = dial_acts(files)
        data_dict = data_search(initial_data)
        data_info = data_match(file_name, data_dict)
        create_file(file_name, data_info)
        #statistics(data_info, file_name)

def main():
    alt_location = True
    main_location = True

    with open('stats.csv', 'w+') as csvfile:
        fieldname = ['file name', '# of segments', 'Average length of segments',
                      'number of positive labels', 'number of negative labels',
                      'positive label average length', 'negative label average length']
        writer = csv.DictWriter(csvfile, fieldnames = fieldname, delimiter = ',')
        writer.writeheader()

    if main_location == True:
        file_list = glob.glob("/home/alex/Downloads/ICSI_plus_NXT/ICSIplus/"
                              "Contributions/Summarization/extractive/*.extsumm.xml")

        run_time(file_list)


    if alt_location == True:
        file_list = glob.glob("/home/alex/additional_data/*")
        run_time(file_list)

if __name__ == "__main__":
    main()