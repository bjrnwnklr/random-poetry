from nltk.corpus import gutenberg

milton = gutenberg.words('milton-paradise.txt')
print(milton[900:1000])