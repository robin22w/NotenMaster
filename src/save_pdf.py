import pandas as pd
import os
import yaml
from pathlib import Path
import shutil

from dataclass import PDF_File


# Create folder in save dir
def save_pdf_files(Pdf_File, instruments_list, folder_options, final_data):
    


 
    dir = Path(Pdf_File.save_path)
    # if dir.exists():
    #     shutil.rmtree(dir)  # delete dir


    for b in [dir / ("{:02d} ".format(i) + x) for i,x in enumerate(instruments_list)]:
        b.mkdir(parents=True, exist_ok=True)  # make dir
        for s in [b / y for y in folder_options]:
            s.mkdir(parents=True, exist_ok=True)  # make dir


    for data in final_data:
        page,instrument,stimme = data
        
        
        
        
        filename = f"{Pdf_File.filename} - {instrument} {stimme}.pdf"

        pass


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