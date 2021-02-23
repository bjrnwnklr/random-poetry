from nltk.corpus import gutenberg
from nltk.corpus import cmudict
from collections import defaultdict
import string
import re
import random

# # Cleaning up the text
# 
# - Turn to lower case
# - remove punctuation
def cleanup_text(words):
    # remove punctuation
    # third parameter of str.maketrans are chars that will be mapped to None
    transtab = str.maketrans('', '', string.punctuation)
    temp_words = [w.translate(transtab) for w in words]
    temp_words = [w for w in temp_words if w != '']
    
    # turn to lower case
    temp_words = [w.lower() for w in temp_words]
    
    return temp_words


# # Creating the markov chain (forward and backward looking)
def generate_markov(words):
    markov_forward = defaultdict(list)
    for i, w in enumerate(words[:-1]):
        markov_forward[w].append(words[i + 1])
    
    markov_backward = defaultdict(list)
    for i, w in enumerate(words[1:]):
        markov_backward[w].append(words[i - 1])
        
    return markov_forward, markov_backward


# # Get the stressed vowels of a word
def stress_pattern(word):
    # look up the word in the cmudict
    if word in cmu_dict:
        # get the first pronounciation of the word
        cmu_word = cmu_dict[word][0]
        pattern = ''
        for c in cmu_word:
            if c[-1] in '012':
                pattern += c[-1]
    else:
        # word was not found
        pattern = None
        
    return pattern


# # Generate a line based on a start or end word and pattern
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

# old version, refactor so it starts with a word that is matched to the pattern (old version starts
# with a seed word that was already matched to the previous part of the pattern)
def poetry_line_old(seed, pattern, reverse=False):
    # look up list of following words
    f_words = markov_backward[seed] if reverse else markov_forward[seed]
    
    # order the markov words in random order
    for fw in random.sample(f_words, len(f_words)):
        # get the pattern of the word
        next_word_pattern = stress_pattern(fw)
        if next_word_pattern and pattern_match(next_word_pattern, pattern, reverse):
            remaining_pattern = pattern[:-len(next_word_pattern)] if reverse else pattern[len(next_word_pattern):]
            # if no more pattern to consume, return the word we found
            if remaining_pattern == '':
                return [fw, ]
            else:
                remaining_phrase = poetry_line(fw, remaining_pattern, reverse)
                if remaining_phrase:
                    return remaining_phrase + [fw, ] if reverse else [fw, ] + remaining_phrase
                
    # we didn't find a chain that matches the pattern
    return None


def poetry_line(word, pattern):
    """
    Generates a line of poetry, based on backward markov chain, i.e. starting at the end
    of the line so the words rhyme.
    :param word:
    :param pattern:
    :return:
    """
    # if the word and pattern are a match, we are done
    if stress_pattern(word) == pattern:
        return [word, ]


# # Generate words that rhyme
# 
# - Go through each word, select the last vowel and any following consonants
# - Add to a rhyme dictionary
# 
# Any words in the same rhyme class will also automatically have the same pattern!
def word_rhyme(word):
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


def generate_rhyme_dict(words):
    rhyme_dict = defaultdict(set)
    for w in words:
        rhyme_dict[word_rhyme(w)].add(w)
        
    return rhyme_dict


# # Generate multiple lines based on line patterns and lines rhyming with each other
# 
# - Pick a start word based on:
#     - the pattern to match (e.g. pick a word '010' if line pattern ends in '010'
#     - the number of rhymes required (e.g. if lines 1 and 3 need to rhyme, pick a class of words that rhyme with each other
#     
def poem_block(rhyming_lines, patterns, words):
    diff_rhymes = defaultdict(int)
    for r in rhyming_lines:
        diff_rhymes[r] += 1
        
    line_rhymes = defaultdict(list)
    for r in diff_rhymes:
        lines = [patterns[i] for i, line in enumerate(rhyming_lines) if line == r]
        l_pat = lines[0]
        # pick a word that matches the pattern end and that has the required number of rhymes
        while True:
            w = random.choice(words)
            w_pat = stress_pattern(w)
            rh = rhymes[word_rhyme(w)]
            if w_pat and pattern_match(w_pat, l_pat, reverse=True) and len(rh) >= diff_rhymes[r]:
                line_rhymes[r].append(w)
                for _ in range(1, diff_rhymes[r]):
                    while True:
                        w_rhyme = random.choice(list(rh))
                        if w_rhyme not in line_rhymes[r] and pattern_match(stress_pattern(w_rhyme), l_pat, reverse=True):
                            line_rhymes[r].append(w_rhyme)
                            break
                break
        
    rhyme_block = []
    rhyme_word_count = defaultdict(int)
    for r, p in zip(rhyming_lines, patterns):
        seed = line_rhymes[r][rhyme_word_count[r]]
        rhyme_block.append(poetry_line(seed, p[:-len(seed)], reverse=True) + [seed, ])
        rhyme_word_count[r] += 1
                           
    return rhyme_block


if __name__ == '__main__':

    sample_text = gutenberg.words('melville-moby_dick.txt')[4712:]
    cmu_dict = cmudict.dict()

    # # Test the process
    clean_text = cleanup_text(sample_text)
    markov_forward, markov_backward = generate_markov(clean_text)
    rhymes = generate_rhyme_dict(clean_text)

    seed = random.choice(clean_text)
    print(poetry_line(seed, '1010101010', reverse=True))

    # print(rhymes[word_rhyme('whale')])
    # print(poem_block([0, 1, 0, 1], ['0101010101'] * 4, clean_text))