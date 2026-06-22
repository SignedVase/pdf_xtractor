from pathlib import Path
import pdfplumber
class Pdf:
    def __init__(self, file:Path):
        self.file = file



    def is_scan(self):
        pass

    @staticmethod
    def ext_txt(arq:pdfplumber.PDF):
        """
        Extracts text from each page of a PDF.

        :param arq: A pdfplumber PDF object.
        :return: A list of strings, one for each page of the PDF.
        """
        pages = []
        for page in arq.pages:
            txt = page.extract_text()
            pages.append(txt)
        return pages


    def ext_img(self):
        pass

    def rotate(self):
        pass


    def extract(self):
        pdf = pdfplumber.open(self.file)
        try:
            self.ext_txt(pdf)
        except:
            print('Deu erro')

        pdf.close()
        pass