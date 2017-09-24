#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-

import re
import json
import os
import sys
import argparse
import collections
import csv
import traceback

from log import log
logger = log(os.path.basename(sys.argv[0]))

LEMMAS_QS_JSON_FILE = u'lemmas/lemmas_qs.json'
LEMMAS_QS_EXTRA_JSON_FILE = u'lemmas/lemmas_qs_extra.json'
REVERSE_LEMMAS_JSON_FILE = u'lemmas/rev_lemmas.json'

class AllText(object):
    def __init__(self, file_path):
        """
        :param file_path:

        生成以下私有变量：
        __file_path string, 输入的文件名
        __all_text  string. 全文

        __words             list, 未去重的所有单词
        __words_cnt         dict, 根据原始文本统计的词频，未作任何筛除{word: frequency, ...}
        __words_distinct    set, 去重后的所有单词，包含了各种形式

        # 单词均为小写
        __lower_word          list,
        __lower_words_cnt      dict
        __lower_words_distinct set

        """
        try:
            with open(file_path, u'r', encoding=u'utf-8') as allText_file:
                self.__file_path = file_path
                # 将中文 单引号、双引号 替换为 相应的英文标点
                self.__all_text = allText_file.read().replace(u"‘", u"'").replace(u'’', u"'").\
                    replace(u'“', u'"').replace(u'”', u'"')

                self.__words = self.parse_text(self.__all_text)
                self.__words_cnt = dict(collections.Counter(self.__words))
                self.__words_distinct = set(self.__words)

                self.__lower_word = [word.lower() for word in self.__words]
                self.__lower_words_cnt = dict(collections.Counter(self.__lower_word))
                self.__lower_words_distinct = set(self.__lower_word)
        except Exception as exc:
            message = u'FAILED: Open "%s", exc:%r, detail: %s' % (file_path, exc, traceback.format_exc())
            logger.error(message)

    def parse_text(self, text):
        """根据输入的文本，返回解析后的单词列表
        处理以下缩写：
        n't  's  're   'd   've  'll
        中文单引号、双引号
        :param text:
        :return:
        """
        # 先将标点符号替换为空格，除了 单引号。因为 部分单词的缩写会使用单引号，在后面进行处理
        temp_words = text.replace(u'.', u' ').replace(u'?', u' ').replace('!', ' ').replace(u';', u' ').\
            replace(u',', u' ').replace(u':', u' ').replace(u'(', u' ').replace(u')', u' ').replace(u'{', u' '). \
            replace(u'}', u' ').replace(u'[', u' ').replace(u']', u' ').replace(u'_', u' ').replace(u'"', u' ').\
            replace(u'-\r\n', u'-').replace(u'-\n', u'-').replace('—', ' ').replace('--', ' ').split()
        short_words = [u"n't", u"'re", u"'s", u"'d", u"'ve", u"'ll"]
        words = []
        for w in temp_words:
            w = w.replace(u' ', u'')
            if w:
                is_short = False
                for s_w in short_words:
                    if w.endswith(s_w):
                        words.extend(self.__parse_no_short_words(w.split(s_w)[0]))
                        words.append(s_w)
                        is_short = True
                        break
                if not is_short:
                    words.extend(self.__parse_no_short_words(w))
        return words

    def __parse_no_short_words(self, text):
        """处理不含缩写的文本，返回解析后的单词列表
        前面已经替换了除  '—' '--' "'" "’" 的标点
        :param text:
        :return:
        """
        words = []
        if text and text[0].isalpha():
            if text[-1] == '-':
                text = text[:-1]

            # 去除 非 字母和- 的字符
            words.append(''.join([x for x in text if x.isalpha() or x == '-']))
        return words

    def get_all_text(self):
        return self.__all_text

    def get_words_list(self):
        return self.__words

    def get_words_count(self):
        """
        :return: dict
        """
        return self.__words_cnt

    def get_words_distinct(self):
        """
        :return: set
        """
        return self.__words_distinct

    def get_lower_words(self):
        return self.__lower_words

    def get_lower_word_cnt(self):
        """
        :return: dict
        """
        return self.__lower_words_cnt

    def get_lower_words_distinct(self):
        """
        :return: set
        """
        return self.__lower_words_distinct

    def get_del_lemma_words(self):
        """使用文本的小写单词列表
        如果遇到异常，返回 原文单词列表 (or 终止 程序?)
        :return: 单词均为小写
        """
        from lemmas import create_lemmas_file
        create_lemmas_file()
        try:
            with open(LEMMAS_QS_JSON_FILE, u'r', encoding=u'utf-8') as lemmas_qs_file:
                self.__lemmas_qs = json.loads(lemmas_qs_file.read())
            with open(LEMMAS_QS_EXTRA_JSON_FILE, u'r', encoding=u'utf-8') as lemmas_qs_extra_file:
                self.__lemmas_qs_extra = json.loads(lemmas_qs_extra_file.read())
            return [self.get_base_word(word) for word in self.__lower_word]
        except Exception as exc:
            message = u'FAILED: handle lemmms_qs.json/lemmas_qs_extra.json, exc:%r, detail: %s' % (
                exc, traceback.format_exc())
            logger.error(message)
            return self.__lower_word

    def get_del_lemma_words_cnt(self):
        """单词均为小写
        :return: dict
        """
        return dict(collections.Counter(self.get_del_lemma_words()))

    def get_del_lemma_words_distinct(self):
        """单词均为小写
        :return: set
        """
        return set(self.get_del_lemma_words())

    def get_base_word(self, word):
        """返回单词的原形，如果lemmas表中没有找到，则返回该单词本身
        :param word:
        :return:
        """
        if word:
            alpha_lemmas = self.__lemmas_qs.get(word[0])
            if word in alpha_lemmas:
                # word is base_word
                return word
            else:
                for base_word, a_lemmas in alpha_lemmas.items():
                    if a_lemmas and (word in a_lemmas):
                        return base_word
            for base_word, a_lemmas in self.__lemmas_qs_extra.items():
                if word in a_lemmas:
                    return base_word
        return word

    def get_hard_words(self, frequency=0, vocabulary=u'', del_lemmas=True):
        """根据去重后的原型单词列表，返回难词表
        :return: set
        """
        if frequency > 0:
            return self.del_by_frq(frequency, del_lemmas=del_lemmas)
        elif vocabulary:
            return self.del_by_vocab(vocabulary, del_lemmas=del_lemmas)
        else:
            return set()

    def del_by_frq(self, frequency=0, del_lemmas=True):
        """
        如果 del_lemmas 为True：
            以去重、去lemmas的 __del_lemma_words_distinct 为基准
        否则：
            将文本中去重后的小写单词作为基准
        再：根据词频表 移除单词、根据简单词表 移除单词

        NOTE: windows下文件另存为utf8，注意另存为 utf-8 无BOM头 格式，否则Windows会在文件开始处添加BOM头EF BB
        :param frequency: int
        :return: set
        """
        if frequency > 0:
            del_lemma_words_distinct = self.get_del_lemma_words_distinct()
            if del_lemmas:
                hard_words = del_lemma_words_distinct
            else:
                hard_words = self.__lower_words_distinct
            simple_words = self.__load_simple_words()
            with open(u'vocabulary/COCA60000.txt', u'r', encoding=u'utf-8') as coca:
                coca_list = coca.readlines()
                for word in coca_list[:frequency]:
                    word = word.lower().strip()
                    if word in del_lemma_words_distinct:
                        if word in hard_words:
                            hard_words.remove(word)
                for word in simple_words:
                    if word in del_lemma_words_distinct:
                        if word in hard_words:
                            hard_words.remove(word)
            return hard_words

    def del_by_vocab(self, vocabulary=u'', del_lemmas=True):
        """
        :param vocabulary:
        :return: set
        """
        simple_words = self.__load_simple_words()
        del_lemma_words_distinct = self.get_del_lemma_words_distinct()
        hard_words = set()

        if del_lemmas:
            hard_words = set(del_lemma_words_distinct).difference(simple_words)
        else:
            hard_words = set(self.__lower_words_distinct).difference(simple_words)
        if vocabulary == u'HIGHSCHOOL':
            high_school_words = self.__load_high_school_words()
            hard_words = hard_words.difference(high_school_words)
        elif vocabulary == u'CET4':
            pass
        elif vocabulary == u'CET6':
            hard_words = hard_words.difference(self.__load_high_school_words())
            hard_words = hard_words.difference(self.__load_cet6_words())
        elif vocabulary == u'IELTS':
            pass
        elif vocabulary == u'TOEFL':
            hard_words = hard_words.difference(self.__load_high_school_words())
            hard_words = hard_words.difference(self.__load_cet6_words())
            hard_words = hard_words.difference(self.__load_toefl_words())
        elif vocabulary == u'GRE':
            hard_words = hard_words.difference(self.__load_high_school_words())
            hard_words = hard_words.difference(self.__load_cet6_words())
            hard_words = hard_words.difference(self.__load_toefl_words())
            hard_words = hard_words.difference(self.__load_gre_words())
        return hard_words

    def __load_simple_words(self):
        """加载 简单词 表
        :return: simple_words, set
        """
        simple_words = set()
        try:
            with open(u'vocabulary/simple_words.txt', u'r', encoding=u'utf-8') as simple:
                for w in simple.readlines():
                    if not w.startswith('#'):
                        simple_words.add(w.strip().lower())
        except Exception as exc:
            message = u'FAILED: handle FILE simple_words, exc:%r, detail: %s' % (exc, traceback.format_exc())
            logger.error(message)
        return simple_words

    def __load_high_school_words(self):
        """加载 HIGHSCHOOL 词汇表
        :return: high_school_words, set
        """
        high_school_words = set()
        try:
            with open(u'vocabulary/highschool_edited.txt', u'r', encoding=u'utf-8') as high_school:
                for w in high_school.readlines():
                    high_school_words.add(w.strip().lower())
        except Exception as exc:
            message = u'FAILED: handle File high school, exc:%r, detail: %s' % (exc, traceback.format_exc())
            logger.error(message)
        return high_school_words

    def __load_cet6_words(self):
        """加载 CET6 词汇表
        :return: cet6_words, set
        """
        cet6_words = set()
        try:
            with open(u'vocabulary/CET6_edited.txt', u'r', encoding=u'utf-8') as cet6:
                for w in cet6.readlines():
                    cet6_words.add(w.strip().lower())
        except Exception as exc:
            message = u'FAILED: handle File cet6, exc:%r, detail: %s' % (exc, traceback.format_exc())
            logger.error(message)
        return cet6_words

    def __load_toefl_words(self):
        """加载 TOEFL 词汇表
        :return: toefl_words, set
        """
        toefl_words = set()
        try:
            with open(u'vocabulary/WordList_TOEFL.txt', u'r', encoding=u'utf-8') as toefl:
                for w in toefl.readlines():
                    toefl_words.add(w.strip().lower())
        except Exception as exc:
            message = u'FAILED: handle File TOEFL, exc:%r, detail: %s' % (exc, traceback.format_exc())
            logger.error(message)
        return toefl_words

    def __load_gre_words(self):
        """加载 GRE 词汇表
        :return: gre_words, set
        """
        gre_words = set()
        try:
            with open(u'vocabulary/WordList_GRE.txt', u'r', encoding=u'utf-8') as gre:
                for w in gre.readlines():
                    gre_words.add(w.strip().lower())
        except Exception as exc:
            message = u'FAILED: handle File GRE, exc:%r, detail: %s' % (exc, traceback.format_exc())
            logger.error(message)
        return gre_words

    def get_translated(self, words=[], frequency=0, vocabulary=u''):
        """
        :param words: 用户指定要翻译的单词表
        :param frequency: 指定剔除 词频在frequency以内的单词
        :param vocabulary: 指定 提出 某个词汇表，支持 'CET4'  'CET6' 'TOEFL' 'GRE'
        :return:
        """
        hard_words = set(words)
        if frequency:
            hard_words = hard_words.union(self.del_by_frq(frequency=frequency))
        elif vocabulary:
            hard_words = hard_words.union(self.del_by_vocab(vocabulary=vocabulary))
        if hard_words:
            words_trans = self.get_words_tans(hard_words)
        else:
            words_trans = self.get_words_tans(self.__words_distinct)
        all_text_trans = self.__all_text
        for w, tran in words_trans.items():
            if tran:
                # 替换之外，给生词和翻译加上html格式
                w_tran = u'<font color=red>' + w + '</font>' + '(<font color=blue size=-1>' + tran + '</font>)'
                # 为避免误替换单词，被替换的单词前后必须有以下标点的任意一个:
                # 空格,:.'"?!@;()\r\n
                # NOTE: 如果一个单词连续出现两次以上，则只会替换第一个
                pattern = re.compile(r'([ ,:\'\"\.\?!@;(\n])%s([ ,:\'\"\.\?!@;)\n])' % w)
                all_text_trans = pattern.sub(r'\1%s\2' % w_tran, all_text_trans)

        all_text_trans = all_text_trans.replace(u'\n', u'</br>')

        with open(self.__file_path + u'-trans.html', u'w', encoding=u'utf-8') as fout:
            fout.write(all_text_trans)

    def __load_dictionary(self):
        """加载 英汉词典
        :return:
        """
        dictionary = {}
        #with open(u'dictionary/vivo_edited.csv', u'r', encoding=u'utf-8') as ec:
        with open(u'dictionary/简明英汉词典（vivo_edited）.csv', u'r') as ec:
            f_ecdict = csv.reader(ec)
            headers = next(f_ecdict)
            for row in f_ecdict:
                # NOTE: 将词典的 key转换为小写
                dictionary[row[0].lower()] = row[1]
            return dictionary

    def __get_orignal_words(self, words):
        """根据 words 中传入的单词，查找原文的单词
        :param words: list
        :return:
        """
        orignal_words = set()
        for w in self.__words:
            if w in words:
                orignal_words.add(w)
            elif w.lower() in words:
                orignal_words.add(w)
        return orignal_words

    def get_words_tans(self, words=[]):
        """如果单词没有解释，则查询其是否有原型单词，如有，使用其原型单词的解释
        :param words:
        :param dictionary:
        :return:
        """
        dictionary = self.__load_dictionary()
        words = self.__get_orignal_words(words)
        words_trans = {}
        get_lemmas_dict = self.__get_rev_lemmas()
        if get_lemmas_dict.get(u'message') == u'OK':
            rev_lemmas_dict = get_lemmas_dict.get(u'rev_lemmas_dict')
            for w in words:
                lower_w = w.lower()
                trans = dictionary.get(lower_w)
                if trans:
                    words_trans[w] = dictionary.get(lower_w)
                else:
                    org_word = rev_lemmas_dict.get(lower_w)
                    if not org_word:
                        logger.warning(u'%s, No translation' % w)
                    else:
                        org_trans = dictionary.get(org_word.lower())
                        if not org_trans:
                            logger.warning(u'%s, No translation' % w)
                        else:
                            words_trans[w] = org_trans
        return words_trans

    def __get_rev_lemmas(self):
        """
        :return:
        """
        rev_lemmas_dict = {}
        message = u''
        try:
            with open(REVERSE_LEMMAS_JSON_FILE, u'r', encoding=u'utf-8') as rev_lemmas_dict_file:
                rev_lemmas_dict = json.loads(rev_lemmas_dict_file.read())
            message = u'OK'
        except Exception as exc:
            import traceback
            message = u'FAILED: handle rev_lemmas_dict.json, exc:%r, detail: %s' % (exc, traceback.format_exc())
            logger.error(message)
        return {u'message': message, u'rev_lemmas_dict': rev_lemmas_dict}

def main():
    import time
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", begin to init")
    #allText = AllText(u'tests/ShortHistory.txt')
    #allText = AllText(u'tests/1342-0.txt')
    allText = AllText(u'tests/pg1260.txt')
    #allText = AllText(u'tests/driveless.txt')
    #allText = AllText(u'tests/test.txt')
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", start to get hard words")
    #hard_words = allText.get_hard_words(count=5000)
    hard_words = allText.get_hard_words(vocabulary=u'HIGHSCHOOL')
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", deleted HIGHSCHOOL: " + str(len(hard_words)))
    hard_words = allText.get_hard_words(vocabulary=u'CET6')
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", deleted CET6: " + str(len(hard_words)))
    hard_words = allText.get_hard_words(vocabulary=u'TOEFL')
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", deleted TOEFL: " + str(len(hard_words)))
    hard_words = allText.get_hard_words(vocabulary=u'GRE')
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", deleted GRE: " + str(len(hard_words)))
    print(hard_words)

    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", begin to transalte")
    #trans_allText = allText.get_translated()
    #trans_allText = allText.get_translated(vocabulary=u'CET6')
    trans_allText = allText.get_translated(vocabulary=u'GRE')
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ", wrote to file")

if __name__ == '__main__':
    main()