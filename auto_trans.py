# -*- coding: UTF-8 -*-
import time
import csv
import re


dict_data = {}
count = 0

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", open ecdict.csv")

with open('ecdict.csv', 'r', encoding='utf-8') as ec:
    f_ecdict = csv.reader(ec)
    headers = next(f_ecdict)
    for row in f_ecdict:
        # 如果需要将释义中的换行符去掉，则取消下面一行的注释
        row[3] = row[3].replace(u'\\n', '  ')
        # NOTE: 将词典的 key转换为小写
        dict_data[row[0].lower()] = row[3]

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", got dict_data")

with open('shhard.txt', 'r', encoding='utf-8') as w:
    word_list = w.read().split('\n')

with open('shorthistory.txt', 'r', encoding='utf-8') as ori:
    all_text = ori.read()

# 将lemmas.txt转化成两个字典：
# 第一个字典，key是lemmas.txt每行的第一列，value是以list格式存放的lemma.txt一整行内容
# 第二个字典，key是lemmas.txt的每一个单词，value是key所在行的第一列，value只有一个单词
# NOTE: 两个字典的内容均为 小写

lemmas = {}
re_lemmas = {}

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", open lemmmas.txt")

with open('lemmas.txt', 'r', encoding='utf-8') as lemmas_file:
    temp_lemmas = lemmas_file.readlines()
    for line in temp_lemmas:
        parts = line.split()
        lemmas[parts[0].lower()] = []
        for i in range(0, len(parts)):
            lemmas[parts[0].lower()].append(parts[i].lower())
            re_lemmas[parts[i].lower()] = parts[0].lower()

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", got lemmmas and re_lemmas")

# 将w_list和w_list所有单词的其他形式，以及中文意思，存到all_words_trans

all_words_trans = {}
for w in word_list:
    if w:
        w_lemmas = lemmas.get(w)
        for w_le in w_lemmas:
            a_tran = dict_data.get(w_le.lower())
            if not a_tran:
                org_w = re_lemmas.get(w_le.lower())
                if org_w:
                    org_w_tran = dict_data.get(org_w)
                    if org_w_tran:
                        a_tran = org_w_tran
                    else:
                        print('Error, "%s" is not in dict_data' % org_w)
                else:
                    print('Error, "%s" is not in re_lamms' % org_w)
            if a_tran:
                all_words_trans[w_le] = a_tran
            else:
                all_words_trans[w_le] = "No translation"
print(all_words_trans)

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", begin to replace")

for w, tran in all_words_trans.items():
    # 替换之外，给生词和翻译加上html格式
    w_tran =  '<font color=red>'+ w  + '</font>'+ '(<font color=blue size=-1>' + tran + '</font>)'
    # 为避免误替换单词，被替换的单词前后必须有以下标点的任意一个:
    # 空格,:.'?!@;()\r\n
    # NOTE: 如果一个单词连续出现两次以上，则只会替换第一个

    pattern = re.compile(r'([ ,:\'\.\?!@;(])%s(([ ,:\'\.\?!@;)])|(\r)|(\n))' % w)
    all_text = pattern.sub(r'\1%s\2' % w_tran, all_text)

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", end" )

all_text = all_text.replace('\n', '</br>')

with open('trans_result.html', 'w', encoding='utf-8') as fin:
    fin.write(all_text)

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", wrote to file")