#http://www.mhermans.net/from-pdf-to-wordcloud-using-the-python-nltk.html
#! /usr/bin/env python
# wordcount.py: parse & return word frequency
import sys, nltk

f = open(sys.argv[1], 'rU')
txt = f.read()
f.close()

tokens = nltk.word_tokenize(txt) # tokenize text
clean_tokens = []

for word in tokens:
    word = word.lower()
    if word.isalpha(): # drop all non-words
        clean_tokens.append(word)

# make frequency distribution of words
fd = nltk.FreqDist(clean_tokens)
for token in fd:
    print token, ':', fd[token]