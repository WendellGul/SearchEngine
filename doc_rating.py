"""
查询：      ( 输入：词典词项 倒排索引 输出：查询结果)
文档评分(BM25 自定义评分(相关度、时间、热度 、标题正文))
snippet生成
"""

import math
import time

from utils import *


def search_result(terms, content_inverted_idx, title_inverted_idx):
    """
    根据查询词项和倒排索引得到相关文档
    :param terms: 查询词项
    :param content_inverted_idx
    :param title_inverted_idx
    :return:
    """
    terms_content_index = [content_inverted_idx[term] for term in terms]
    terms_content_index.sort(key=lambda x: x['df'], reverse=True)
    terms_title_index = []
    for term in terms:
        if term in title_inverted_idx:
            terms_title_index.append(title_inverted_idx[term])

    title_list = []
    if len(terms_title_index) > 0:
        terms_title_index.sort(key=lambda x: x['df'], reverse=True)
        print(terms_title_index)
        title_list = intersect([item['idx'] for item in terms_title_index])
        print(title_list)
    doc_list = intersect([item['idx'] for item in terms_content_index])
    if len(doc_list) == 0:
        doc_list = title_list
    return {
        'terms': terms,
        'docs': doc_list,
        'titles': title_list
    }


def intersect(indices):
    """
    返回倒排索引的交集
    :param indices: 倒排索引
    :return:
    """
    if len(indices) == 1:
        return indices[0]
    idx = intersect2(indices[-1], indices[-2])
    indices.pop()
    indices.pop()
    indices.append(idx)
    return intersect(indices)


def intersect2(idx1, idx2):
    i, j, result = 0, 0, []
    while i < len(idx1) and j < len(idx2):
        # print(idx1[i], idx2[j])
        if idx1[i]['doc_id'] == idx2[j]['doc_id']:
            tf = [idx2[j]['tf']]
            if isinstance(idx1[i]['tf'], list):
                tf.extend(idx1[i]['tf'])
            else:
                tf.append(idx1[i]['tf'])
            result.append({
                'doc_id': idx1[i]['doc_id'],
                'tf': tf,
            })
            i += 1
            j += 1
        elif idx1[i]['doc_id'] < idx2[j]['doc_id']:
            i += 1
        else:
            j += 1
    return result


def bm25(input, inverted_idx, dict_doclen, k=2, b=0.75):
    items = input['terms']
    docs = input['docs']
    # print (len(docs))
    docs_id = []
    for i in docs:
        docs_id.append(i['idx']['doc_id'])

    # 计算相关文档的平均文档长度
    avdl = 0
    for doc in docs_id:
        # print (doc,type(doc))
        avdl += dict_doclen[str(doc)]

    avdl = avdl/len(docs_id)
    N = len(dict_doclen)

    # print(len(docs_id))
    # print (len(items))

    result = []
    for doc in docs_id:
        grade = 0.
        for item in items:
            df_i = inverted_idx[item]['df']
            idf = math.log(N/df_i)
            # print (idf)
            dl = dict_doclen[str(doc)]
            tf_i = int(inverted_idx[item]['idx'][doc])
            grade += ((k+1)*tf_i)/(k*((1-b)+b*dl/avdl)+tf_i)
        result.append([doc, grade])
    result = sorted(result, key=lambda x: x[1], reverse=True)
    # print (len(result))
    return result


def bm25f(result, inverted_indices, field_lens, comment_score, boosts, k=2, b=0.75):
    """
    calculate the bm25f score of each doc of the result and rank the docs with the scores
    :param result: the return of function search_result
    :param inverted_indices: list of all field indices [title_index, content_index]
    :param field_lens: list of all field length
    :param comment_score: dict of doc comment score
    :param boosts: list of each field weight
    :param k: parameter k
    :param b: parameter b
    :return: the rank of search_result
    """
    fields_num = len(inverted_indices)
    doc_num = len(field_lens[1])

    if len(result['docs']) == 0:
        return None

    # get all docs in the result
    doc_ids = []
    doc_tfs = {}
    for doc in result['docs']:
        doc_id = doc['doc_id']
        doc_ids.append(doc_id)
        doc_tfs[doc_id] = doc['tf']
        if isinstance(doc_tfs[doc_id], int):
            doc_tfs[doc_id] = [doc_tfs[doc_id]]
        else:
            doc_tfs[doc_id].reverse()

    # get title term frequencies
    title_tfs = {}
    for title in result['titles']:
        doc_id = title['doc_id']
        title_tfs[doc_id] = title['tf']
        if isinstance(title_tfs[doc_id], int):
            title_tfs[doc_id] = [title_tfs[doc_id]]
        else:
            title_tfs[doc_id].reverse()

    # calculate average length of each field
    ave_l = [0] * fields_num
    for i in range(fields_num):
        for key in doc_ids:
            ave_l[i] += field_lens[i][str(key)]
        ave_l[i] /= len(doc_ids)

    # get all terms in the query
    terms = result['terms']

    # get the weight of every term in every doc
    weights = {}
    for i in range(len(terms)):
        term = terms[i]
        weight = {}
        for key in doc_ids:
            weight[key] = 0.0
            for j in range(fields_num):
                if j == 0:
                    tf = 0 if key not in title_tfs else title_tfs[key][i]
                else:
                    tf = doc_tfs[key][i]
                weight[key] += (tf * boosts[j]) / ((1 - b) + b * field_lens[j][str(key)])
        weights[term] = weight

    # generate the final result
    result = []
    for key in doc_ids:
        score = boosts[-1] * comment_score[str(key)] if key in comment_score else 0.0
        for term in terms:
            df = inverted_indices[1][term]['df']
            idf = math.log((doc_num - df + 0.5) / (df + 0.5))
            score += (1 - boosts[-1]) * (weights[term][key] * idf) / (k + weights[term][key])
        result.append((key, score))
    result.sort(key=lambda x: x[1], reverse=True)
    return result


if __name__ == '__main__':
    start = time.time()
    inverted_idx = load_pkl_inverted_idx()

    title_inverted_idx = load_pkl_inverted_idx(TITLE_INVERTED_IDX_PATH)

    comment_score = load_comment_score()

    dict_doclen = load_doc_lens()

    title_lens = load_title_lens()

    improved_inverted_index = load_improved_inverted_index()

    end = time.time()
    print(end - start)

    start = time.time()
    interset = search_result(['库克', '竟', '电脑', '果粉'], inverted_idx, title_inverted_idx)
    # result = bm25(interset,improved_inverted_index,dict_doclen)
    result = bm25f(interset, [title_inverted_idx, inverted_idx], [title_lens, dict_doclen], comment_score,
                   boosts=[0.7, 0.3, 0.1])
    end = time.time()
    print(end - start)
    print(result)
    # print(result)
