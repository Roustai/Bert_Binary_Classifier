import re
import glob
import csv
import statistics as stat

#Checks system positives with gold standard
def positive_test(system, gold):
    value = 0
    for line in system:
        for i in range(len(gold)):
            if line in gold[i]:
                value = value + 1

    return value

#First thing we will do is to gather all of the data regarding the
sys_file_list = glob.glob("/home/alex/rouge_test/Test/*.txt")
mod_file_list = glob.glob('/home/alex/rouge_test/GS/*.txt')
list.sort(sys_file_list)
list.sort(mod_file_list)
#print(sys_file_list)
#print(mod_file_list)

all_data = {}
#Next thing to do is to open up the files 1-by-1 and get the scores
for i in range(len(sys_file_list)):
    tot_neg = 0
    tot_pos = 0

    neg_list = []
    pos_list = []

    system_pos = []

    #General Stats
    with open(mod_file_list[i], 'r') as t:
        text_model = t.read()

    with open(sys_file_list[i], 'r') as t:
        text_sys = t.read()

    for line in text_sys.split('\n'):
        if line != '':
            system_pos.append(line)

    for line in text_model.split('\n'):
        if line != '':
            if line[-1] == '0':
                tot_neg = tot_neg + 1
                neg_list.append(line.split('0')[0])
            if line[-1] == '1':
                tot_pos = tot_pos + 1
                pos_list.append(line.split('0')[0])

    file = mod_file_list[i].strip('/home/alex/rouge_test/GS/gold_standard.A.')
    print('file: ', file)
    print('Total Positive: ', tot_pos)
    print('Total negative: ', tot_neg)


    #True positive
    true_pos = positive_test(system_pos, pos_list)
    print('True Positive:\t', true_pos)

    #False Positive
    false_pos = positive_test(system_pos, neg_list)
    print('False Positive:\t', false_pos)

    #True Negative
    true_neg =  tot_neg - false_pos
    print('True Negative:\t', true_neg)

    #False Negative
    false_neg = tot_pos - true_pos
    print('False Negative:\t', false_neg)
    print('--------------------------------------------')
    #test case
    if i == 10:
        print(len(system_pos))
        #print(text_sys)
        true_pos = positive_test(system_pos, pos_list)
        print('--------------------------------------------')
        print('--------------------------------------------')
        false_pos = positive_test(system_pos, neg_list)
        #print(neg_list)

    file_stats = {file : {'TotalPositive' : tot_pos, 'TotalNegative': tot_neg,  'TrueNegative': true_neg,
                  'TruePositive': true_pos, 'FalsePositive': false_pos,
                 'TrueNegative': true_neg, 'FalseNegative': false_neg}}
    all_data.update(file_stats)

#print(all_data)

csv_columns = ['FileName', 'TotalPositive', 'TotalNegative', 'TrueNegative',
               'TruePositive', 'FalsePositive', 'TrueNegative', 'FalseNegative']
csv_file    = "Data_Matrix.csv"
with open(csv_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()
    for key, val in all_data.items():
        row = {'FileName': key}
        row.update(val)
        print(row)
        writer.writerow(row)