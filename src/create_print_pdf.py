import os
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfWriter, PdfReader


def create_print_pdf(Pdf_File, final_df):

    # Load pdf
    inputpdf = PdfReader(open(Pdf_File.filepath, "rb"))
    output = PdfWriter()

    # Filename
    filename = Path(Pdf_File.save_path) / (f"{Pdf_File.filename}_print.pdf")
    
    # Iterate over Stimmen
    for index, row in final_df.iterrows():

        # Get page
        pagenumber = int(final_df.loc[index]["Seite"]) -1

        # Print amounts
        for i in range(int(row["Druckanzahl"])):
            # Check if multiple pages
            if pd.isnull(row['Seitenanzahl']):
                try:
                    output.add_page(inputpdf.pages[pagenumber])
                except:
                    continue
            else:
                # More then one page
                pageamount = int(final_df.loc[index]["Seitenanzahl"])
                for page in range(pageamount):
                    output.add_page(inputpdf.pages[pagenumber + page])
            
    # Write file to disk
    with open(filename, "wb") as outputStream:
        output.write(outputStream)