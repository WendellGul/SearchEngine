import logging
import sqlite3
from datetime import datetime

import jieba
import pymysql
from gensim import models
from jieba import analyse

from doc_rating import search_result, bm25f
from permutation_index import LunpaiIndex, load_dict
from utils import *


class SearchEngine(object):
    def __init__(self, db_type='local'):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(asctime)s -%(name)s-%(levelname)s-%(module)s:%(message)s'))
        self.logger.addHandler(ch)

        self.highlight_prefix = '<span style="color:#d90909">'
        self.highlight_suffix = '</span>'

        self.db_type = db_type

        self.logger.info('Start loading resources...')
        load_start_time = datetime.now()
        self.load_resources()
        jieba.load_userdict(WORD_DICT_PATH)
        self.init_db()
        load_end_time = datetime.now()
        self.logger.info('Load resources finished, cost ' + str((load_end_time - load_start_time).total_seconds()) + '.')

    def load_resources(self):
        self.logger.info("Loading field length...")
        self.doc_lens = load_doc_lens()
        self.title_lens = load_title_lens()
        self.field_lens = [self.title_lens, self.doc_lens]

        self.logger.info("Loading inverted indices...")
        self.content_inverted_idx = load_pkl_inverted_idx(CONTENT_INVERTED_IDX_PATH)
        self.title_inverted_idx = load_pkl_inverted_idx(TITLE_INVERTED_IDX_PATH)
        self.inverted_indices = [self.title_inverted_idx, self.content_inverted_idx]
        # self.improved_inverted_index = load_improved_inverted_index()

        self.logger.info("Loading permutation index...")
        self.permutation_idx = LunpaiIndex()
        self.permutation_idx.load()

        self.logger.info("Loading word frequency...")
        self.word_dict = load_dict()

        self.logger.info("Loading news id map...")
        self.doc_id_dict = load_news_doc_id_dict()

        self.logger.info("Loading stopwords...")
        self.stopwords = load_stopwords()

        self.logger.info("Loading comment score file...")
        self.comment_score = load_comment_score()

        self.logger.info("Loading word2vec model...")
        self.word2vec_model = models.Word2Vec.load(WORD2VEC_PATH)

        self.logger.info("Loading hot news...")
        self.hot_news = load_hot_news()

    def init_db(self):
        if self.db_type == 'local':
            self.db = sqlite3.connect(NEWS_DB_PATH)
            self.cursor = self.db.cursor()
        else:
            self.db = pymysql.connect(host='alimysql.gregchan.cn',
                                      user='root',
                                      password='UCASir2017',
                                      db='ir2017',
                                      port=3306,
                                      charset='utf8')
            self.cursor = self.db.cursor()

    def suggest(self, search_text):
        """
        return suggestions from the dictionary with permutation_idx
        :param search_text:
        :return:
        """
        if search_text.find('*') != -1:
            pass
        else:
            query_str = '$' + search_text
            return self.get_suggestions(query_str, search_text)

    def get_suggestions(self, query_str, search_text):
        words = self.permutation_idx.predict_queryindex(query_str)
        result_dict = {}
        for word in words:
            result_dict[word] = self.word_dict[word]
        result_tuple = sorted(result_dict.items(), key=lambda x: x[1], reverse=True)
        result = [key for key, _ in result_tuple]
        if len(result) > 0 and result[0] == search_text:
            result.pop(0)
        if len(result) < 10:
            return result
        else:
            return result[:10]

    def search(self, search_text, page=0, more=0):
        start_time = datetime.now()
        raw_query = remove_enter(search_text)

        star_pos = raw_query.find('*')
        if star_pos != -1:
            if star_pos == len(raw_query) - 1:
                query_str = '$' + raw_query[:star_pos].replace('*', '')
            elif star_pos == 0:
                query_str = raw_query[star_pos + 1:].replace('*', '') + '$'
            else:
                query_str = raw_query[star_pos + 1:].replace('*', '') + '$' + raw_query[:star_pos]
            raw_query = self.get_suggestions(query_str, raw_query.replace('*', ''))[0]

        keyword = analyse.extract_tags(raw_query, 1)[0]

        suggestions = self.get_top_sim([keyword])

        if more:
            raw_terms = analyse.extract_tags(raw_query, 3)
        else:
            raw_terms = jieba.lcut_for_search(raw_query)
        terms = []
        for term in raw_terms:
            if term not in self.stopwords:
                if term in self.content_inverted_idx:
                    terms.append(term)
        if len(terms) == 0:
            return {
                'flag': 0,
                'word': raw_query
            }

        intersect = search_result(terms, self.content_inverted_idx, self.title_inverted_idx)
        doc_list = bm25f(intersect, self.inverted_indices, self.field_lens, self.comment_score, boosts=[0.7, 0.3, 0.1])
        total_nums = len(doc_list)
        hit_list = []
        page_end = (page + 1) * 10 if (page + 1) * 10 < total_nums else total_nums
        page_num = 10 if (page + 1) * 10 < total_nums else total_nums - page * 10
        page_count = total_nums / 10 if total_nums % 10 == 0 else total_nums / 10 + 1
        for i in range(page * 10, page_end):
            doc_id = self.doc_id_dict[doc_list[i][0]]
            if doc_id.startswith('sina'):
                source = '新浪新闻'
                if self.db_type != 'local':
                    doc_id = doc_id[4:]
                table = 'sina_news'
            elif doc_id.startswith('sohu'):
                source = '搜狐新闻'
                if self.db_type != 'local':
                    doc_id = doc_id[4:]
                table = 'sohu_news'
            elif doc_id.startswith('ifeng'):
                source = '凤凰新闻'
                if self.db_type != 'local':
                    doc_id = doc_id[5:]
                table = 'ifeng_news'
            elif doc_id.startswith('thepaper'):
                source = '澎湃新闻'
                if self.db_type != 'local':
                    doc_id = doc_id[8:]
                table = 'thepaper_news'
            elif doc_id.startswith('netease'):
                source = '网易新闻'
                if self.db_type != 'local':
                    doc_id = doc_id[7:]
                table = 'netease_news'
            else:
                raise Exception("Wrong news id.")

            # fetch data from the table in table
            sql = "SELECT * FROM " + table + " where Doc_ID = '" + doc_id + "'"
            self.cursor.execute(sql)
            data = self.cursor.fetchone()
            title, content = data[3], data[4]

            if title.find(raw_query) != -1:
                title = title.replace(raw_query, self.highlight_prefix + raw_query + self.highlight_suffix)
            else:
                for term in terms:
                    title = title.replace(term, self.highlight_prefix + term + self.highlight_suffix)

            pos = content.find(raw_query)
            if pos != -1:
                content = content[0 if pos < 10 else pos - 10: pos + 90]\
                    .replace(raw_query, self.highlight_prefix + raw_query + self.highlight_suffix)
            else:
                for term in terms:
                    content = content[0:100].replace(term, self.highlight_prefix + term + self.highlight_suffix)

            # append data into result
            hit_list.append({
                'id': doc_id,
                'url': data[1],
                'title': title,
                'date': data[2],
                'content': content,
                'source': source,
                'score': doc_list[i][1]
            })
        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        result = {
            'flag': 1,
            'query': search_text,
            'page': page,
            'page_num': page_num,
            'page_count': page_count,
            'total_nums': len(doc_list),
            'all_hits': hit_list,
            'last_seconds': last_seconds,
            'suggestions': suggestions,
            'hot_news': self.hot_news
        }
        print(result)
        return result

    def get_top_sim(self, keyword):
        items = self.word2vec_model.most_similar(keyword, topn=10)
        words = [item[0] for item in items]
        words.sort(key=lambda x: len(x), reverse=True)
        return words[0:5]


def remove_enter(record):
    record = record.replace("'", "")
    record = record.replace(' ', '')
    record = record.replace('\r', '')
    record = record.replace('\n', '')
    record = record.replace('\n\r', '')
    record = record.replace('\t', '')
    return record


def get_hot_news(write_path=HOTTESTED_NEWS_PATH):
    db = pymysql.connect(host='alimysql.gregchan.cn',
                         user='root',
                         password='UCASir2017',
                         db='ir2017',
                         port=3306,
                         charset='utf8')
    cursor = db.cursor()
    hot_news = []
    sql = """
        SELECT Doc_ID, count(*) as comment_count FROM sina_comment GROUP BY Doc_ID ORDER BY comment_count DESC LIMIT 10
    """
    doc_ids = []
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            doc_ids.append(result[0])
    except:
        print('Error: unable to fetch data')
    sql = "SELECT * FROM sina_news WHERE Doc_ID IN " + str(tuple(doc_ids)) + " ORDER BY Doc_datetime DESC"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            hot_news.append((result[1], result[2]))
    except:
        print('Error: unable to fetch data')

    with open(write_path, 'w', encoding='utf8') as f:
        for news in hot_news:
            f.write(news[0] + '\t' + news[1])
            f.write('\n')


if __name__ == '__main__':
    a = "asfdasfa"
    print(a + a[2:].replace('a', 'ff'))
