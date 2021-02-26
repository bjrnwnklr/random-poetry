from nltk.corpus import cmudict
from collections import defaultdict
import string
import logging
import random

cmu_dict = cmudict.dict()


class Word:
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
        # get the pattern of the word
        word_pattern = self.pattern
        if word_pattern and len(word_pattern) <= len(line_pattern):
            if reverse:
                word_pattern = self.pattern[::-1]
                line_pattern = line_pattern[::-1]
            for w, l in zip(list(word_pattern), list(line_pattern)):
                if (l == '2') or (w == '2') or (w == l):
                    continue
                else:
                    logging.debug(f'pattern_match: no match: {self.w} ({word_pattern}), {line_pattern}')
                    return False

            logging.debug(f'pattern_match: match: {self.w} ({word_pattern}), {line_pattern}')
            return True
        else:
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


def cleanup_text(words):
    """
    Cleans up a raw list of words by:
    - turning to lower case
    - removing punctuation
    :param words: A list of words
    :return: A list of lowercase words without punctuation.
    """
    # remove punctuation
    # third parameter of str.maketrans are chars that will be mapped to None

    logging.debug(f'Corpus: Cleaning up text with {len(words)} words.')

    transtab = str.maketrans('', '', string.punctuation)
    temp_words = [w.translate(transtab) for w in words]
    temp_words = [w for w in temp_words if w != '']

    # turn to lower case
    temp_words = [w.lower() for w in temp_words]

    return temp_words


class Corpus:
    def __init__(self, words):
        # sample_text = gutenberg.words('melville-moby_dick.txt')[4712:]
        # with open('sonnets.txt', 'r') as f:
        #     raw_text = f.read()
        #     sample_text = [w.strip() for w in raw_text.split()]

        self.clean_text = cleanup_text(words)
        self.words = self.generate_word_registry()
        self.markov_forward, self.markov_backward = self.generate_markov()
        self.rhymes = self.generate_rhyme_dict()

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

    # # Creating the markov chain (forward and backward looking)
    def generate_markov(self):
        markov_forward = defaultdict(list)
        for i, w in enumerate(self.clean_text[:-1]):
            if w in self.words:
                markov_forward[self.words[w]].append(Word(self.clean_text[i + 1]))

        markov_backward = defaultdict(list)
        for i, w in enumerate(self.clean_text[1:], start=1):
            markov_backward[Word(w)].append(Word(self.clean_text[i - 1]))

        return markov_forward, markov_backward

    def generate_rhyme_dict(self):
        rhyme_dict = defaultdict(set)
        for w in words:
            rhyme_dict[self.word_rhyme(w)].add(w)

        return rhyme_dict

    # # Generate words that rhyme
    #
    # - Go through each word, select the last vowel and any following consonants
    # - Add to a rhyme dictionary
    #
    # Any words in the same rhyme class will also automatically have the same pattern!
    def word_rhyme(self):
        # look up the word in the cmudict
        if word in cmu_dict:
            # get the first pronounciation of the word
            cmu_word = cmu_dict[word][0]
            # find the last vowel
            rhyme = []
            for phone in cmu_word[::-1]:
                if phone[-1] in '012':
                    rhyme.append(phone)
                    break
                else:
                    rhyme.append(phone)
            return tuple(rhyme[::-1])
        else:
            return None


class Poem:
    def __init__(self, corpus):
        self.corpus = corpus

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
