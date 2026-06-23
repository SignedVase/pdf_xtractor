from pathlib import Path
import pymupdf as mpdf
class Pdf:
    def __init__(self, file:Path):
        self.file = file



    def is_scan(self):
        pass

    @staticmethod
    def ext_txt(arq:mpdf.Document):
        """
        Extracts text from each page of a PDF.

        :param arq: A pdfplumber PDF object.
        :return: A list of strings, one for each page of the PDF.
        """
        pages = []
        for page in arq:
            txt = page.get_text()
            pages.append(txt)
        return pages


    def ext_img(self):
        pass

    def rotate(self):
        pass


    def extract(self):
        pass
        # pdf = mpdf.open(self.file)
        # for page in pdf:
        #     print(page.xref)
        # print(self.ext_txt(pdf))