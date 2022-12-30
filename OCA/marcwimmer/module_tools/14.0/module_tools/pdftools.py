import subprocess
import tempfile
import os
import base64
import copy
import io

def rotate_pdf(pdf, degrees):
    """
    :params pdf: binary content

    """
    import PyPDF2
    stream = io.BytesIO()
    stream.write(pdf)
    stream.seek(0)
    stream_out = io.BytesIO()

    pdf_reader = PyPDF2.PdfFileReader(stream)
    pdf_writer = PyPDF2.PdfFileWriter()

    for pagenum in range(pdf_reader.numPages):
        page = pdf_reader.getPage(pagenum)
        page.rotateClockwise(degrees)
        pdf_writer.addPage(page)

    pdf_writer.write(stream_out)
    stream_out.seek(0)
    content = stream_out.read()
    return content

def reverse_pdf(pdf):
    """
    :params pdf: binary content

    """
    import PyPDF2
    stream = io.BytesIO()
    stream.write(pdf)
    stream.seek(0)
    stream_out = io.BytesIO()

    pdf_reader = PyPDF2.PdfFileReader(stream)
    pdf_writer = PyPDF2.PdfFileWriter()

    for pagenum in reversed(range(pdf_reader.numPages)):
        page = pdf_reader.getPage(pagenum)
        pdf_writer.addPage(page)

    pdf_writer.write(stream_out)
    stream_out.seek(0)
    content = stream_out.read()
    return content

def merge_pdfs(list_of_filecontents=[], filepaths=[], return_b64=False):

    to_unlink = []
    local_file_paths = filepaths and copy.deepcopy(list(filepaths)) or []

    if list_of_filecontents and not filepaths:
        for content in list_of_filecontents:
            filepath = tempfile.mktemp(suffix='.pdf')
            with open(filepath, 'wb') as f:
                f.write(content)
                f.flush()
            local_file_paths.append(filepath)
            to_unlink.append(filepath)
    try:
        outfile = tempfile.mktemp(suffix='.pdf')
        subprocess.check_call([
            'pdftk',
        ] + local_file_paths + [
            'cat',
            'output',
            outfile
        ])
        with open(outfile, 'rb') as f:
            res = f.read()
            if return_b64:
                res = base64.encodestring(res)
            return res
    finally:
        for x in to_unlink:
            os.unlink(x)

def stamp_pdfs(pdfs):
    """
    :params pdfs: iterable binary contents

    """
    from PyPDF2 import PdfFileReader, PdfFileWriter

    def get_pdf_page_count(pdf):
        return PdfFileReader(io.BytesIO(pdf), strict=False).getNumPages()

    def get_greatest_page_count(pdfs):
        return max([get_pdf_page_count(pdf) for pdf in pdfs])

    writer = PdfFileWriter()
    greatest_page_count = get_greatest_page_count(pdfs)
    first_pdf_reader = PdfFileReader(io.BytesIO(pdfs.pop(0)), strict=False)
    for page_index in range(0, greatest_page_count):
        for pdf in pdfs:
            pdf_reader = PdfFileReader(io.BytesIO(pdf), strict=False)
            pdf_page_count = pdf_reader.getNumPages()
            page = first_pdf_reader.getPage(page_index)
            if page_index < pdf_page_count:
                page_to_be_merged = pdf_reader.getPage(page_index)
                page_to_be_merged.scaleTo(int(page.mediaBox.getWidth()), int(page.mediaBox.getHeight()))
                page.mergePage(page_to_be_merged)
            writer.addPage(page)
    io_buffer = io.BytesIO()
    writer.write(io_buffer)
    merged_pdf = io_buffer.getvalue()
    io_buffer.close()
    return merged_pdf
