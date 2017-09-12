#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import re
import os
import sys
import json

from log import log
logger = log(os.path.basename(sys.argv[0]))

FINAL_FILE = 'lemmas/lemmas_final'

"""
将多个渠道获取的lemmas文件合并，生成最终的lemmmas文件

为方便比较、合并, 过程中将所有lemmas文件都转换成以下的字典格式:
{
    'he': {'frequency': 1196022, 'lemmas':['his', 'him', 'they']}
}
key是单词
value也是字典,每个key是相关的属性,至少要有'lemmas'这个key,
如果源文件包含其他属性,则创建新的key，加入value

"""

def parse_lemmas():
    """处理lemmas.txt 下载链接 https://github.com/tsaoye/freeq/blob/master/lemmas.txt
    该文件中,如果单词没有其他形式,则该单词所在行只有一列,即单词本身, 这种单词不会作为结果返回
    单词以tab分隔

    文件内容示例:
    abacus	abaci abacuses

    :param filename:
    :return: {'message': message, 'result': lemmas_dict}
    """
    message = ''
    lemmas_dict = {}
    try:
        with open(u'lemmas/lemmas.txt', 'r', encoding=u'utf-8') as lemmas_file:
            for line in lemmas_file.readlines():
                parts = line.split()
                word = parts[0].lower()
                if len(parts) > 1:
                    lemmas_dict[word] = []
                    for i in range(1, len(parts)):
                        if parts[i].lower() != parts[0]:
                            lemmas_dict[word].append(parts[i].lower())
        message = 'OK'
    except Exception as exc:
        import traceback
        message = 'parse_lemmas failed, exc:%r, detail: %s' % (exc, traceback.format_exc())
        logger.error(message)

    return {'message': message, 'result': lemmas_dict}

def parse_bnc_lemmas():
    """处理AntBNC_lemmas_ver_001.txt
    下载链接 http://www.laurenceanthony.net/resources/wordlists/antbnc_lemmas_ver_001.zip

    文件内容示例:
    aaah	->	aaahed	aaah

    单词 -> 以tab分隔的各种形式

    :param filename:
    :return: {'message': message, 'result': lemmas_dict}
    """
    message = ''
    lemmas_dict = {}
    try:
        with open(u'lemmas/AntBNC_lemmas_ver_001.txt', 'r', encoding=u'utf-8') as lemmas_file:
            for index, line in enumerate(lemmas_file.readlines()):
                parts = line.split()
                word = parts[0].lower()
                lemmas_dict[word] = []
                if len(parts) > 2:
                    for i in range(2, len(parts)):
                        if parts[i].lower() != parts[0]:
                            lemmas_dict[word].append(parts[i].lower())
                else:
                    logger.warning(u'Format is wrong in file AntBNC_lemmas_ver_001.txt, line: %d' % (index + 1))
        message = 'OK'
    except Exception as exc:
        import traceback
        message = 'parse_bnc_lemmas failed, exc:%r, detail: %s' % (exc, traceback.format_exc())
        logger.error(message)

    return {'message': message, 'result': lemmas_dict}

def parse_e_lemmas():
    """处理e_lemma.txt
    下载链接 http://www.laurenceanthony.net/resources/wordlists/e_lemma.zip

    文件内容示例:
    abandon -> abandons,abandoning,abandoned

    格式:
    单词/词频 -> 以逗号分隔的该单词的各种形式

    :param filename:
    :return: {'message': message, 'result': lemmas_dict}
    """
    message = ''
    lemmas_dict = {}
    try:
        with open(u'lemmas/e_lemma.txt', 'r', encoding=u'utf-8') as e_lemmas_file:
            for index, line in enumerate(e_lemmas_file.readlines()):
                if re.match(r'^[a-zA-Z]+', line):
                #if not line.startswith(u'['):
                    parts = line.split()
                    word = parts[0].lower()
                    if len(parts) > 2:
                        lemmas_dict[word] = []
                        # 文件中的lemmmas是以 , 分隔，故需要再split
                        final_parts = parts[2].split(u',')
                        for i in range(0, len(final_parts)):
                            if final_parts[i].lower() != word:
                                lemmas_dict[word].append(final_parts[i].lower())
                    else:
                        logger.warning(u'Format is wrong in file e_lemma.txt, line: %d' % (index + 1))
        message = 'OK'
    except Exception as exc:
        import traceback
        message = 'parse_bnc_lemmas failed, exc:%r, detail: %s' % (exc, traceback.format_exc())
        logger.error(message)

    return {'message': message, 'result': lemmas_dict}


def compare_lemmas(base_lemmas, cmp_lemmas):
    """以 base_lemmas 为基准，循环每个元素
    cmp_lemmas 中与 base_lemmas 单词相同，单词其他形式不同的，结果以 diff_words 返回
    如果 base_lemmas 存在的单词在 cmp_lemmas 中不存在，结果以 not_in_new_lemmas 返回

    1 如果 'lemmmas' 的value为空，则打印warning log
    2 判断 cmp_lemmas 的单词是否在 base_lemmas 中
        2.1 如果在，则判断cmp_lemmas的key 'lemmas' 的value是否为空
            2.1.1 如果不为空，判断单词的其他形式是否完全相同
                2.1.1.1 如果是，same_count 计数加1
                2.1.1.2 如果不是，将结果记录到diff_words
            2.1.2 如果为空，将 base_lemmas 的元素记录到 not_in_new_lemma
        2.2 如果不在，将 base_lemmas 的元素记录到 not_in_new_lemma

    :param base_lemmas:
    :param cmp_lemmas:
    :return:
        same_count
        diff_words
        not_in_new_lemmas
    """
    same_count = 0
    diff_words = {}
    not_in_new_lemmas = {}

    for word, info in base_lemmas.items():
        if info:
            if word in cmp_lemmas:
                new_info = cmp_lemmas.get(word)
                if new_info:
                    a_lemmas = info
                    a_new_lemmas = new_info
                    if a_lemmas.sort() == a_new_lemmas.sort():
                        same_count += 1
                    else:
                        diff_words.setdefault(word, {'base_lemmmas': info, 'new_lemmas': new_info})
                        if a_lemmas.sort() < a_new_lemmas.sort():
                            not_in_new_lemmas.update(word, info)
                else:
                    not_in_new_lemmas.setdefault(word, info)
            else:
                not_in_new_lemmas.setdefault(word, info)
        else:
            logger.warning(u'word: %s, no lemmas in base_lemmas' % word)
    return same_count, diff_words, not_in_new_lemmas


def merge_lemmas():
    """将各个渠道的lemmas文件合并，生成
        FINAL_FILE 每行单词以空格分隔，不会出现只有一个单词的行
        FINAL_FILE+'.json' 与lemmas_final.txt内容相同，json格式存储
    :return:
    """
    message = 'OK'
    lemmas_txt = parse_lemmas()
    bnc_lemmas_txt = parse_bnc_lemmas()
    e_lemmas_txt = parse_e_lemmas()

    message = lemmas_txt.get(u'message')
    if message == 'OK':
        lemmas = lemmas_txt.get(u'result')
    else:
        return message
    message = bnc_lemmas_txt.get(u'message')
    if message == 'OK':
        bnc_lemmas = bnc_lemmas_txt.get(u'result')
    else:
        return message
    message = e_lemmas_txt.get(u'message')
    if message == 'OK':
        e_lemmas = e_lemmas_txt.get(u'result')
    else:
        return message

    print(u'lemmas.txt total: %s' % len(lemmas))
    print(u'AntBNC_lemmas_ver_001.txt total: %s' % len(bnc_lemmas))
    print(u'e_lemma.txt total: %s' % len(e_lemmas))

    same_count, diff_words, not_in_new_lemmas = compare_lemmas(lemmas, bnc_lemmas)
    if diff_words:
        message = 'lemmas vs bnc_lemmas: diff_words is not null.'
        return message
    same_count, diff_words, not_in_new_lemmas = compare_lemmas(lemmas, e_lemmas)
    if diff_words:
        message = 'lemmas vs e_lemmas: diff_words is not null.'
        return message

    same_count, diff_words, not_in_newlemmas_1 = compare_lemmas(bnc_lemmas, lemmas)
    if not diff_words:
        lemmas.update(not_in_newlemmas_1)
    else:
        print(diff_words)
        message = 'Same word has different lemmas, "%s" vs "%s" ' % (bnc_lemmas, lemmas)
        logger.error(message)
        return message
    updated_bnc_count = len(lemmas)

    same_count, diff_words, not_in_new_lemmas_2 = compare_lemmas(e_lemmas, lemmas)
    if not diff_words:
        lemmas.update(not_in_new_lemmas_2)
    else:
        print(diff_words)
        message = 'Same word has different lemmas, "%s" vs "%s" ' % (bnc_lemmas, lemmas)
        logger.error(message)
        return message
    updated_e_count = len(lemmas)
    print(u'updated_bnc_count: %d' % updated_bnc_count, 'updated_e_count: %d' % updated_e_count)

    # write to file
    with open(FINAL_FILE, 'w', encoding=u'utf-8') as lemmas_new:
        for word, value in lemmas.items():
            lemmas_new.write(word + ' ' + ' '.join(value) + '\n')
        same_count, diff_words, not_in_new_lemmas_3 = compare_lemmas(not_in_new_lemmas_2, not_in_newlemmas_1)

        str_lemmas = json.dumps(lemmas)
        with open(FINAL_FILE+'.json', 'w', encoding=u'utf-8') as lemmas_josn:
            lemmas_josn.write(str_lemmas)

        if (len(not_in_new_lemmas_3) + updated_bnc_count) != updated_e_count:
            message = "It seems to be some wrong in Merge lemms."
            return message
    return message

def create_lemmas_dict():
    message = u''
    lemmas_dict= {}
    rev_lemmas_dict = {}
    try:
        with open(u'lemmas/lemmas_final', u'r', encoding=u'utf-8') as lemmas_file:
            temp_lemmas = lemmas_file.readlines()
            for line in temp_lemmas:
                parts = line.split()
                lemmas_dict[parts[0].lower()] = []
                for i in range(1, len(parts)):
                    lemmas_dict[parts[0].lower()].append(parts[i].lower())
                    rev_lemmas_dict[parts[i].lower()] = parts[0].lower()

        with open(u'lemmas/lemmas_dict.json', u'w', encoding=u'utf-8') as lemmas_json:
            lemmas_json.write(json.dumps(lemmas_dict))
        with open(u'lemmas/rev_lemmas_dict.json', u'w', encoding=u'utf-8') as rev_lemmas_json:
            rev_lemmas_json.write(json.dumps(rev_lemmas_dict))
        message = u'OK'
    except Exception as exc:
        import traceback
        message = 'FAILED: create_lemmas_dict, exc:%r, detail: %s' % (exc, traceback.format_exc())
        logger.error(message)

    return message

def create_quick_search():
    """将lemmas文件划分成以下两个文件，用于快速搜索：
    lemmas_qs_extra.txt 对lemmas_quick_search.txt 的补充：使用字典存储，任何一个lemma与单词的开头字母不同，存到这个文件中
        {
            'I': ['me'],
        }
    lemmas_qs.txt 二级字典格式存储，第一级key是26个字母，value也是字典
        {
            'a': {
                    'a': ['an'],
                    'abacus': ['abaci', 'abacuses'],
                    ...
                }
            'b': {...}
            ...
            'z': {...}
        }

    :return:
    """
    lemmas_qs = {}
    lemmas_qs_extra = {}
    message = u''
    try:
        with open(FINAL_FILE, 'r', encoding=u'utf-8') as lemmas_final_file:
            for line in lemmas_final_file.readlines():
                parts = line.split()
                # merge_lemmas保证lemmas_final.txt 每行的单词至少有两个，故不判断parts的长度是否大于1
                for i in range(1, len(parts)):
                    if parts[i][0] != parts[0][0]:
                        lemmas_qs_extra.setdefault(parts[0], parts[1:])
                        break
                if not lemmas_qs_extra.get(parts[0]):
                    alpha_lemmas = lemmas_qs.setdefault(parts[0][0], {})
                    alpha_lemmas[parts[0]] = parts[1:]

        with open(u'lemmas/lemmas_qs.json', 'w', encoding=u'utf-8') as lemmas_qs_file:
            lemmas_qs_file.write(json.dumps(lemmas_qs))
        with open(u'lemmas/lemmas_qs_extra.json', 'w', encoding=u'utf-8') as lemmas_qs_extra_file:
            lemmas_qs_extra_file.write(json.dumps(lemmas_qs_extra))
        message = u'OK'
    except Exception as exc:
        import traceback
        message = 'FAILED: create_quick_search, exc:%r, detail: %s' % (exc, traceback.format_exc())
        logger.error(message)
    return message

def test_lemmas_qs():
    lemmas_qs_all = {}
    with open(FINAL_FILE+'.json', 'r', encoding=u'utf-8') as lemmas_final_json_file:
        lemmas_final_json = json.loads(lemmas_final_json_file.read())
    with open(u'lemmas/lemmas_qs.json', 'r', encoding=u'utf-8') as lemmas_qs_file:
        lemmas_qs = json.loads(lemmas_qs_file.read())
    with open(u'lemmas/lemmas_qs_extra.json', 'r', encoding=u'utf-8') as lemmas_qs_extra_file:
        lemmas_qs_extra = json.loads(lemmas_qs_extra_file.read())

    for alpha_lemmas in lemmas_qs.values():
        lemmas_qs_all.update(alpha_lemmas)
    lemmas_qs_all.update(lemmas_qs_extra)

    import operator
    if not operator.eq(lemmas_qs_all, lemmas_final_json):
        logger.error(u'lemmas_qs != lemmas_final')
    if lemmas_qs_all.keys() != lemmas_final_json.keys():
        print(u'key !=')
    else:
        for key, value in lemmas_qs_all.items():
            if value != lemmas_final_json.get(key):
                print(u'FAILED: %s, %s' % (value, lemmas_final_json.get(key)))

def main():
    message1 = merge_lemmas()
    if message1 == 'OK':
        message2 = create_quick_search()
        if message2 == "OK":
            test_lemmas_qs()
        else:
            print(message2)

        message3 = create_lemmas_dict()
        if message3 != "OK":
            print(message3)
    else:
        print(message1)

if __name__ == '__main__':
    main()
