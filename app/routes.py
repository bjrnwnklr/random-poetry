from app import app, pfr, cr
from app.forms import PoemForm
from randompoetry import Poem
import random
from flask import render_template


@app.route('/', methods=['GET', 'POST'])
def index():

    form = PoemForm()
    if form.validate_on_submit():
        # generate a poem based on the passed values. Validate that the input is a valid key in the pfr and cf objects!
        poemstyle = form.poemstyle.data
        # validate that the passed value is indeed a key in the poemformregistry
        if poemstyle not in pfr.poemforms:
            raise ValueError(f'Not a valid PoemForm: {poemstyle}')
        textcorpus = form.textcorpus.data
        if textcorpus not in cr.registry:
            raise ValueError(f'Not a valid Corpus: {textcorpus}')
    else:
        # randomly select a style and text source and update the dropdown fields with the selected values
        poemstyle = random.choice(list(pfr.poemforms.keys()))
        form.poemstyle.data = poemstyle
        textcorpus = random.choice(list(cr.registry.keys()))
        form.textcorpus.data = textcorpus

    # generate the poem and pass it to the rendered page
    poem = Poem(cr.registry[textcorpus], pfr.poemforms[poemstyle])
    return render_template('generate.html',
                           poem=poem.generate_poem(),
                           poemstyle=poemstyle,
                           textcorpus=textcorpus,
                           form=form)
