from nltk.corpus import cmudict
from collections import defaultdict
import string
import logging
import random
import json
from pathlib import Path

cmu_dict = cmudict.dict()


class Word:
    """
    Represents a word. Key attributes:
    - Word.w = text representation of the word
    - Word.pattern = the stress pattern of the word e.g. '1010'
    """

    def __init__(self, w):
        self.w = w
        self.pattern = self.stress_pattern()

    def __str__(self):
        return self.w

    def __repr__(self):
        return f'{self.w} ({self.pattern})'

    def stress_pattern(self):
        """
        Generate the stress pattern of a word by using the stress of the vowels as
        per the CMU dictionary.
        '0': vowel not stressed
        '1': vowel is stressed
        '2': vowel is optionally stressed
        :return: Stress pattern of the word e.g. '0102'
        """
        # look up the word in the cmudict
        if self.w in cmu_dict:
            # get the first pronunciation of the word
            cmu_word = cmu_dict[self.w][0]
            pattern = ''
            # Add the stress from each vowel to create the stress pattern of the word
            for c in cmu_word:
                if c[-1] in '012':
                    pattern += c[-1]
        else:
            # word was not found
            logging.debug(f'stress_pattern: not in CMU: {self.w}')
            pattern = None

        return pattern

    def pattern_match(self, line_pattern, reverse=False):
        """
        Match a word's pattern (if the vowels are stressed or not) to a target pattern for a line of poetry.

        Patterns are in the form of '[012]+', e.g. '0102'.
        - '0': vowel is not stressed
        - '1': vowel has primary stress
        - '2': vowel has secondary stress. Vowels with 2 in either the word pattern or line pattern will match any
               vowel in the other pattern, e.g. '012' matches both '010', '011' and '012'.
        See http://en.wikipedia.org/wiki/Arpabet or https://www.nltk.org/book/ch02.html,
        chapter 4.2 A Pronouncing Dictionary, based on the nltk.corpus.cmudict
        CMU Pronouncing Dictionary for US English.
        """
        word_pattern = self.pattern
        # the word needs to have a valid stress pattern (i.e. it was in the dictionary),
        # and its pattern has to be shorter than the line pattern so it fits in
        if word_pattern and len(word_pattern) <= len(line_pattern):
            # for poems, we typically start at the end of the line with a rhyme, so need to match
            # the word to the end of the pattern. This can be done easiest by reversing both the
            # word and line patterns and then comparing them.
            if reverse:
                word_pattern = self.pattern[::-1]
                line_pattern = line_pattern[::-1]
            # Word and line pattern match if they either have the exact same stress (0 or 1),
            # while a 2 in word or line matches any of 0, 1 or 2.
            for w, l in zip(list(word_pattern), list(line_pattern)):
                if (l == '2') or (w == '2') or (w == l):
                    continue
                else:
                    # one of the positions didn't match, so we can stop
                    logging.debug(f'pattern_match: no match: {self.w} ({word_pattern}), {line_pattern}')
                    return False

            logging.debug(f'pattern_match: match: {self.w} ({word_pattern}), {line_pattern}')
            return True
        else:
            # If we get to here, the word either didn't have a valid pattern or the line pattern is too short
            return False

    def remaining_pattern(self, line_pattern):
        """
        Return the remaining pattern after removing the word's pattern from the passed in line pattern.

        E.g 'brow' has a stress pattern of '1'. For the line pattern '0101', the remaining pattern after
        taking off the '1' is '010'.

        :param line_pattern: A line poetry pattern, specifying the number of vowels and stresses
        :return: Remaining line pattern after taking off the word's pattern
        """
        if self.pattern:
            return line_pattern[:-len(self.pattern)]
        else:
            return None

    def word_rhyme(self):
        """
        Extract the last stressed vowel and any following syllables from a word and return as a tuple.
        This can be used to find words that rhyme with this word.
        :return: A tuple of rhyming phonems e.g. ('EH0', 'ER')
        """
        # look up if the word is in the cmu dictionary - if not, we can't find a rhyme
        if self.w in cmu_dict:
            # get the first pronounciation of the word
            cmu_word = cmu_dict[self.w][0]
            # go backwards through each phonem in the word from the end and find the last stressed vowel
            # stop after we find the first vowel and return the vowel plus all following consonants as a tuple
            # Note:
            # - use '012' to use the last vowel, regardless if stressed or not.
            # - use '12' to use the last _stressed_ vowel.
            rhyme = []
            for phone in cmu_word[::-1]:
                if phone[-1] in '12':
                    rhyme.append(phone)
                    break
                else:
                    rhyme.append(phone)
            return tuple(rhyme[::-1])
        else:
            # the word was not in the CMU dictionary, so no rhyme
            return None


class CorpusRegistry:
    def __init__(self):
        logging.debug(f'CorpusRegistry: initializing registry.')
        p = Path('data') / 'textinput'

        self.registry = dict()
        for f in list(p.glob('*.txt')):
            self.registry[f.stem] = Corpus.from_path(f)


class Corpus:
    """
    Represents a text corpus with all words from the corpus, a forward and backward markov chain and
    a dictionary of words that rhyme. Cleans up the text and looks up all words in the CMU dictionary.
    Any words not in the CMU dictionary will not be used for the markov chains and rhyme dictionary.
    """

    def __init__(self, words, name='Some text'):
        logging.debug(f'Corpus: initializing corpus: {name}.')

        self.name = name
        self.raw_words = words
        self.clean_text = self.cleanup_text()
        self.words = self.generate_word_registry()
        self.markov_forward, self.markov_backward = self.generate_markov()
        self.rhymes = self.generate_rhyme_dict()

    @classmethod
    def from_file(cls, filename):
        """
        Generates a Corpus object from the words in a text file.
        :param filename: name of a text file, has to be in the 'data/textinput' directory.
        :return: Corpus object initialized with the words from the text file.
        """
        logging.debug(f'Corpus: loading file {filename}.')

        p = Path('data') / 'textinput' / filename

        if not p.exists():
            raise FileNotFoundError(f'not found: {p}')

        with open(p, 'r', encoding='utf-8') as f:
            raw_text = f.read()
            return cls([w.strip() for w in raw_text.split()], p.stem)

    @classmethod
    def from_path(cls, path):
        """
        Generates a Corpus object from the words in a text file.
        :param path: Pathlib Path to the input file.
        :return: Corpus object initialized with the words from the text file.
        """
        logging.debug(f'Corpus: loading file {path}.')

        if not path.exists():
            raise FileNotFoundError(f'not found: {path}')

        with open(path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
            return cls([w.strip() for w in raw_text.split()], path.stem)

    def cleanup_text(self):
        """
        Cleans up a raw list of words by:
        - turning to lower case
        - removing punctuation
        :return: A list of lowercase words without punctuation.
        """
        logging.debug(f'Corpus: Cleaning up text with {len(self.raw_words)} words.')

        # remove punctuation
        # third parameter of str.maketrans are chars that will be mapped to None
        transtab = str.maketrans('', '', string.punctuation)
        temp_words = [w.translate(transtab) for w in self.raw_words]
        temp_words = [w for w in temp_words if w != '']

        # turn to lower case
        temp_words = [w.lower() for w in temp_words]

        return temp_words

    def generate_word_registry(self):
        """
        Generate a dictionary of words: Word objects for words found in the CMU Dictionary.
        :return: Dictionary with word: Word(word) items.
        """
        logging.debug(f'Corpus: Generating word registry.')
        wreg = {
            w: Word(w) for w in self.clean_text
            if w in cmu_dict
        }
        logging.debug(f'Corpus: Added {len(wreg)} words to the registry.')
        return wreg

    def generate_markov(self):
        """
        Generate a forward and backward Markov chain dictionary. Entries in the chain
        are words that can be found in the cmu dictionary. Any other words are not added.
        :return: Two dictionaries: markov_forward, markov_backward. Each dictionary contains Word objects as
        key and value.
        """
        logging.debug(f'Corpus: Generating markov chains.')

        # Generate a markov chain. Only words that were found in the CMU dictionary are used for both the
        # current and the preceeding / following word.
        markov_forward = defaultdict(list)
        for i, w in enumerate(self.clean_text[:-1]):
            if w in self.words and self.clean_text[i + 1] in self.words:
                markov_forward[self.words[w]].append(self.words[self.clean_text[i + 1]])

        markov_backward = defaultdict(list)
        for i, w in enumerate(self.clean_text[1:], start=1):
            if w in self.words and self.clean_text[i - 1] in self.words:
                markov_backward[self.words[w]].append(self.words[self.clean_text[i - 1]])

        logging.debug(f'Corpus: Generated markov chains. Forward: {len(markov_forward)} words; ' +
                      f'backward: {len(markov_backward)} words.')

        return markov_forward, markov_backward

    def generate_rhyme_dict(self):
        """
        Generate a dictionary of rhymes associated with each word in the word registry. The rhymes
        are generated based on the last syllable (i.e. last vowel plus any following consonants) of the
        word.
        :return: Dictionary with keys: tuple of last vowel / consonants as in the CMU dictionary, values: Word objects.
        """
        logging.debug(f'Corpus: Generating Rhyme dictionary.')
        rhyme_dict = defaultdict(set)
        for w in self.words.values():
            rhyme_dict[w.word_rhyme()].add(w)

        logging.debug(f'Corpus: Generated Rhyme dict: {len(rhyme_dict)} rhymes.')
        return rhyme_dict


class Poem:
    """
    Represents a poem with a metric pattern and provides methods to generate a poem based on a metric pattern
    and a provided corpus of words.
    """

    def __init__(self, corpus, form):
        self.corpus = corpus
        self.form = form

    def generate_poem(self):
        """
        Generate a poem based on the lines and patterns in the PoemForm (self.form).
        :return: A string representation of the poem.
        """
        logging.debug(f'Poem: generating poem from {self.corpus.name} and {self.form.name}.')
        # count how many lines are required for each element in lines
        line_count = {
            c: self.form.lines.count(c)
            for c in list(self.form.lines) if c != ' '
        }

        # call self.generate_poem_block with the pattern and number of lines required
        # repeat until the returned value is not none, otherwise try again
        # store in a dictionary of lists (A: [line1, line2,...])
        poem_blocks = dict()
        for line in line_count:
            poem_block = None
            while poem_block is None:
                poem_block = self.generate_poem_block(self.form.pattern[line], line_count[line])
            poem_blocks[line] = poem_block

        # assemble the output string from lines, including blank lines
        poem_string = ''
        for line in list(self.form.lines):
            if line == ' ':
                poem_string += '\n'
            else:
                poem_string += poem_blocks[line].pop(0)
                poem_string += '\n'

        return poem_string.strip()

    def generate_poem_block(self, line_pattern, k=2):
        """
        Generates k lines of poem, based on the provided line pattern.
        :param line_pattern: Pattern of feet e.g. one unstressed syllable followed by a stressed syllable. '0101010101'
        :param k: Number of lines to be generated. Lines will rhyme.
        :return: A list of rhyming lines as strings.
        """
        logging.debug(f'Poem: generating poem block: {line_pattern}, {k=}')

        # randomly pick rhymes until we find one that has at least k seed words that match the pattern.
        seed_words = []
        while len(seed_words) < k:
            # pick a random rhyme that has at least k entries
            rhyme = random.choice([r for r in self.corpus.rhymes if len(self.corpus.rhymes[r]) >= k])
            logging.debug(f'Poem: picked seed rhyme {rhyme}')

            # get all words from the rhyme that match the line pattern
            seed_words = [w for w in self.corpus.rhymes[rhyme] if w.pattern_match(line_pattern, reverse=True)]
            logging.debug(f'Poem: found {len(seed_words)} seed words.')

        lines = []
        for seed in random.sample(seed_words, k=len(seed_words)):
            # pick a random seed word that matches the line pattern. Avoid using the same word for each line.
            logging.debug(f'Poem: trying to generate a line from seed word: {seed}')
            if pl := self.poetry_line(seed, line_pattern):
                line = ' '.join(pl)
                logging.debug(f'Poem: found a line: {line}')
                lines.append(line.title())
            if len(lines) == k:
                return lines

        return None

    def poetry_line(self, word, line_pattern):
        """
        Generates a line of poetry, based on backward markov chain, i.e. starting at the end
        of the line so the words rhyme.
        :param word:
        :param line_pattern:
        :return:
        """
        logging.debug(f'poetry_line({word}, {line_pattern})')

        # if the word and pattern are a match, we are done
        if word.pattern == line_pattern:
            logging.debug(f'poetry_line({word}): found final match.')
            return [word.w, ]
        # if the word doesn't match with the end of the pattern, we don't even need to proceed. Try a new word.
        if not word.pattern_match(line_pattern, reverse=True):
            logging.debug(f'poetry_line({word}): no match, returning None')
            return None

        # if we get to this point, we have a word that matches the end of the pattern, and there is more pattern
        # left. So we need to find a word that matches the remaining pattern etc until we find words that match
        # all of the remaining pattern. If we find a word that doesn't match their part of the pattern, we need
        # to backtrack.

        # get all next possible words from the markov chain
        rest_pattern = word.remaining_pattern(line_pattern)
        options = set([w for w in self.corpus.markov_backward[word] if w.pattern_match(rest_pattern, reverse=True)])
        logging.debug(f'poetry_line({word}): trying to match {len(options)} options to {rest_pattern}.')
        if not options:
            # we didn't find any viable options
            return None

        # go through random order of all available next words until we find a line that matches the rest of the pattern
        for next_word in random.sample(list(options), len(options)):
            rest_of_line = self.poetry_line(next_word, rest_pattern)
            if rest_of_line:
                logging.debug(f'poetry_line({word}): found a match {rest_of_line} + {word}')
                return rest_of_line + [word.w, ]

        # if we get to here, we found no valid options and need to abort (which results in either backtracking or the
        # line needs to be started from a different word
        logging.debug(f'poetry_line({word}): found no valid options, returning None')
        return None


class PoemForm:
    """
    Class defining the attributes of a poem.
    - name: name of the poem type, e.g. "Sonnet"
    - lines: structure of the poem: how many lines and which ones rhyme with each other. Spaces declare a blank line
    - pattern: dictionary of line: meter pairs, e.g. for a line with iambic pentameter: 'A': '0101010101'
    """
    def __init__(self, name, lines, pattern):
        # TODO: check if lines and pattern match i.e. if for every letter in self.line,
        #  there is a matching pattern entry. Raise an exception if not matching.
        self.name = name
        self.lines = lines
        self.pattern = pattern

    def __repr__(self):
        repr_str = f'{self.name}\n\t{self.lines}\n'
        for k, v in self.pattern.items():
            repr_str += f'\t\t{k}: {v}\n'

        return repr_str


class PoemFormRegistry:
    def __init__(self):
        self.poemforms = dict()

    @classmethod
    def from_json(cls, filename):
        logging.debug(f'PoemFormRegistry: loading file {filename}.')

        p = Path('data') / 'config' / filename

        if not p.exists():
            raise FileNotFoundError(f'not found: {p}')

        with open(p, 'r') as f:
            poem_dict = json.load(f)

        pfr = PoemFormRegistry()
        for pf in poem_dict['poemforms']:
            pfr.poemforms[pf['name']] = PoemForm(pf['name'], pf['lines'], pf['pattern'])

        return pfr

    def __repr__(self):
        repr_str = f'PoemFormRegistry with {len(self.poemforms)} entries:\n'
        for pf in self.poemforms.values():
            repr_str += str(pf)
        return repr_str