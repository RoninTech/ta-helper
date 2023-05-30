#!/usr/bin/python

from turtle import width
from bs4 import BeautifulSoup
import os, glob
import cv2
import urllib.request
import numpy as np

OK_WIDTHS=[210, 315, 370, 1000]
BAD_FILES=[]

# Process all .md files in folder and sub-folders for image blocks
for filename in glob.glob('**/*.md', recursive=True):
    print("\nProcessing " + filename + "\n")
    with open(os.path.join(os.getcwd(), filename), 'r') as f:
        bad_file = False
        contents = f.read()
        soup = BeautifulSoup(contents, 'lxml')
        match = "text-align: center"
        divs = 0
        imgs = 0
        for track in soup.find_all('div', attrs={'style': match}):
            divs = divs + 1        
            print("Found div " + str(divs) + ": ", end = '')
            image_row = ""
            for image in track.find_all('img'):
                #print(image['src'])
                req = urllib.request.urlopen(image['src'])
                arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, -1)
                #img = cv2.imread(image['src'])
                h, w, c = img.shape
                if w not in OK_WIDTHS:
                    print(" *** ",end = '')
                    bad_file = True
                if int(image['width']) != w:
                    print(" !!! ",end = '')
                    bad_file = True
                imgs = imgs + 1
                if h > w:
                    orientation = "P"
                else:
                    orientation = "L"
                image_row = image_row + orientation
                if bad_file:
                    BAD_FILES.append(filename)
                    print(" " + image['width']+"("+orientation+") "+str(h)+"x"+str(w), end = '')
                else:
                    print(" " + image['width']+"("+orientation+") ", end = '')
            print(" > " + image_row)
        print("\nFound " + str(divs) + " total divs")
        print("Found " + str(imgs) + " total imgs")

print("\n\nBad Files:\n\n" + BAD_FILES)
