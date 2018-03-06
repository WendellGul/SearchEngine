import json
import sys
import os

from flask import Flask
from flask import render_template
from flask import request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from search_engine import SearchEngine

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search/')
def search():
    more = request.args.get('m')
    more = 0 if more is None else int(more)
    search_text = request.args.get('q')
    page = int(request.args.get('p')) if request.args.get('p') is not None else 0
    result = se.search(search_text, page, more)
    return render_template('result.html', result=result, more=more)


@app.route('/suggest/')
def suggest():
    search_text = request.args.get('s')
    result = []
    if len(search_text) > 0:
        result.extend(se.suggest(search_text))
    return json.dumps(result)


if __name__ == '__main__':
    db_type = 'local'
    if len(sys.argv) > 1:
        db_type = sys.argv[1]
    se = SearchEngine(db_type=db_type)
    app.run()
