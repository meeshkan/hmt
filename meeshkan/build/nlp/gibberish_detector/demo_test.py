import pickle
import gib_detect_train
model_data = pickle.load(open('gib_model.pki', 'rb'))



while True:
        l = input()
        model_mat = model_data['mat']
        threshold = model_data['thresh']
        if (gib_detect_train.avg_transition_prob(l, model_mat) > threshold):
                print('not_id')
        else:
                print('id')
