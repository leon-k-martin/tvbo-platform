"""Fill the Charité "Time recording for EU projects" workbook by writing values straight into its sheet XML, which keeps the logo, conditional formatting, dropdowns and macros intact (openpyxl would drop them)."""
import html
import io
import re
import zipfile
from xml.sax.saxutils import escape

from odoo.exceptions import UserError

SHEET_XML = 'xl/worksheets/sheet3.xml'  # "3. Time Sheet"
CALC_CHAIN = 'xl/calcChain.xml'
MONTH_LABELS = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July',
    8: 'August ', 9: 'September', 10: 'October', 11: 'November ', 12: 'December',
}  # must equal the template's month dropdown, trailing spaces included
WP_ROWS = range(19, 26)
SICK_ROW, VACATION_ROW, SPECIAL_ROW = 26, 27, 28


def day_column(day):
    """Column letters of a day of the month: day 1 is column C."""
    n, letters = day + 2, ''
    while n:
        n, rest = divmod(n - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def acronyms(template):
    """Every shared string of the workbook, which includes each grant acronym the J11 dropdown offers."""
    with zipfile.ZipFile(io.BytesIO(template)) as z:
        return {html.unescape(t) for t in re.findall(r'<t[^>]*>([^<]*)</t>', z.read('xl/sharedStrings.xml').decode())}


def _set_cell(sheet, ref, value):
    """Replace the value of an existing styled cell, keeping its style."""
    match = re.search(r'<c r="%s"([^>]*?)(?:/>|>.*?</c>)' % ref, sheet, re.S)
    if not match:
        raise UserError(f'The EU timesheet template has no cell {ref}; upload the Charité "Time recording for EU projects" workbook.')
    style = re.search(r'\bs="\d+"', match.group(1))
    attrs = f' {style.group(0)}' if style else ''
    if isinstance(value, str):
        cell = f'<c r="{ref}"{attrs} t="inlineStr"><is><t xml:space="preserve">{escape(value)}</t></is></c>'
    else:
        cell = f'<c r="{ref}"{attrs}><v>{value:g}</v></c>'
    return sheet[:match.start()] + cell + sheet[match.end():]


def fill(template, cells):
    """Return a copy of the ``template`` workbook with ``cells`` (e.g. ``{'J7': 'Name', 'C19': 7.5}``) written into its time sheet.

    Cached formula results and the calculation chain are dropped and a full recalculation on load is requested, so Excel and LibreOffice recompute dates, weekdays, sums and the grant-agreement lookup.
    """
    src = zipfile.ZipFile(io.BytesIO(template))
    data = {info.filename: src.read(info) for info in src.infolist()}
    sheet = data[SHEET_XML].decode()
    for ref, value in cells.items():
        sheet = _set_cell(sheet, ref, value)
    data[SHEET_XML] = re.sub(r'(<f[^>]*>.*?</f>|<f[^>]*/>)<v>.*?</v>', r'\1', sheet, flags=re.S).encode()
    workbook = data['xl/workbook.xml'].decode()
    if 'fullCalcOnLoad' not in workbook:
        data['xl/workbook.xml'] = workbook.replace('<calcPr ', '<calcPr fullCalcOnLoad="1" ', 1).encode()
    for name, pattern in (('[Content_Types].xml', r'<Override PartName="/xl/calcChain\.xml"[^>]*/>'), ('xl/_rels/workbook.xml.rels', r'<Relationship [^>]*Target="calcChain\.xml"[^>]*/>')):
        data[name] = re.sub(pattern, '', data[name].decode()).encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for info in src.infolist():
            if info.filename != CALC_CHAIN:
                z.writestr(info, data[info.filename])
    return out.getvalue()
