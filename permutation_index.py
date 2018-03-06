import pickle

from settings import *


class LunpaiIndex(object):
    def __init__(self, input=None):
        self.input = input
        self.trie = {}
        self.lunpai_dict = {}
        self.prefix_dict = {}

    def lunpai(self,item):
        item += '$'
        tmp_list = []
        for k in range(len(item)):
            tmp = item[k:] + item[:k]
            tmp_list.append(tmp)
        return tmp_list

    def lunpai_listify(self):
        lunpai_list = []
        for item in self.input:
            tmp_list = self.lunpai(item)
            lunpai_list+=tmp_list
            for j in tmp_list:
                self.lunpai_dict[j] = item
        return lunpai_list

    # 字典结构 构建轮排索引
    # 构建字典树
    def init_trie(self):
        lunpai_list = self.lunpai_listify()
        for word in lunpai_list:
            p = self.trie
            for c in word:
                if c not in p:
                    p[c] = {}
                p = p[c]

    # 查找字符串
    def trie_querystr(self,query):
        p= self.trie
        for c in query:
            if c in p:
                p = p[c]
        if p == {}:
            print ('true')
            return True
        else:
            print ('false')
            return False

    # 前缀查找
    def trie_queryindex(self,query):
        p = self.trie
        for c in query:
            if c in p:
                p = p[c]
            else:
                p = None
                break

        result = []
        mystack = []
        mystack.append((query,p))

        if p!= None :
            while(mystack):
                item = mystack[0]
                mystack.pop(0)
                mytree = item[1]
                mystr = item[0]
                if mytree =={}:
                    result.append(mystr)
                else:
                    for i in mytree.keys():
                        tmp_str = mystr
                        tmp_str+=i
                        tmp_tree = mytree[i].copy()
                        mystack.append((tmp_str,tmp_tree))
            # print ('true')
            print(result)
        else:
            print ('false')

        tmp = []
        for i in result:
            print(self.lunpai_dict[i])
            tmp.append(self.lunpai_dict[i])
        return tmp


    # 前缀数组构建轮排索引
    def init_prefixdict(self):
        lunpai_list = self.lunpai_listify()
        for word in lunpai_list:
            # print (word)
            for c in range(1,len(word)+1):
                tmp_word = word[:c]
                if tmp_word not in self.prefix_dict.keys():
                    self.prefix_dict[tmp_word] =[]
                self.prefix_dict[tmp_word].append(word)
                # print (tmp_word)
        # for i in self.prefix_dict.keys():
            # print (i,self.prefix_dict[i])


    # 查找字符串
    def predict_querystr(self,query):

        if query in self.prefix_dict.keys():
            print ('true')
            return True
        else:
            print ('false')
            return False

    # 前缀查找
    def predict_queryindex(self,query):
        result = []
        if query in self.prefix_dict.keys():
            result = self.prefix_dict[query]
        tmp = []
        for i in result:
            tmp.append(self.lunpai_dict[i])
        return tmp

    def save(self, save_path=PERMUTATION_IDX_PATH):
        with open(save_path, 'wb') as f:
            pickle.dump((self.trie, self.lunpai_dict, self.prefix_dict), f)

    def load(self, load_path=PERMUTATION_IDX_PATH):
        with open(load_path, 'rb') as f:
            self.trie, self.lunpai_dict, self.prefix_dict = pickle.load(f)


def load_dict(dict_path=WORD_DICT_PATH):
    word_dict = {}
    with open(dict_path, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            key, value, _ = line.split()
            word_dict[key] = int(value)
            line = f.readline()
    return word_dict


if __name__ == '__main__':
    # words = load_dict()
    #
    # tmp = LunpaiIndex(words.keys())
    # tmp.init_prefixdict()
    # tmp.save()
    permutation_idx = LunpaiIndex()
    permutation_idx.load()
    query = '$中国人'
    permutation_idx.predict_queryindex(query)

