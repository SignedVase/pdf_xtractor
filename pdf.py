import shutil
from pathlib import Path
import pymupdf as mpdf
import io
from PIL import Image, ImageOps
import pytesseract
from pypdf import PdfReader
from pypdf.generic import ContentStream

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Pdf:
    def __init__(self, file:Path) -> None:
        self._file = file


    def _is_scan(self) ->  list[int]:
        """
        Identifies PDF pages that likely require OCR processing.

        This method analyzes each page of the PDF and checks whether it contains
        font resources and native PDF text operators in its content stream. Pages
        without font resources, without content, or without detectable text
        operators are considered scanned or image-based pages and are marked for
        OCR.

        :return: A list of zero-based page indexes that likely require OCR.
        :rtype: list[int]
        """
        TEXT_OPERATORS = {
            b"Tj",
            b"TJ",
            b"'",
            b'"',
        }

        reader = PdfReader(self._file)

        ocr = []
        txt = []
        for index, page in enumerate(reader.pages):
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

        return ocr


    @staticmethod
    def _rotate(pdf:mpdf.Document) -> None:

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
    def _ext_txt(arq:mpdf.Document, idx:list) -> dict[int,str]:
        """
        Extracts native text from the pages of a PDF document.

        This method iterates through the PDF pages and extracts text only from pages
        that are not listed in ``idx``. If ``idx`` is empty, text is extracted from all
        pages.

        :param arq: A PyMuPDF Document object.
        :type arq: mpdf.Document
        :param idx: A list of zero-based page indexes that should be skipped during
                    native text extraction, usually because they will be processed
                    with OCR.
        :type idx: list[int]
        :return: A dictionary where each key is a zero-based page index and each value
                 is the extracted native text from that page.
        :rtype: dict[int, str]
        """

        pages = {}
        for index, page in enumerate(arq.pages()):
            if not idx or index not in idx:
                txt = page.get_text()
                pages.update({index:txt})
        return pages


    @staticmethod
    def _ext_ocr(pdf:mpdf.Document , arq: Path, ocr_idx:list[int]) -> tuple[dict[int,str], Path]:
        """
        Applies OCR to selected pages of a PDF document and creates a searchable PDF copy.

        This method processes only the pages whose indexes are present in ``ocr_idx``.
        Pages not listed in ``ocr_idx`` are copied directly to the output document without
        OCR. For OCR pages, the method renders the page as an image, adds a black border
        to improve text recognition, extracts the text using Tesseract, and creates a
        searchable PDF page. The added border is clipped out visually so that the final
        page keeps the original page size and appearance.

        The generated searchable PDF is saved with the suffix ``_ocr`` added to the
        original file name. The output file is then moved to an ``OCR`` folder inside
        the original file's parent directory if a file with the same name does not
        already exist there.

        :param pdf: A PyMuPDF Document object containing the source PDF pages.
        :type pdf: mpdf.Document
        :param arq: The original PDF file path used to generate the output file name.
        :type arq: Path
        :param ocr_idx: A list of zero-based page indexes that should be processed with OCR.
        :type ocr_idx: list[int]
        :return: A tuple containing a dictionary with the extracted OCR text by page index
         and the final path of the generated OCR PDF file.
        :rtype: tuple[dict[int, str], Path]
        """

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

            pix = page.get_pixmap(dpi=300, alpha=False)
            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

            original_w, original_h = image.size

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

            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                image=image_with_border,
                extension="pdf",
                lang="por",
                config=config
            )

            ocr_doc = mpdf.open(stream=pdf_bytes, filetype="pdf")
            ocr_page = ocr_doc[0]

            ocr_rect = ocr_page.rect

            clip = mpdf.Rect(
                border_px / expanded_w * ocr_rect.width,
                border_px / expanded_h * ocr_rect.height,
                (border_px + original_w) / expanded_w * ocr_rect.width,
                (border_px + original_h) / expanded_h * ocr_rect.height,
            )

            fixed_doc = mpdf.open()
            fixed_page = fixed_doc.new_page(
                width=original_rect.width,
                height=original_rect.height
            )

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
        backup = Path(f"{arq.parent}/OCR")
        backup.mkdir(exist_ok=True)
        final_path = backup / output_path.name
        if not final_path.exists():
            shutil.move(output_path, backup)
        return txt_ocr, final_path






    def extract(self, rotate :bool=True, only_ocr :bool=False) -> dict[int, str]:
        """
        Extracts text from a PDF document using native text extraction and/or OCR.

        This method opens the PDF file, optionally corrects page rotation, and extracts
        text from the document. By default, it detects which pages are likely scanned
        or image-based and applies OCR only to those pages, while extracting native text
        from the remaining pages. If ``only_ocr`` is enabled, OCR is applied to every
        page of the PDF.

        When ``rotate`` is enabled, the PDF pages may be rotated in place before text
        extraction, and the changes are saved incrementally to the original file.

        :param rotate: Whether to detect and correct page rotation before extraction.
        :type rotate: bool
        :param only_ocr: Whether to force OCR extraction on all pages instead of mixing
                         native text extraction and OCR.
        :type only_ocr: bool
        :return: A dictionary containing the extracted text, where each key is a
                 zero-based page index and each value is the extracted page text.
        :rtype: dict[int, str]
        """
        pdf = mpdf.open(self._file)
        textos = {}

        if rotate:
            self._rotate(pdf)
            pdf.saveIncr()

        if only_ocr:
            ocr_pg_idx = [pg for pg in range(pdf.page_count)]
            textos, path =self._ext_ocr(pdf, self._file, ocr_pg_idx)

        if not only_ocr:
            ocr_pg_idx = self._is_scan()

            if ocr_pg_idx:
                dict_txt = self._ext_txt(pdf, ocr_pg_idx)
                dict_ocr, path = self._ext_ocr(pdf, self._file, ocr_pg_idx)
                textos = dict(sorted((dict_txt | dict_ocr).items()))
            else:
                textos = self._ext_txt(pdf, ocr_pg_idx)

        pdf.close()

        return textos

