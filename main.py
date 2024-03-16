import json
import os
os.environ["TESSDATA_PREFIX"] = 'C:/Program Files/Tesseract-OCR/tessdata'
import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PyPDF2
import pytesseract
import yaml
from pdf2image import convert_from_path
from pypdf import PdfReader
from tqdm import tqdm
import tesserocr
from tesserocr import PyTessBaseAPI
from PIL import Image
import threading
import multiprocessing

from utils import create_lookup_table

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
            start_2 = time.time()
            text_df = self.process_image_to_text(thresh, line_items_coordinates)
            end_2 = time.time()
            print("TIME: OCR: {}".format(end_2 - start_2))

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

        # ########### Threading ##############
        # # Maximum number of threads
        # max_threads = 8  # Adjust this based on your requirements

        # # Semaphore to limit the number of concurrent threads
        # thread_semaphore = threading.Semaphore(max_threads)

        # def perform_ocr_threaded(img, id):
        #     df.loc[id] = tesserocr.image_to_text(Image.fromarray(img), lang="deu")

        # def worker(img, id):
        #     with thread_semaphore:
        #         perform_ocr_threaded(img, id)
        
        # # Create threads for each image
        # threads = []
        # for id, c in zip(range(len(line_items_coordinates)), line_items_coordinates):
        #     img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]
        #     thread = threading.Thread(target=worker, args=(img,id,))
        #     threads.append(thread)
        #     thread.start()

        # # Warten Sie darauf, dass alle Threads beendet sind
        # for thread in threads:
        #     thread.join()

        # print("All threads have finished processing.")

        # ############ Multiprocessing ##############

        # # Maximum number of processes
        # max_processes = 4  # Adjust this based on your requirements

        # # Semaphore to control concurrent access
        # semaphore = multiprocessing.Semaphore(max_processes)

        # # def perform_ocr_threaded(img, id):
        # #     df.loc[id] = tesserocr.image_to_text(Image.fromarray(img), lang="deu")

        # # def worker(img, id, semaphore):
        # #     with semaphore:
        # #         perform_ocr_threaded(img, id)

        # # Create a list to store process objects
        # processes = []

        # for id, c in zip(range(len(line_items_coordinates)), line_items_coordinates):
        #     # Create a new process for each image
        #     img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]
        #     process = multiprocessing.Process(target=worker, args=(img,id,semaphore,))
        #     processes.append(process)
        #     process.start()

        # # Wait for all processes to finish
        # for process in processes:
        #     process.join()

        # print("All processes have finished processing.")


        for i in range(len(line_items_coordinates)):

            # get co-ordinates to crop the image
            c = line_items_coordinates[i]

            # cropping image img = image[y0:y1, x0:x1]
            img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]   

            # if self.debugmode:
            #     plt.figure(figsize=(10,10))
            #     plt.imshow(img, cmap=plt.cm.gray)

            # pytesseract image to string to get results
            # TODO: Speedup: https://pypi.org/project/tesserocr/
            # https://stackoverflow.com/questions/66334737/pytesseract-is-very-slow-for-real-time-ocr-any-way-to-optimise-my-code
            # print(tesserocr.tesseract_version())  # print tesseract-ocr version
            # print(tesserocr.get_languages())
            #PyTessBaseAPI(path='C:/Program Files/Tesseract-OCR/tessdata')
            #start_10 = time.time()
            df.loc[i] = tesserocr.image_to_text(Image.fromarray(img), lang="deu")
            #end_10 = time.time()
            #print("TIME: OCR_tesseract_better?: {}".format(end_10 - start_10))


            # start_1 = time.time()
            # df.loc[i] = str(pytesseract.image_to_string(img, lang="deu")) # use german language (ä,ü,ö,ß,...)
            # end_1 = time.time()
            # print("TIME: OCR_tesseract: {}".format(end_1 - start_1))
            

        
            

        ## Preprocess dataframe
        # Remove empty rows/ only spaces of dataframe
        df.replace('', np.nan, inplace=True)
        df.dropna(inplace=True)
        if self.debugmode: print(df)

        # Add character lenght
        df["text_len"] = df["text"].map(lambda calc: len(calc))

        # Good idea??
        # Clean texts with more then 40 characters and less then 6
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


        print("instrument: {},\ntext: {}".format(instrument, matching[0].strip()))

        return instrument[0]


def main():


    #pdf_path = os.path.join(os.getcwd(), "Augenblicke - FH1.pdf")
    pdf_path = os.path.join(os.getcwd(), "testdata", "Augenblicke.pdf")

    # Load config-yml-file with tesseract information
    with open(os.path.join(os.getcwd(), "config.yml"), encoding='utf8') as f:
        config = yaml.safe_load(f)
        pytesseract.pytesseract.tesseract_cmd = config["tesseract_path"]

    PDF_OBJ = PDF_SEPARATOR(pdf_path=pdf_path,
                            debugmode=False)
    PDF_OBJ.process_pdf_pages()


    cv2.destroyAllWindows()


if __name__=="__main__":

    # Run script
    main()