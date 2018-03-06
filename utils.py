import codecs
import csv
import pickle

from settings import *


def load_inverted_index(file_path, write_file=CONTENT_INVERTED_IDX_PATH):
    """
    generate inverted index structure and save it.
    :param file_path:
    :param write_file:
    :return:
    """
    inverted_idx = {}
    with codecs.open(file_path, 'r', encoding='utf8') as f:
        rows = csv.reader(f, delimiter='\t')
        for row in rows:
            if len(row) > 2:
                idx_item = {
                    'idx': [],  # the index list corresponding to the term
                    'df': 0,  # doc frequency
                }
                for i in range(1, len(row)):
                    if row[i] == "":
                        continue
                    doc_id, tf_and_pos = row[i].split(':')
                    tf_and_pos_list = tf_and_pos.replace('\n', '').split(',')

                    # each index info in the index list
                    idx_info = {
                        'doc_id': int(doc_id),  # doc id
                        'tf': int(tf_and_pos_list[0]),  # term frequency
                    }
                    idx_item['df'] += 1
                    idx_item['idx'].append(idx_info)
                inverted_idx[row[0]] = idx_item
    with open(write_file, 'wb') as f:
        pickle.dump(inverted_idx, f)
    return inverted_idx


def load_pkl_inverted_idx(file_path=CONTENT_INVERTED_IDX_PATH):
    with codecs.open(file_path, 'rb') as f:
        inverted_idx = pickle.load(f)
    return inverted_idx


def load_news_doc_id_dict(file_path=NEWS_DOC_ID_DICT_PATH):
    doc_id_dict = []
    with open(file_path, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            doc_id_dict.append(line.split()[0])
            line = f.readline()
    return doc_id_dict


def load_doc_lens(file_path=DOC_WORDS_COUNT_PATH):
    dict_doc_lens = {}
    f = open(file_path, 'r', encoding='utf8')
    while True:
        line = f.readline()
        if len(line) <= 1:
            break
        key, value = line.strip().split('\t')
        dict_doc_lens[key] = int(value)
    return dict_doc_lens


def load_title_lens(file_path=TITLE_WORDS_COUNT_PATH):
    dict_title_len = {}
    with open(file_path, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            key, value = line.strip().split('\t')
            dict_title_len[key] = int(value)
            line = f.readline()
    return dict_title_len


def init_improved_inverted_index(write_file=IMPROVED_INVERTED_IDX_PATH):
    improved_inverted_index = load_pkl_inverted_idx()
    for i in improved_inverted_index.keys():
        tmp_dict = {}
        for j in improved_inverted_index[i]['idx']:
            tmp_dict[j['doc_id']] = j['tf']
            # print (j['doc_id'],j['tf'])
            improved_inverted_index[i]['idx'] = tmp_dict
    with open(write_file, 'wb') as f:
        pickle.dump(improved_inverted_index, f)
    print(len(improved_inverted_index))


def load_improved_inverted_index(file_path=IMPROVED_INVERTED_IDX_PATH):
    with codecs.open(file_path, 'rb') as f:
        improved_inverted_index = pickle.load(f)
    return improved_inverted_index


def load_stopwords(file_path=STOPWORDS_PATH):
    stopwords = []
    with open(file_path, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            stopwords.append(line.strip())
            line = f.readline()
    return stopwords


def load_comment_score(file_path=COMMENT_SCORE_PATH):
    comment_score = {}
    with open(file_path, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            item = line.strip().split()
            comment_score[item[0]] = float(item[1])
            line = f.readline()
    return comment_score


def load_hot_news(file_path=HOTTESTED_NEWS_PATH):
    hot_news = []
    with open(file_path, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            url, title = line.strip().split('\t')
            title = title.replace(' ', ',')
            hot_news.append((url, title))
            line = f.readline()
    return hot_news


if __name__ == '__main__':
    load_inverted_index(file_path=CONTENT_IR_PATH, write_file=CONTENT_INVERTED_IDX_PATH)
    load_inverted_index(file_path=TITLE_IR_PATH, write_file=TITLE_INVERTED_IDX_PATH)
    # init_improved_inverted_index()
    print()

