def pattern_match(word_pattern, line_pattern, reverse=False):
    """
    Match a word pattern (if the vowels are stressed or not) to a target pattern for a line of poetry.

    Patterns are in the form of '[012]+', e.g. '0102'.
    - '0': vowel is not stressed
    - '1': vowel has primary stress
    - '2': vowel has secondary stress. Vowels with 2 in either the word pattern or line pattern will match any
           vowel in the other pattern, e.g. '012' matches both '010', '011' and '012'.
    See http://en.wikipedia.org/wiki/Arpabet or https://www.nltk.org/book/ch02.html, chapter 4.2 A Pronouncing Dictionary,
    based on the nltk.corpus.cmudict CMU Pronouncing Dictionary for US English.
    """
    if reverse:
        word_pattern = word_pattern[::-1]
        line_pattern = line_pattern[::-1]
    for w, l in zip(list(word_pattern), list(line_pattern)):
        if (l == '2') or (w == '2') or (w == l):
            continue
        else:
            return False

    return True


if __name__ == '__main__':
    line_p = '210100'
    word_p = '010'

    print(pattern_match(word_p, line_p, reverse=False))
