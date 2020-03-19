#!/usr/bin/python

import pickle
import gibberish_detector.gib_detect_train as gib_detect_train
from entity_extractor import split_path
model_data = pickle.load(open('gibberish_detector/gib_model.pki', 'rb'))


#input=path=>>>
path='/v3/profiles/saf45gdrg4gsdf/transfers/sdfsr456ygh56ujhgf/payments'
#path_list=split_path(path)

def id_classifier(path):
    id=[]
    path_list=split_path(path)
    for item in path_list:
        l =item
        model_mat = model_data['mat']
        threshold = model_data['thresh']
        if not (gib_detect_train.avg_transition_prob(l, model_mat) > threshold):
               id.append(item)
    if len(id)!=0:
         return id[-1]
    else:
         return None
#print(id_classifier(path))
