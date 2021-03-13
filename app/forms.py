from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from app import pfr, cr


class PoemForm(FlaskForm):
    poemstyle = SelectField('Poem style', choices=list(pfr.poemforms.keys()))
    textcorpus = SelectField('Text corpus', choices=list(cr.registry.keys()))
    submit = SubmitField('Go!')
    randompoem = SubmitField("I'm feeling lucky!")
