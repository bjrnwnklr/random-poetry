from nltk.corpus import gutenberg
import logging
from randompoetry import Poem, PoemFormRegistry, Corpus, CorpusRegistry

if __name__ == '__main__':

    logging.basicConfig(filename='poetry.log', level=logging.ERROR, filemode='w', format='%(asctime)s %(message)s')

    pfr = PoemFormRegistry.from_json('poemforms.json')
    print(pfr)

    cr = CorpusRegistry()

    # for each corpus (text style / text input, e.g. Shakespeare), create a poem in each of the forms
    for corpus_name in cr.registry:
        print(f'--- In the style of {corpus_name}: ---')
        for pf_name in pfr.poemforms:
            print(f'\nA {pf_name} poem!')
            print('-' * 20, '\n')
            poem = Poem(cr.registry[corpus_name], pfr.poemforms[pf_name])
            print(poem.generate_poem())
