# Assume each input spectrogram has 1024 time frames
from non_human_recognition.feature_extraction import ASTModelVis, make_features
import torch
from torch.cuda.amp import autocast
import joblib
import os

input_tdim = 1024
filename = r'.\non_human_recognition\classifier\svc_best.pkl'
if os.path.exists(filename):
    print("File exists")
else:
    print("File does not exist")
clf = joblib.load(filename)

# now load the visualization model
ast_mdl = ASTModelVis(label_dim=527, input_tdim=input_tdim, imagenet_pretrain=True, audioset_pretrain=False)
audio_model = torch.nn.DataParallel(ast_mdl, device_ids=[0])
if torch.cuda.is_available():
    print("Loading feature extract model using cuda")
    audio_model = audio_model.to(torch.device("cuda:0"))
else:
    print("Loading feature extract model using cpu")
    audio_model = audio_model.to(torch.device("cpu"))
audio_model.eval()

  
def extract_features(sound_sample_path,min_id,max_id):
    with torch.no_grad():
        feats = make_features(sound_sample_path,min_id,max_id, mel_bins=128)  # shape(1024, 128)
        # only feature extraction
        feats_data = feats.expand(1, input_tdim, 128)
        if torch.cuda.is_available():
            print("Loading feature extract model using cuda")
            feats_data = feats_data.to(torch.device("cuda:0"))
        else:
            print("Loading feature extract model using cpu")
            feats_data = feats_data.to(torch.device("cpu"))           # reshape the feature
        with autocast():
            output = audio_model.forward(feats_data, classifier = False)
            att_list = audio_model.module.forward_visualization(feats_data)
    return output, att_list, feats

def predict(sound_sample_path,min_id,max_id):
    feat, att_list, mel = extract_features(sound_sample_path,min_id,max_id)    # shape(1024, 128)
    feat = feat.cpu()
    feat = feat.reshape(1,768)
    pred = clf.predict(feat)
    return pred, att_list, mel

