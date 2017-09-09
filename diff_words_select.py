# -*- coding: UTF-8 -*-

with open('allwords_freq_jane_eyre.txt', 'r') as aw:
    word_list = aw.read().split('\n')

with open('coca_60000.txt', 'r') as coca:
    coca_list = coca.read().split('\n')

with open('cet6_edited.txt', 'r') as cet:
    cet_list = cet.read().split('\n')


diff_list = list(set(word_list).difference(set(cet_list)))

temp_dict = {}
for x in diff_list:
    if x in coca_list:
        p = coca_list.index(x)
        temp_dict[x] = p

# diff_dict = sorted(temp_dict.items(), key=lambda x: x[1])

diff_dict =  dict((k, v) for v, k in temp_dict.items())

# for k in sorted(diff_dict.keys()):
#     print(k, diff_dict[k])

for k in sorted(diff_dict.keys()):
    print(diff_dict[k])