#!/usr/bin/env python
from flask import Flask, render_template, Response
from flask import make_response
import sys
import numpy as np
import cv2
import imgtransform as ti


frame_duration = 25
fps = 1000/frame_duration

def transform_img(img):
    # get height and width
    height, width, _ = img.shape

    # convert to grayscale
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray_image', gray_image)

    # subtract asphalt color and take absolute value
    absimg = cv2.absdiff(gray_image, 80)

    # Otsu binarization
    ret, bimg = cv2.threshold(absimg, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #cv2.imshow('bimg',bimg)

    # define kernel for convolution
    kernel = np.ones((5, 5), np.uint8)

    # morphological operations to reduce noise
    opening = cv2.morphologyEx(bimg, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    # erosion = cv2.erode(closing,kernel,iterations = 3)
    dilation = cv2.dilate(closing, kernel, iterations=3)
    #cv2.imshow("dilation", dilation)

    for i in range(0, width, int(width/5)):
        for block in range(2):
            j = 0
            while j < int(height/2):
                j_ = int(block*height/2) + j
                if i<width and j_<height:
                    if (ti.checkoccupancy(i, j_, i + int(width/5), j_ + int(height*0.13), dilation)
                            or (i > 2.5/5*width)):
                        colour = (0, 0, 255)
                        # cv2.rectangle(img, (i + 5, j_ + 5), (i + int(width/5)-5, j_ + int(height*0.13)-5), (0, 0, 255), 2)
                    else:
                        colour = (0, 255, 0)
                        # cv2.rectangle(img, (i + 5, j_ + 5), (i + int(width/5)-5, j_ + int(height*0.13)-5), (0, 255, 0), 2)
                    cv2.rectangle(img, (i + 5, j_ + 5), (i + int(width / 5) - 5, j_ + int(height * 0.13) - 5), colour, 2)
                    j_ += int(height * (0.22 + 0.13))
                    j = j_ - int(block*height/2)
        i += 5

    return img


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def get_frame():
    cap = cv2.VideoCapture("resources/parking480.mov")

    while True:
        

        ret, frame = cap.read()
        frame_count = 0
    
    #while(ret):
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # top left
        tl = (293, 96)
        # top right
        tr = (490, 100)
        #bottom left
        bl = (30, 310)
        #bottom right
        br = (560, 330)

        # max width
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        # max height
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        t1 = (0, 0)
        t2 = (maxWidth, 0)
        t3 = (0, maxHeight)
        t4 = (maxWidth, maxHeight)

        pts1 = np.float32([list(tl), list(tr), list(bl), list(br)])
        pts2 = np.float32([list(t1), list(t2), list(t3), list(t4)])

        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        result = cv2.warpPerspective(frame, matrix, (maxWidth, maxHeight))

        cv2.imshow('Pre-label', result)

        frame_count += 1
        if frame_count > fps:
            # if __name__ == '__main__':
            #   Thread(target=transform_img, args=(result, )).start()
            output_img = transform_img(result)
            imgencode=cv2.imencode('.jpg',output_img)[1]
            stringData=imgencode.tostring()
            yield (b'--frame\r\n'
                b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')

            frame_count = 0
    del(cap)

        
        #cv2.imshow('frame', frame)

    













@app.route('/calc')
def calc():
     return Response(get_frame(),mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='localhost', debug=True, threaded=True)
