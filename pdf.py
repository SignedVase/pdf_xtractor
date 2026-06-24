from pathlib import Path
import pymupdf as mpdf
import io
from PIL import Image
import pytesseract
from pypdf import PdfReader
from pypdf.generic import ContentStream

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Pdf:
    def __init__(self, file:Path):
        self._file = file


    def _is_scan(self):
        TEXT_OPERATORS = {
            b"Tj",
            b"TJ",
            b"'",
            b'"',
        }

        reader = PdfReader(self._file)

        ocr = []
        txt = []
        for index, page in enumerate(reader.pages, start=1):
            if "/Font" in page.get("/Resources", {}):
                contents = page.get_contents()

                if contents is None:
                    continue

                content_stream = ContentStream(contents, reader)

                for operands, operator in content_stream.operations:
                    if operator  in TEXT_OPERATORS:
                        txt.append(index)
                        break
                if index not in txt and index not in ocr:
                    ocr.append(index)
            else:
                ocr.append(index)


        reader.close()

        if ocr:
            return True, ocr
        else:
            return False, None


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
                    rotate_osd = int(osd.split('Rotate:')[1].split('\n')[0].strip())


                    if rotate_osd != 0 and rotate != 0:
                        page.set_rotation(0)

                    if rotate_osd != rotate and rotate == 0:
                        page.set_rotation(rotate_osd)


    @staticmethod
    def _ext_txt(arq:mpdf.Document):
        """
        Extracts text from each page of a PDF document.

        :param arq: A PyMuPDF Document object.
        :type arq: mpdf.Document
        :return: A list of strings, where each item contains the text of one PDF page.
        :rtype: list[str]
        """

        pages = []
        for page in arq:
            txt = page.get_text()
            pages.append(txt)
        return pages


    def _ext_img(self):
        pass




    def extract(self, rotate:bool=True):
        pass
        # var, ocr_pg_idx = self._is_scan()
        # pdf = mpdf.open(self._file)
        # if rotate:
        #     self._rotate(pdf)
        #     pdf.saveIncr()
        # pdf.close()
        # print(var, ocr_pg_idx)