import PyPDF2
from pypdf import PdfReader
import aspose.ocr as ocr
import os
import cv2
from PIL import Image
import matplotlib.pyplot as plt

from pdf2image import convert_from_path, convert_from_bytes
import pytesseract
import pandas as pd
import numpy as np
import argparse as args
import yaml
import json
from tqdm import tqdm

from utils import create_lookup_table

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


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
            self.config = yaml.safe_load(f)
            print(json.dumps(self.config, indent=2, ensure_ascii=False))

        # Create lookup-table
        self.lookup_table = create_lookup_table(self.config, self.debugmode)

        # Get number of pdf-pages
        with open(pdf_path, 'rb') as f:
            pdfReader = PyPDF2.PdfReader(f)
            self.num_pdf_pages = len(pdfReader.pages)

        # Create page-instrument table for later separation
        self.pdf_page_instrument_table = pd.DataFrame(
            np.stack((
                np.arange(1,self.num_pdf_pages+1),
                np.zeros(self.num_pdf_pages)),
                axis=1),
            columns=["page", "instrument"]
            )

    def process_pdf_pages(self):
        """Iterate over pages and store information in dataframe
        """
        for self.p in tqdm(range(1,self.num_pdf_pages+1)):
            img = convert_from_path(pdf_path=self.pdf_path,
                                    dpi=200,
                                    first_page=self.p,
                                    last_page=self.p)
            
            # 1. Get Regions of Interest
            thresh, line_items_coordinates = self.mark_regions_of_interest(img[0])

            # 2. Performing OCR (Optical character recognition) incl. preprocessing
            text_df = self.process_image_to_text(thresh, line_items_coordinates)
            
            # 3. Classify translated text
            instrument = self.classify_instrument(text_df)

            # 4. Store information in dataframe
            self.pdf_page_instrument_table.loc[self.pdf_page_instrument_table["page"] == self.p, ["instrument"]] = instrument

        print(self.pdf_page_instrument_table)
                


            
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
                if area > 500:
                    image = cv2.rectangle(img, (x,y), (x+w, y+h), color=(255,0,255), thickness=3)
                    line_items_coordinates.append([(x,y), (x+w, y+h)])
        
        if self.debugmode:
            cv2.imshow("Processed image with detections", image)
            cv2.waitKey(0)

        return thresh, line_items_coordinates
        
    def process_image_to_text(self, image, line_items_coordinates):

        # Create pandas dataframe
        df = pd.DataFrame(columns=['text'])

        for i in range(len(line_items_coordinates)):

            # get co-ordinates to crop the image
            c = line_items_coordinates[i]

            # cropping image img = image[y0:y1, x0:x1]
            img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]    

            # if self.debugmode:
            #     plt.figure(figsize=(10,10))
            #     plt.imshow(img, cmap=plt.cm.gray)

            # pytesseract image to string to get results
            df.loc[i] = str(pytesseract.image_to_string(img, lang="deu")) # use german language (ä,ü,ö,ß,...)
            

        ## Preprocess dataframe
        # Remove empty rows/ only spaces of dataframe
        df.replace('', np.nan, inplace=True)
        df.dropna(inplace=True)
        if self.debugmode: print(df)

        # Add character lenght
        df["text_len"] = df["text"].map(lambda calc: len(calc))

        # Good idea??
        # Clean texts with more then 40 characters and less then 6
        df = df[(df["text_len"] < 40) & (df["text_len"] > 3)]
        if self.debugmode: print(df)

        return df

    def classify_instrument(self, df):

        matching = [s for s in df["text"] if any(f in s for f in self.lookup_table["filters"])]
        
        if len(matching) > 1:
            print("Value Error! More then one matches!\n{}".format(matching))

        if len(matching) == 0:
            print("No match for page {}".format(self.p))
            return None

        instrument = []
        for f in self.lookup_table["filters"]:
            if f in matching[0]:
                if instrument: # Check if list has been already filled
                    # Check if new detection is already satisfied, if yes: skip
                    if any(self.lookup_table.loc[self.lookup_table['filters'] == f]["instrument"].item() in x for x in instrument):
                        continue
                    else:
                        instrument.append(self.lookup_table.loc[self.lookup_table['filters'] == f]["instrument"].item())
                else:
                    instrument.append(self.lookup_table.loc[self.lookup_table['filters'] == f]["instrument"].item())

        if len(instrument) > 1:
            print("More then one instrument detected!\n{}".format(instrument))


        print("instrument: {},\ntext: {}".format(instrument, matching))

        return instrument[0]





# def preprocess_pdf(pdf_path: str):

#     pages = convert_from_path(pdf_path=pdf_path,
#                               dpi=200,
#                               last_page=4
#                               )




#     reader = PdfReader(pdf_path)
#     # for page in reader.pages:

        
#     #     #ex = pdf.getPage(6)

#     #     for image in page.images:

#     #         open_cv_image = convert_from_bytes(image.data)
#     #         # Convert RGB to BGR
#     #         open_cv_image = open_cv_image[:, :, ::-1].copy()
#     #         cv2.imshow("window_name", open_cv_image)
#     #         cv2.waitKey(0)


#     #         # with open(image.name, "wb") as fp:
#     #         #     fp.write(image.data)


#     # print(len(reader.pages))



#     # Create dataframe with length equals number of pages

#     # Generate jpgs of each page






# # def convert_pdf_to_img(pdf_path):

# #     pages = convert_from_path(pdf_path=pdf_path)
    

# #     i = 1
# #     for page in pages:
# #         image_name = "Page_" + str(i) + ".jpg"  
# #         page.save(image_name, "JPEG")
# #         i = i+1 


# def mark_region(image_path):
    
#     im = cv2.imread(image_path)
#     im_height, im_width, channels = im.shape

#     gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
#     #blur = cv2.GaussianBlur(gray, (9,9), 0)
#     thresh1 = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)
#     _,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
    
#     cv2.imshow("window_name", thresh)
#     cv2.waitKey(0)
#     plt.figure(figsize=(10,10))
#     plt.imshow(thresh, cmap=plt.cm.gray)


#     # Dilate to combine adjacent text contours
#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
#     dilate = cv2.dilate(thresh, kernel, iterations=4)
#     cv2.imshow("window_name", dilate)
#     cv2.waitKey(0)

#     # Find contours, highlight text areas, and extract ROIs
#     cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     cnts = cnts[0] if len(cnts) == 2 else cnts[1]

#     line_items_coordinates = []
#     for c in cnts:
#         area = cv2.contourArea(c)
#         x,y,w,h = cv2.boundingRect(c)

#         # if y >= 600 and x <= 1000:
#         #     if area > 10000:
#         #         image = cv2.rectangle(im, (x,y), (2200, y+h), color=(255,0,255), thickness=3)
#         #         line_items_coordinates.append([(x,y), (2200, y+h)])

#         if y <= im_height/3:
#             if area > 500:
#                 image = cv2.rectangle(im, (x,y), (x+w, y+h), color=(255,0,255), thickness=3)
#                 line_items_coordinates.append([(x,y), (x+w, y+h)])

#         # if y >= 400 and x<= 1000:
#         #     image = cv2.rectangle(im, (x,y), (2200, y+h), color=(255,0,255), thickness=3)
#         #     line_items_coordinates.append([(x,y), (2200, y+h)])

#     return thresh, image, line_items_coordinates

# def process_image_to_text(image, line_items_coordinates):

#     # Create pandas dataframe
#     df = pd.DataFrame(columns=['text'])

#     for i in range(len(line_items_coordinates)):

#         # get co-ordinates to crop the image
#         c = line_items_coordinates[i]

#         # cropping image img = image[y0:y1, x0:x1]
#         img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]    

#         plt.figure(figsize=(10,10))
#         plt.imshow(img, cmap=plt.cm.gray)

#         # convert the image to black and white for better OCR
#         #ret,thresh1 = cv2.threshold(img,120,255,cv2.THRESH_BINARY)

#         # pytesseract image to string to get results
#         df.loc[i] = str(pytesseract.image_to_string(img, lang="deu")) # use german language (ä,ü,ö,ß,...)
        

#     ## Preprocess dataframe
#     # Remove empty rows/ only spaces of dataframe
#     print(df)
#     df.replace('', np.nan, inplace=True)
#     df.dropna(inplace=True)
#     print(df)

#     # Add character lenght
#     df["text_len"] = df["text"].map(lambda calc: len(calc))

#     # Good idea??
#     # Clean texts with more then 40 characters and less then 6
#     df = df[(df["text_len"] < 40) & (df["text_len"] > 5)]
#     print(df)

#     return df






def main():

    #pdf_path = os.path.join(os.getcwd(), "Augenblicke - FH1.pdf")
    pdf_path = os.path.join(os.getcwd(), "testdata", "Augenblicke.pdf")

    PDF_OBJ = PDF_SEPARATOR(pdf_path=pdf_path,
                            debugmode=False)
    PDF_OBJ.process_pdf_pages()


    cv2.destroyAllWindows()


if __name__=="__main__":

    # Run script
    main()