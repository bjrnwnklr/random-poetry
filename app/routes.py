from app import app, pfr, cr
from app.forms import PoemForm
from randompoetry import Poem
import random
from flask import render_template


@app.route('/')
@app.route('/index')
def index():

    form = PoemForm()

    # randomly select a style and text source
    poemstyle = random.choice(list(pfr.poemforms.keys()))
    textcorpus = random.choice(list(cr.registry.keys()))

    # generate a random poem
    poem = Poem(cr.registry[textcorpus], pfr.poemforms[poemstyle])

    return render_template('generate.html', poem=poem.generate_poem(), poemstyle=poemstyle, textcorpus=textcorpus, form=form)



