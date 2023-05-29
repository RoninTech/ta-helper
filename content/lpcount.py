#!/usr/bin/python

from turtle import width
from bs4 import BeautifulSoup
import os, glob
import cv2
import urllib.request
import numpy as np

# Process all .md files in folder and sub-folders for image blocks
for filename in glob.glob('**/*.md', recursive=True):
    print("\nProcessing " + filename)
    with open(os.path.join(os.getcwd(), filename), 'r') as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'lxml')
        match = "text-align: center"
        divs = 0
        imgs = 0
        for track in soup.find_all('div', attrs={'style': match}):
            divs = divs + 1        
            print("\nfound div " + str(divs) + ": ", end = '')
            image_row = ""
            for image in track.find_all('img'):
                #print(image['src'])
                req = urllib.request.urlopen(image['src'])
                arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, -1)
                #img = cv2.imread(image['src'])
                h, w, c = img.shape
                if int(image['width']) != w:
                    print(" !!! ",end = '')
                imgs = imgs + 1
                if h > w:
                    image_row = image_row + "P"
                else:
                    image_row = image_row + "L"
                print(" " + image['width']+" "+str(h)+"x"+str(w), end = '')
            print(" > " + image_row)
        print("\nFound " + str(divs) + " total divs")
        print("Found " + str(imgs) + " total imgs")
