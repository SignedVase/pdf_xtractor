from pathlib import Path
import pdfplumber
class Pdf:
    def __init__(self, file:Path):
        self.pdf = pdfplumber.open(file)



    def is_scan(self):
        pass


    def ext_txt(self):
        pass


    def ext_img(self):
        pass

    def rotate(self):
        pass


    def extract(self):
        pass