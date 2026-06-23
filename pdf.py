from pathlib import Path
import pymupdf as mpdf
import io
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Pdf:
    def __init__(self, file:Path):
        self._file = file


    def _is_scan(self):
        pass

    @staticmethod
    def _rotate(pdf:mpdf.Document):

        """
        Detects and corrects the rotation of each page in a PDF document.

        This method renders each PDF page as an image and uses Tesseract OSD
        (Orientation and Script Detection) to identify the visual rotation of
        the page. If the detected orientation differs from the page's current
        rotation metadata, the page rotation is adjusted accordingly.

        :param pdf: A PyMuPDF Document object whose pages will be checked and rotated.
        :type pdf: mpdf.Document
        :return: None. The PDF document is modified in place.
        :rtype: None
        """

        for page in pdf:
                rotate:int = page.rotation

                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                try:
                    osd = pytesseract.image_to_osd(img, lang='osd', config="--psm 0")
                except Exception as e:
                    osd = None
                    print(f'Erro: {e}')
                if osd is not None:
                    rotate_osd = osd.split('Rotate:')[1].split('\n')[0].strip()


                    if int(rotate_osd) != 0 and int(rotate) != 0:
                        page.set_rotation(0)

                    if int(rotate_osd) != int(rotate) and int(rotate) == 0:
                        page.set_rotation(int(rotate_osd))


    @staticmethod
    def _ext_txt(arq:mpdf.Document):
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


    def _ext_img(self):
        pass




    def extract(self, rotate:bool=True):
        pdf = mpdf.open(self._file)
        if rotate:
            self._rotate(pdf)
            pdf.saveIncr()
        pdf.close()