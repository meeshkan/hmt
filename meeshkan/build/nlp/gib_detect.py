#!/usr/bin/python

import pickle
import gibberish_detector.gib_detect_train as gib_detect_train
#from entity_extractor import split_path


#model_data = pickle.load(open('gibberish_detector/gib_model.pki', 'rb'))


class IdClassifier:

    def __init__(self):
         #path='/v3/profiles/saf45gdrg4gsdf/transfers/sdfsr456ygh56ujhgf/payments'
         self.model_data = pickle.load(open('gibberish_detector/gib_model.pki', 'rb'))

    def id_classifier(self, path_list):
         id=[]
         for item in path_list:
             l =item
             model_mat = self.model_data['mat']
             threshold = self.model_data['thresh']
             if not (gib_detect_train.avg_transition_prob(l, model_mat) > threshold):
                  id.append(item)
                  if len(id)!=0:
                       return id[-1]
             else:
                  return None
