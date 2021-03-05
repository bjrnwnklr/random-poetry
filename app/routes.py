from app import app
from randompoetry import Poem, PoemFormRegistry, Corpus, CorpusRegistry

@app.route('/')
@app.route('/index')
def index():
    return "Hello world!"

@app.route('/poem')
def poem():
    pfr = PoemFormRegistry.from_json('poemforms.json')