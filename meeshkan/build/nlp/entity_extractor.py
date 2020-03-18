import os
import re

#import nltk
import spacy
#from sklearn.feature_extraction.text import CountVectorizer
nlp=spacy.load('en_core_web_lg')

def split_path(path):
    path_list=path.split('/')[1:]
    return(path_list)
'''    splits =[]
    while path != '/':
        print(path)
        path, split = os.path.split(path)
        splits.append(split)
    return  list(reversed(splits))
'''

def tokenize(path):
    res = list()
    for item in path:
        item = re.sub('[^0-9a-z]+', ' ', item.lower())
        item = re.sub('[0-9]+', '', item)
        for word in item.split(' '):
            if len(word) > 3:
               if word in nlp.vocab:
                	res.append(word)
    return res


class EntityExtractorNLP:
    STOP_WORDS = [r'v?\d+', r'api.*', r'json', r'yaml']
    STOP_TAGS = {'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'}

    def __init__(self):
         self.nlp=spacy.load('en_core_web_lg')
    # def train(self, pathes):
    #     path_lists = self._split_pathes(pathes)
    #     for path_list, path in zip(path_lists, pathes):
    #         self._mapping[path] = path_list[-1]

    def _split_pathes(self, pathes):
        path_lists=[]
        for path in pathes:
            path_list=[item for item in tokenize(split_path(path)) if not self._is_stop_word(item)]
            path_list =[word for word in path_list if nlp(word)[0].tag_ not in self.STOP_TAGS]
            path_lists.append(path_list)
        return path_list

    def get_entity_from_url(self, path):
        return self.nlp(self._split_pathes([path])[-1])[0].lemma_
        # return self._mapping.get(path)

    def _is_stop_word(self, path_item):
        for stop_word in self.STOP_WORDS:
            if re.match(stop_word, path_item):
                return True
        return False


EntityExtractor = EntityExtractorNLP
