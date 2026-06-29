import shutil
from pathlib import Path
import pymupdf as mpdf
import io
from PIL import Image, ImageOps
import pytesseract
from pypdf import PdfReader, PdfWriter
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


    @staticmethod
    def _ext_ocr(pdf:mpdf.Document , arq: Path, ocr_idx:list[int]) -> tuple[dict[int,str], Path]:
        src = pdf
        border_px = 40

        config = (
            "--oem 1 --psm 6 --dpi 300 "
            "-c preserve_interword_spaces=1"
        )

        output_path = arq.with_name(f"{arq.stem}_ocr{arq.suffix}")


        out = mpdf.open()
        txt_ocr = {}

        for idx in range(src.page_count):
            page = src.load_page(idx)

            if idx not in ocr_idx:
                out.insert_pdf(src, from_page=idx, to_page=idx)
                continue

            original_rect = page.rect

            # Renderiza a página original
            pix = page.get_pixmap(dpi=300, alpha=False)
            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

            original_w, original_h = image.size

            # Aqui você mantém a borda preta para ajudar o OCR
            image_with_border = ImageOps.expand(
                image,
                border=border_px,
                fill="black"
            )

            expanded_w, expanded_h = image_with_border.size

            txt = pytesseract.image_to_string(
                image=image_with_border,
                lang="por",
                config=config
            )

            if isinstance(txt, bytes):
                txt = txt.decode("utf-8", errors="replace")
            txt_ocr.update({idx: txt})

            # Gera PDF pesquisável com a imagem COM borda
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                image=image_with_border,
                extension="pdf",
                lang="por",
                config=config
            )

            ocr_doc = mpdf.open(stream=pdf_bytes, filetype="pdf")
            ocr_page = ocr_doc[0]

            # Calcula, no sistema de coordenadas do PDF gerado pelo Tesseract,
            # qual área corresponde à página original sem a borda
            ocr_rect = ocr_page.rect

            clip = mpdf.Rect(
                border_px / expanded_w * ocr_rect.width,
                border_px / expanded_h * ocr_rect.height,
                (border_px + original_w) / expanded_w * ocr_rect.width,
                (border_px + original_h) / expanded_h * ocr_rect.height,
            )

            # Cria uma página final com o mesmo tamanho da página original
            fixed_doc = mpdf.open()
            fixed_page = fixed_doc.new_page(
                width=original_rect.width,
                height=original_rect.height
            )

            # Insere apenas a parte útil do PDF OCR,
            # descartando visualmente a borda preta
            fixed_page.show_pdf_page(
                fixed_page.rect,
                ocr_doc,
                0,
                clip=clip,
                keep_proportion=False
            )

            out.insert_pdf(fixed_doc, from_page=0, to_page=0)

            ocr_doc.close()
            fixed_doc.close()

        out.save(output_path, garbage=4, deflate=True)
        out.close()
        backup = Path(f"{arq.parent}/originais")
        backup.mkdir(exist_ok=True)
        if not (backup / arq.name).exists():
            shutil.move(arq, backup)
        return txt_ocr, output_path






    def extract(self, rotate:bool=True):
        pass
        # var, ocr_pg_idx = self._is_scan()
        # pdf = mpdf.open(self._file)
        # if rotate:
        #     self._rotate(pdf)
        #     pdf.saveIncr()
        # pdf.close()
        # print(var, ocr_pg_idx)