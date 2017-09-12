#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import re
import string
from collections import Counter


lemmas = {}
with open('lemmas.txt') as fin:
    for line in fin:
        line = line.strip()
        headword = line.split('\t')[0]
        try:
            related = line.split('\t')[1]
        except IndexError:
            related = None
        lemmas[headword] = related


valid_words = set()
for headword, related in lemmas.items():
    valid_words.add(headword)
    if related:
        valid_words.update(set(related.split()))


main_table = {}
for char in string.ascii_lowercase:
    main_table[char] = {}

special_table = {}

for headword, related in lemmas.items():
    headword = headword.lower()
    try:
        related = related.lower()
    except AttributeError:
        related = None
    if related:
        for word in related.split():
            if word[0] != headword[0]:
                special_table[headword] = set(related.split())
                break
        else:
             main_table[headword[0]][headword] = set(related.split())
    else:
        main_table[headword[0]][headword] = None


def find_headword(word):
    word = word.lower()
    alpha_table = main_table[word[0]]
    if word in alpha_table:
        return word

    for headword, related in alpha_table.items():
        if related and (word in related):
            return headword

    for headword, related in special_table.items():
        if word == headword:
            return word
        if word in related:
            return headword

    return word


def is_dirt(word):
    return word not in valid_words


with open('shorthistory.txt','r', encoding='utf-8') as ft:
    content = ft.read().lower()
    temp_list = re.split(r'\b([a-zA-Z-]+)\b', content)
    temp_list = [item for item in temp_list if not is_dirt(item)]
    stemp_list = [find_headword(item) for item in temp_list]


cnt = Counter()
for word in stemp_list:
    cnt[word] += 1


report = sorted(cnt.items(), key=lambda x: x[1], reverse=True)


for row in report:
    print(row[0], row[1])


with open('output_file.txt', 'w') as output:
    for x in report:
        output.write(x[0] + ' ' + str(x[1]) + '\n')