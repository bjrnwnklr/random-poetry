from app import app
from randompoetry import Poem, PoemFormRegistry, Corpus, CorpusRegistry
import random

@app.route('/')
@app.route('/index')
def index():
    return "Hello world!"

    # randomly select a style and text source
    poemstyle = random.choice(pfr.poemforms)
    textcorpus = random.choice(cr.registry)
    
