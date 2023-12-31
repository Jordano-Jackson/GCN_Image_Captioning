import h5py
import json
import math
from math import floor
from PIL import Image, ImageDraw
import random

import torch
from torch.utils.data import Dataset, DataLoader 
import numpy as np
import os
import requests
from io import BytesIO

VG_PATH = "/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/"

image_data = json.load(open(os.path.join(VG_PATH, 'image_data.json')))
vg_sgg = h5py.File('/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG-SGG-with-attri.h5')
vg_sgg_original = h5py.File('/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG-SGG.h5')
vg_sgg_dicts = json.load(open('/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG-SGG-dicts-with-attri.json'))

USE_BOX_SIZE = 1024

def draw_single_box(pic, box, color = (255,0,255,128)) :
    draw = ImageDraw.Draw(pic)
    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    draw.rectangle(((x1,y1), (x2, y2)), outline = color)

def draw_boxes(image_id, boxes) :
    pic = Image.open("/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG_100K/{}.jpg".format(image_id))
    num_obj = boxes.shape[0] 
    for i in range(num_obj) :
        draw_single_box(pic, boxes[i])
    return pic

def show_box_attributes(image_data, vg_sgg, obj_attributes, vg_sgg_dicts, img_idx = None) :
    idx_to_label = vg_sgg_dicts['idx_to_label']
    idx_to_attribute = vg_sgg_dicts['idx_to_attribute']
    if img_idx is None :
        img_idx = random.randint(0, len(image_data)-1)
    height, width = image_data[img_idx]['height'], image_data[img_idx]['width']
    filename = "/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG_100K/{}.jpg".format(str(image_data[img_idx]['image_id']))
    pic = Image.open(filename)
    ith_s = vg_sgg['img_to_first_box'][img_idx]
    ith_e = vg_sgg['img_to_last_box'][img_idx]
    obj_idx = random.randint(ith_s, ith_e)
    box = vg_sgg['boxes_1024'][obj_idx]
    label = vg_sgg['labels'][obj_idx]
    attribute = obj_attributes[obj_idx]
    box[:2] = box[:2]-box[2:]/2
    box[2:] = box[:2]+box[2:]
    box = box.astype(float) / USE_BOX_SIZE * max(height,width)
    draw_single_box(pic, box)
    att_list = []
    if attribute.sum() > 0 :
        for i in attribute.tolist():
            if i>0:
                att_list.append(idx_to_attribute[str(i)])
        print('Index: {}, Path : {}'.format(img_idx, filename))
        print('Label: {}'.format(idx_to_label[str(int(label))]))
        print('Attribute: {}'.format(','.join(att_list)))
        return pic
    else :
        return show_box_attributes(image_data, vg_sgg, obj_attributes, vg_sgg_dicts)
    
#show_box_attributes(image_info, vg_sgg, obj_attributes, vg_sgg_dicts)

# todo : retrieve scene graph from the image 
# 1. get all the list of objects per image

def get_scene_graph(vg_sgg, img_idx) :
    idx_to_label = vg_sgg_dicts['idx_to_label']
    idx_to_attribute = vg_sgg_dicts['idx_to_attribute']
    
    ith_s = vg_sgg['img_to_first_box'][img_idx]
    ith_e = vg_sgg['img_to_last_box'][img_idx]
    rth_s = vg_sgg['img_to_first_rel'][img_idx]
    rth_e = vg_sgg['img_to_last_rel'][img_idx]
    num_objs = ith_e - ith_s
    num_rels = rth_e - rth_s
    print('img id : ',image_data[img_idx]['image_id'])
    print('num obj : ', num_objs, 'num rel : ', num_rels)
    image_path = image_data[img_idx]['url']
    filename = "/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG_100K/{}.jpg".format(str(image_data[img_idx]['image_id']))
    img = Image.open(filename).convert("RGB")
    print(np.shape(img))
    img.show()
    print('active obj mask', vg_sgg['labels'])
    for obj_idx in range(ith_s, ith_e + 1) :
        print('obj_idx: ', obj_idx)
        label = vg_sgg['labels'][obj_idx]
        print(vg_sgg['boxes_1024'][obj_idx])
        print(vg_sgg['boxes_512'][obj_idx])
        print(vg_sgg['attributes'][obj_idx])
        print(label, idx_to_label[str(int(label))])
    print('relationships *********** ', num_rels)
    for rel_idx in range(rth_s, rth_e + 1) :
        print('rel num : ',rel_idx)
        rel =vg_sgg['relationships'][rel_idx]
        predicate = vg_sgg['predicates'][rel_idx]
        rel1_label = vg_sgg['labels'][rel[0]]
        rel2_label = vg_sgg['labels'][rel[1]]
        print(rel,rel1_label,rel2_label, idx_to_label[str(int(rel1_label))], idx_to_label[str(int(rel2_label))])
        print(predicate, vg_sgg_dicts['idx_to_predicate'][str(int(predicate))])

a =  [torch.FloatTensor([[79.8867, 286.8000, 329.7450, 444.0000],[11.8980, 13.2000, 596.6006, 596.4000]])] 
print(vg_sgg['relationships'].shape[0])
print(a[0].shape)
print(len(image_data))
get_scene_graph(vg_sgg,1590) #gray : 57084 
    
#num_objs = idx_to_label[str(vg_sgg['labels'][1][0])]

# 2. make dataloader for object classification 
class ObjectDetectionDataset(Dataset) :
    def __init__(self, ):
        self.image_data = json.load(open(os.path.join(VG_PATH, 'image_data.json')))
        self.vg_sgg = h5py.File('/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG-SGG-with-attri.h5')
        self.vg_sgg_dicts = json.load(open('/home/csjihwanh/Desktop/Projects/GCN_Image_Captioning/datasets/vg/VG-SGG-dicts-with-attri.json'))


    def __len__(self) :
        return len(self.vg_sgg['label'].shape[0])
    
    def __getitem__(self, idx) :
        None
        #image = self.

    #def binary_search_img_indices(self, obj_idx) :




# 3. make dataloader for semantic relation prediction 

