import os
import re

import spacy

def split_path(path):
    path_list=path.split('/')[1:]
    return(path_list)


class EntityExtractorNLP:
    STOP_WORDS = [r'v?\d+', r'api.*', r'json', r'yaml']
    STOP_TAGS = {'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'}

    def __init__(self):
         self.nlp=spacy.load('en_core_web_lg')


    def tokenize(self, path_list):
        res = list()
        for item in path_list:
            item = re.sub('[^0-9a-z]+', ' ', item.lower())
            item = re.sub('[0-9]+', '', item)
            for word in item.split(' '):
                if len(word) > 3:
                    if word in self.nlp.vocab:
                        res.append(word)
        return res


    def _split_pathes(self, p_list):
        path_lists=[]
        for path in p_list:
            path_list=[item for item in self.tokenize(p_list) if not self._is_stop_word(item)]
            path_list =[word for word in path_list if self.nlp(word)[0].tag_ not in self.STOP_TAGS]
            path_lists.append(path_list)
        return path_list

    def get_entity_from_url(self, p_list):
        return self.nlp(self._split_pathes(p_list)[-1])[0].lemma_
        # return self._mapping.get(path)

    def _is_stop_word(self, path_item):
        for stop_word in self.STOP_WORDS:
            if re.match(stop_word, path_item):
                return True
        return False


EntityExtractor = EntityExtractorNLP
