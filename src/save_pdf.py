import pandas as pd
import os
import yaml
from pathlib import Path
import shutil
import time
from time import localtime, strftime
from PyPDF2 import PdfWriter, PdfReader

from dataclass import PDF_File


# Create folder in save dir
def save_pdf_files(Pdf_File, instruments_list, folder_options, final_df):
    
    # Create dir
    save_dir = Path(Pdf_File.save_path) / f"TaNoKo_{strftime('%Y-%m-%d_%H-%M-%S', localtime(time.time()))}_{Pdf_File.filename}"
    save_dir.mkdir(parents=True, exist_ok=True)  # make dir

    # Iterate over instruments
    for i, instrument in enumerate(instruments_list):
        b = save_dir / ("{:02d} ".format(i+1) + instrument)
        b.mkdir(parents=True, exist_ok=True)  # make dir

        # Iterate over folders
        for s in [b / y for y in folder_options]:
            s.mkdir(parents=True, exist_ok=True)  # make dir
            
            # Check folder selection and create folder for song name
            if Pdf_File.folder_option in str(s):
                k = s / Pdf_File.filename
                k.mkdir(parents=True, exist_ok=True)

                # Check if matching instrument in final_df
                if not final_df.loc[final_df["instrument"] == instrument].empty:
                    
                    for index, row in final_df.loc[final_df["instrument"] == instrument].iterrows():

                        # Check if stimme has a value
                        if row["stimme"] == "None":
                            stimme = ""
                        else:
                            stimme = str(row["stimme"])

                        detection = row["detection"]

                        inputpdf = PdfReader(open(Pdf_File.filepath, "rb"))
                        output = PdfWriter()
                        try:
                            output.add_page(inputpdf.pages[index])
                        except:
                            page = int(final_df.loc[index]["page"])
                            for i in range(4):
                                page -=1000
                                try:
                                    index = final_df.index[final_df["page"] == page].item()
                                    output.add_page(inputpdf.pages[index])
                                    break
                                except:
                                    continue

                        filename = k / (f"{Pdf_File.filename} - {detection}.pdf") # + f"{(' ' + stimme) if not stimme == '' else ''}.pdf")
                        # Write file to disk
                        with open(filename, "wb") as outputStream:
                            output.write(outputStream)


                        # for i in range(len(inputpdf.pages)):
                        #     output = PdfWriter()
                        #     output.add_page(inputpdf.pages[i])
                        #     with open("document-page%s.pdf" % i, "wb") as outputStream:
                        #         output.write(outputStream)
                else:
                    continue


if __name__ == "__main__":

    with open(os.path.join(os.getcwd(), "instruments.yml"), encoding='utf8') as f:
        instruments = yaml.safe_load(f)
    with open(os.path.join(os.getcwd(), "config.yml"), encoding='utf8') as f:
        config = yaml.safe_load(f)
    folder_options = config["folder_options"]
    instrument_list = instruments.keys()

    Pdf_File = PDF_File()
    Pdf_File.save_path = r"C:\Users\robin\OneDrive - bwedu\Dokumente\Python_projects\pdf_splitter\testdata\test"
    Pdf_File.filepath = r"C:\Users\robin\OneDrive - bwedu\Dokumente\Python_projects\pdf_splitter\testdata\Augenblicke.pdf"
    save_pdf_files(Pdf_File, instrument_list, folder_options)