import sqlite3
from datetime import datetime


def save_data_title_to_db(data_file, table, db_path='D:\\PyCharm Project\\SearchEngine\\db\\news_test.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open(data_file, 'r', encoding='utf8') as f:
        line = f.readline()
        # count = 1
        while line != '':
            if not line.startswith(table.split('_')[0]):
                line = f.readline()
                continue
            data = line.strip().split('\t')
            # print(count, len(data))
            doc_id = data[0]
            url = data[1]
            date = datetime.strptime(data[2], '%Y-%m-%d %H:%M:%S')
            title = ''.join(data[3:])
            c.execute('INSERT INTO ' + table + ' VALUES (?, ?, ?, ?, ?)', (doc_id, url, date, title, ''))
            line = f.readline()
            # count += 1
    conn.commit()
    conn.close()


def save_data_content_to_db(data_file, table, db_path='D:\\PyCharm Project\\SearchEngine\\db\\news_test.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    with open(data_file, 'r', encoding='utf8') as f:
        line = f.readline()
        while line != '':
            if not line.startswith(table.split('_')[0]):
                line = f.readline()
                continue
            data = line.strip().split('\t')
            doc_id = data[0]
            content = ''.join(data[3:])
            content = content.replace('"', '').replace("'", "")
            c.execute("UPDATE " + table + ' set Doc_content = "' + content + '" where Doc_ID = "' + doc_id + '"')
            line = f.readline()
    conn.commit()
    conn.close()


if __name__ == '__main__':
    tables = [
        'ifeng_news',
        'sina_news',
        'sohu_news',
        'thepaper_news'
    ]
    title_paths = [
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\ifeng_news_title',
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\sina_news_title',
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\sohu_news_title',
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\thepaper_news_title'
    ]
    content_paths = [
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\ifeng_news_content',
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\sina_news_content',
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\sohu_news_content',
        'D:\\PyCharm Project\\SearchEngine\\test_resources\\jiebaRes\\thepaper_news_content'
    ]
    for i in range(len(tables)):
        save_data_title_to_db(title_paths[i], tables[i])
        save_data_content_to_db(content_paths[i], tables[i])
