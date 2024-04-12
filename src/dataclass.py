from dataclasses import dataclass
import pandas as pd


@dataclass
class PDF_File():
    filename: str = "Dummy"
    filepath: str = ""
    excelpath: str = ""
    num_pages: int = 10
    folder_option: str = "Rot"
    dataframe: pd.DataFrame = pd.DataFrame()
    save_path: str = ""


if __name__ == "__main__":

    print(PDF_File())