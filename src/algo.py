import json
import os
#os.environ["TESSDATA_PREFIX"] = 'C:/Program Files/Tesseract-OCR/tessdata'
import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PyPDF2
#import pytesseract
import yaml
from pdf2image import convert_from_path
from tqdm import tqdm
import tesserocr
#from tesserocr import PyTessBaseAPI
from PIL import Image

from utils.utils import create_lookup_table

# https://towardsdatascience.com/extracting-text-from-scanned-pdf-using-pytesseract-open-cv-cd670ee38052


class PDF_SEPARATOR():

    def __init__(self, pdf_path: str, debugmode: bool=False) -> None:
        """Initialization and parametrization through yml-file
        param: pdf_path: path to pdf
        param: debugmode: prints and visualizations
        """
        self.pdf_path = pdf_path
        self.debugmode = debugmode

        # Load yml-file
        with open(os.path.join(os.getcwd(), "instruments.yml"), encoding='utf8') as f:
            self.instruments = yaml.safe_load(f)
            print(json.dumps(self.instruments, indent=2, ensure_ascii=False))

        # Create lookup-table
        self.lookup_table = create_lookup_table(self.instruments, self.debugmode)
        self.instruments_list = self.instruments.keys()

        # Get number of pdf-pages
        with open(pdf_path, 'rb') as f:
            pdfReader = PyPDF2.PdfReader(f)
            self.num_pdf_pages = len(pdfReader.pages)

        # Create page-instrument table for later separation
        self.pdf_page_instrument_table = pd.DataFrame(
            np.stack((
                np.arange(1,self.num_pdf_pages+1),
                np.zeros((self.num_pdf_pages))),
                axis=1),
            columns=["page", "instrument"]
            )
        self.pdf_page_instrument_table = self.pdf_page_instrument_table.join(pd.DataFrame(
                {
                    'detection': None,
                    'stimme': None,
                    'melodic': None,
                    'accuracy': None
                }, index=self.pdf_page_instrument_table.index
            ))
        
        self.p = 0  # Initial page

    def process_pdf_pages(self):
        """Iterate over pages and store information in dataframe
        """
        self.p +=1
        #for self.p in tqdm(range(1,self.num_pdf_pages+1)):
        img = convert_from_path(pdf_path=self.pdf_path,
                                dpi=200,
                                first_page=self.p,
                                last_page=self.p)


        # 1. Get Regions of Interest
        thresh, line_items_coordinates = self.mark_regions_of_interest(img[0])

        # 2. Performing OCR (Optical character recognition) incl. preprocessing
        start_2 = time.time()
        text_df = self.process_image_to_text(thresh, line_items_coordinates)
        end_2 = time.time()
        print("TIME: OCR: {}".format(end_2 - start_2))

        # 3. Classify translated text
        instrument = self.classify_instrument(text_df)

        if len(instrument) > 1:
            print("More then one instrument detected!\n{}".format(instrument))

            # 4a. Store information in dataframe
            # Multiple detection of instruments
            multiple_detection_code = 0
            for single_inst in instrument:
                inst, detection, number, distinction, overlap = single_inst
                self.pdf_page_instrument_table.loc[multiple_detection_code +
                    self.pdf_page_instrument_table.index[
                        self.pdf_page_instrument_table["page"] == self.p
                        ].item()
                    ] = multiple_detection_code + self.p, inst, detection, number, distinction, overlap
                multiple_detection_code += 1000

        else:
            if instrument is None:
                detection, number, distinction, overlap = None, None, None, None
            else:
                instrument, detection, number, distinction, overlap = instrument[0]
            # 4b. Store information in dataframe
            self.pdf_page_instrument_table.loc[
                self.pdf_page_instrument_table.index[
                    self.pdf_page_instrument_table["page"] == self.p
                    ]
                ] = self.p, instrument, detection, number, distinction, overlap
            
    def mark_regions_of_interest(self, img):
        """
        """
        # Convert PIL.Image to cv2.image
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # Preprocess image with threshold
        img_height, img_width, channels = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #thresh1 = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)
        _,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
        
        # Visualize image if debugmode
        if self.debugmode:
            cv2.imshow("Threshold image", thresh)
            cv2.waitKey(0)
            plt.figure(figsize=(10,10))
            plt.imshow(thresh, cmap=plt.cm.gray)

        # Dilate to combine adjacent text contours
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        dilate = cv2.dilate(thresh, kernel, iterations=4)
        if self.debugmode:
            cv2.imshow("Image with dilation for contours", dilate)
            cv2.waitKey(0)

        # Find contours, highlight text areas, and extract ROIs
        cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        # Get contours
        line_items_coordinates = []
        for c in cnts:
            area = cv2.contourArea(c)
            x,y,w,h = cv2.boundingRect(c)

            # Filter for min-size and location
            if y <= img_height/3:
                if area > 500 and area < (img_height*img_width/6):
                    image = cv2.rectangle(img, (x,y), (x+w, y+h), color=(255,0,255), thickness=3)
                    line_items_coordinates.append([(x,y), (x+w+20, y+h+20)])
        
        # # if self.debugmode:
        # resized_img = cv2.resize(image, (0,0), fx=0.5, fy=0.5) 
        # cv2.imshow("Processed image with detections", resized_img)
        # cv2.waitKey(0)

        return thresh, line_items_coordinates
        
    def process_image_to_text(self, image, line_items_coordinates):

        # Create pandas dataframe
        df = pd.DataFrame(columns=['text'])


        for i in range(len(line_items_coordinates)):

            # get co-ordinates to crop the image
            c = line_items_coordinates[i]

            # cropping image img = image[y0:y1, x0:x1]
            img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]   
            
            sharpening_kernel = np.array([[-1, -1, -1],
                                          [-1, 9, -1],
                                          [-1, -1, -1]])
            sharpened_image = cv2.filter2D(img, -1, sharpening_kernel)
            image_blured = cv2.blur(sharpened_image, (1,1))
            # gaussian_3 = cv2.GaussianBlur(image_blured, (0, 0), 2.0)
            # unsharp_image = cv2.addWeighted(image_blured, 2.0, gaussian_3, -1.0, 0)
            # cv2.imshow('Sharpened Image', image_blured)
            # cv2.waitKey(0)
            df.loc[i] = tesserocr.image_to_text(Image.fromarray(image_blured), lang="deu")
            

        ## Preprocess dataframe
        # Remove empty rows/ only spaces of dataframe
        df.replace('', np.nan, inplace=True)
        df.dropna(inplace=True)

        # Define a function to remove '\n' from a string
        def remove_newlines(text):
            return text.replace('\n', '')
        df['text'] = df['text'].apply(remove_newlines)

        #if self.debugmode: print(df)
        print(df)

        # Add character lenght
        df["text_len"] = df["text"].map(lambda calc: len(calc))

        # Good idea??
        # Clean texts with more then 40 characters and less then 3
        df = df[(df["text_len"] < 60) & (df["text_len"] > 3)]
        if self.debugmode: print(df)

        return df

    def classify_instrument(self, df):

        matching = [s for s in df["text"] if any(f in s for f in self.lookup_table["filters"])]
        
        if len(matching) > 1:
            print("Value Error! More then one matches!\n{}".format(matching))

        if len(matching) == 0:
            print("No match for page {}".format(self.p))
            return None

        # Treat Posaunen and Bass differently due to same filters
        mask_posaune = self.lookup_table['instrument'].isin(["Posaune in b","Posaune in c"])
        posaunen_filter = self.lookup_table[mask_posaune]["filters"]
        mask_bass = self.lookup_table['instrument'].isin(["Bass in c","Bass andere"])
        bass_filter = self.lookup_table[mask_bass]["filters"]

        instrument = []
        for f in self.lookup_table["filters"]:
            if f in matching[0]:
                
                # Remove special characters in string
                for ch in ['\\','`','*','{','}','[',']','/','>','<','^','?','#','+','.','!','$','\'']:  # '(',')'
                    if ch in matching[0]:
                        matching[0] = matching[0].replace(ch,'')

                ## Calculate Overlap
                # Percentage of matching characters
                overlap = round(self.calculate_overlap(matching[0], f), 2)

                numbers, distinction = self.get_stimme(matching[0])

                if distinction is None:
                    distinction = "None"

                if f in (list(posaunen_filter.values) + list(bass_filter.values)):

                    if f in list(posaunen_filter.values):
                            if distinction.lower() == "c" or "c" in matching[0].lower():
                                instrument.append(("Posaune in c", matching[0], numbers, distinction, overlap))
                            else:
                                # Default??
                                instrument.append(("Posaune in b", matching[0], numbers, distinction, overlap))

                    if f in list(bass_filter.values):
                            if distinction.lower() == "c" or "c" in matching[0].lower():
                                instrument.append(("Bass in c", matching[0], numbers, distinction, overlap))
                            else:
                                instrument.append(("Bass andere", matching[0], numbers, distinction, overlap))
                
                else:
                    instrument.append((self.lookup_table.loc[self.lookup_table['filters'] == f]["instrument"].item(), matching[0], numbers, distinction, overlap))

        if not instrument:
            return None

        # Sort by best overlap
        instrument = sorted(instrument, key=lambda x: x[4], reverse=True) 
        print("instrument: {}\ntext: {}".format(instrument, matching[0].strip()))

        return instrument  # Retrun best guess (overlap)
    
    def calculate_overlap(self, detection_string, filter_string):
        if not filter_string:
            return 0
        
        detection_len = len(detection_string)
        filter_len = len(filter_string)
        
        max_matches = 0
        
        for i in range(detection_len):
            for j in range(filter_len):
                if detection_string[i] == filter_string[j]:
                    k = 1
                    while (i+k < detection_len) and (j+k < filter_len) and (detection_string[i+k] == filter_string[j+k]):
                        k += 1
                    if k > max_matches:
                        max_matches = k
        
        return max_matches / detection_len
    
    def get_stimme(self, input_string):

        # Get numbers in detection
        numbers = self.extract_numbers(input_string)

        # Get melodic in detection
        distinction = self.extract_melodic(input_string) # c, b, es

        return numbers, distinction

    def extract_numbers(self, input_string):
        numbers = []
        current_number = ""
        for char in input_string:
            if char.isdigit():
                current_number += char
            elif current_number:
                numbers.append(int(current_number))
                current_number = ""
        if current_number:  # Überprüfen Sie, ob am Ende der Zeichenkette eine Zahl verbleibt
            numbers.append(int(current_number))
        if numbers:
            if len(numbers) > 1:
                return "multiple"
        else:
            return None
        return numbers[0]

    def extract_melodic(self, input_string):

        for i, split in enumerate(input_string.split(" ")):
            if split == "in":
                try:
                    return input_string.split(" ")[i+1]
                except:
                    return None
    
    def get_current_page(self):
        return self.p

def main():

    #pdf_path = os.path.join(os.getcwd(), "Augenblicke - FH1.pdf")
    pdf_path = os.path.join(os.getcwd(), "testdata", "Augenblicke_possaunen_tuben.pdf")
    #pdf_path = os.path.join(os.getcwd(), "testdata", "Gabrielas Song - KL1.pdf")

    PDF_OBJ = PDF_SEPARATOR(pdf_path=pdf_path,
                            debugmode=False)
    pdf_page_instrument_table = PDF_OBJ.process_pdf_pages()
    print(pdf_page_instrument_table)

    cv2.destroyAllWindows()


if __name__=="__main__":

    # Run script
    main()