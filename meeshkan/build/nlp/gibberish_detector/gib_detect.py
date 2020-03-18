#!/usr/bin/python

import pickle
import gib_detect_train
from entity_extractor import split_path
model_data = pickle.load(open('gib_model.pki', 'rb'))


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
    return id[-1]
print(id_classifier(path))
