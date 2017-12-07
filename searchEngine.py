#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 18:04:43 2017

@author: manalisatghar
"""
from collections import defaultdict
from functools import reduce
import math
from nltk.corpus import stopwords
from prettytable import PrettyTable
import os
import sys
import codecs
from bs4 import BeautifulSoup
import re
import requests
import time

# dictionary containing ids and files 
corpus_files = {}
# a set to contain dictionary of all words in the document corpus
dictionary = set()
# a defaultdict whose keys are words, and corresponding values are the list of documents the word appears in
postings = defaultdict(dict)
# a defaultdict whose keys are words, and corresponding values are the number of documents which contain it
document_frequency = defaultdict(int)
# a defaultdict whose keys are document ids, and corresponding values are Euclidean length of the corresponding document vector
length = defaultdict(float)
# The list of characters to strip out of terms in the document.
characters = " .,!#$%^&*();:\n\t\\\"?!{}[]<>"

# getTweets:
# input: url
# output: file containing tweets
def getTweets(pageLink):
    for i in range(5): # try 5 times
        try:
            #use the browser to access the url
            response=requests.get(pageLink,headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36', })
            html=response.content # get the html
            break # we got the file, break the loop
        except Exception as e:# threw an exception, the attempt to get the response failed
            print ('failed attempt',i)
            time.sleep(2) # wait 2 secs
				
		
    if not html:return # couldnt get the page, ignore
    
    soup = BeautifulSoup(html.decode('ascii', 'ignore'),'lxml') # parse the html 

    tweets=soup.findAll('li', {'class':re.compile('[data-item-type=tweet]')}) # get all the question divs
    #write the tweets to a file
    fw=open("./input/"+ pageLink.split(".com/")[1]+'.txt','w', encoding='utf-8')
    for tweet in tweets:
        txt=None
        try: 
            txt=tweet.find('p', {'class':re.compile('[class$=tweet-text]')}).text
        except: None    
        if txt != None and "Retweeted" not in txt:    
            fw.write(txt.replace('\n',' ')+'\n')
    
    fw.close()

# getTweets:
# input: twitter account list file
# output: downloads files and populates corpus_files
def downloadFiles(filePath):
    # Reading File Content.
    f = open(filePath, "r")
    
    output=f.readline()
    while output:
        print("Getting @"+output.strip()+"'s tweets...")
        getTweets("https://twitter.com/"+output.strip())
        output=f.readline()
    
    print("Finished getting tweets.")

    courpusCounter = 0
    filesList = [f for f in os.listdir('./input') if f.endswith('.txt')]
    for file in filesList:
        corpus_files[courpusCounter]= './input/'+file
        courpusCounter+=1
    
# processDocuments:
# desc: For each document in corpus_files, split into a list of terms, 
#    add terms to the dictionary, add the document to the posting list for each
#    term, with value as the frequency of the term in the
#    document. After that, initializes all document frequencies.
def processDocuments():
    global dictionary, postings, document_frequency
    stop_words= set(stopwords.words('english'))

    for id in corpus_files:
        f = codecs.open(corpus_files[id], encoding='utf-8')
        document = f.read()
        f.close()
        
        terms = document.lower().split()
        terms = [term.strip(characters) for term in terms]
        stopped_tokens = [i for i in terms if not i in stop_words]
       
        unique_terms = set(stopped_tokens)
        dictionary = dictionary.union(unique_terms)
        for term in unique_terms:
            postings[term][id] = terms.count(term) # the value is the frequency of the term in the document

        # initializing document frequencies
        for term in dictionary:
            document_frequency[term] = len(postings[term])	
	                                                                                     
# findDocLength:
# desc: Computes the length for each document as the sum of squares of importance of each term in the document.
def findDocLength():
    global length
    for id in corpus_files:
        l = 0
        for term in dictionary:
            importance = 0.0
            if id in postings[term]:
                importance = postings[term][id]*findInverseFrequency(term)
            l += importance**2
        length[id] = math.sqrt(l)

# findInverseFrequency:
# input: a word
# output: inverse document frequency of the word, or  0 if not in the dictionary
def findInverseFrequency(term):
    if term in dictionary:
        if document_frequency[term] != 0 :
            return math.log(len(corpus_files)/document_frequency[term],2)
        else:
            return 0.0
    else:
        return 0.0

# intersection:
# input: list of sets
# output: the intersection of all sets in the list sets
def intersection(sets):
    return reduce(set.union, [s for s in sets])

# similarity:
# input: query, document id
# output: cosine similarity of query and document id
def similarity(query,id):
    similarity = 0.0
    for term in query:
        if term in dictionary:
            importance = 0.0
            if id in postings[term]:
                importance = postings[term][id]*findInverseFrequency(term)
            similarity += findInverseFrequency(term)*importance
    if length[id] != 0:
    	similarity = similarity / length[id]
    return similarity

# search:
# desc: takes user input and performs search
def search():
    t = PrettyTable(['Match Score', 'Account'])
    query = input("Enter Query:  ")
    if query == "exit":
        sys.exit()
    query = query.lower().split()
    query = [q.strip(characters) for q in query]
    u_query= set(query)

    result_doc_id = set()
    result_doc_id = intersection([set(postings[term].keys()) for term in u_query])
    if not result_doc_id:
        print ("No documents matched the given query")
    else:
        print (str(len(result_doc_id))+" documents matched the given query")
        scores = sorted([(id,similarity(u_query,id))for id in result_doc_id], key=lambda x: x[1],reverse=True)
        for (id,score) in scores:
            t.add_row([str(score), "@"+corpus_files[id].strip('.txt').split('/input/')[1]])
        print(t)
        
if __name__ == "__main__":
    downloadFiles('twitterLinks.txt')
    processDocuments()
    findDocLength()
    while True:
        search()

