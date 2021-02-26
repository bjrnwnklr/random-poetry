from nltk.corpus import gutenberg
import logging
from poetrygenerator import Corpus


if __name__ == '__main__':

    logging.basicConfig(filename='poetry.log', level=logging.DEBUG, filemode='w', format='%(asctime)s %(message)s')

    sample_text = gutenberg.words('melville-moby_dick.txt')[4712:]
    corpus_moby = Corpus(sample_text)
    corpus_sonnets = Corpus.from_file('sonnets.txt')


    # for seed in ['brow', 'eye']:
    #     logging.debug(f'--- Generating poetry line with seed {seed} ---')
    #     print(poetry_line(seed, '0101010121'))

    # print(rhymes[word_rhyme('whale')])
    # print(poem_block([0, 1, 0, 1], ['0101010101'] * 4, clean_text))
