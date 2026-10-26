"""Fill the Charité "Time recording for EU projects" workbook by writing values straight into its sheet XML, which keeps the logo, conditional formatting, dropdowns and macros intact (openpyxl would drop them)."""
import html
import io
import re
import zipfile
from xml.sax.saxutils import escape

from openpyxl.utils import get_column_letter

from odoo.exceptions import UserError

SHEET_XML = 'xl/worksheets/sheet3.xml'  # "3. Time Sheet"
SHARED_STRINGS = 'xl/sharedStrings.xml'
CALC_CHAIN = 'xl/calcChain.xml'
UPLOAD_HINT = 'Upload the Charité "Time recording for EU projects" workbook as the EU timesheet template.'
MONTH_LABELS = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July',
    8: 'August ', 9: 'September', 10: 'October', 11: 'November ', 12: 'December',
}  # must equal the template's month dropdown, trailing spaces included
WP_ROWS = range(19, 26)
SICK_ROW, VACATION_ROW, SPECIAL_ROW = 26, 27, 28


def day_column(day):
    """Column letters of a day of the month: day 1 is column C."""
    return get_column_letter(day + 2)


def _open(template):
    """The ``template`` workbook as a zip, or a UserError when it is not a workbook with the time sheet."""
    try:
        workbook = zipfile.ZipFile(io.BytesIO(template))
    except zipfile.BadZipFile as error:
        raise UserError(UPLOAD_HINT) from error
    if not {SHEET_XML, SHARED_STRINGS} <= set(workbook.namelist()):
        raise UserError(UPLOAD_HINT)
    return workbook


def acronyms(template):
    """Every shared string of the workbook, which includes each grant acronym the J11 dropdown offers."""
    with _open(template) as z:
        return {html.unescape(t) for t in re.findall(r'<t[^>]*>([^<]*)</t>', z.read(SHARED_STRINGS).decode())}


def fill(template, cells):
    """Return a copy of the ``template`` workbook with ``cells`` (e.g. ``{'J7': 'Name', 'C19': 7.5}``) written into its time sheet, each keeping its cell style.

    Cached formula results and the calculation chain are dropped and a full recalculation on load is requested, so Excel and LibreOffice recompute dates, weekdays, sums and the grant-agreement lookup.
    """
    src = _open(template)
    data = {info.filename: src.read(info) for info in src.infolist()}
    pending = dict(cells)

    def write(match):
        ref, attrs = match.group(1), match.group(2)
        if ref not in pending:
            return match.group(0)
        value = pending.pop(ref)
        style = re.search(r'\bs="\d+"', attrs)
        attrs = f' {style.group(0)}' if style else ''
        if isinstance(value, str):
            return f'<c r="{ref}"{attrs} t="inlineStr"><is><t xml:space="preserve">{escape(value)}</t></is></c>'
        return f'<c r="{ref}"{attrs}><v>{value:g}</v></c>'

    sheet = re.sub(r'<c r="([A-Z]+\d+)"([^>]*?)(?:/>|>.*?</c>)', write, data[SHEET_XML].decode(), flags=re.S)
    if pending:
        raise UserError(f'The EU timesheet template has no cell {", ".join(pending)}. {UPLOAD_HINT}')
    data[SHEET_XML] = re.sub(r'(<f(?:\s[^>]*)?(?:/>|>[^<]*</f>))<v>[^<]*</v>', r'\1', sheet).encode()
    workbook = re.sub(r'\sfullCalcOnLoad="[^"]*"', '', data['xl/workbook.xml'].decode())
    data['xl/workbook.xml'] = re.sub(r'<calcPr\b', '<calcPr fullCalcOnLoad="1"', workbook, count=1).encode()
    for name, pattern in (('[Content_Types].xml', r'<Override PartName="/xl/calcChain\.xml"[^>]*/>'), ('xl/_rels/workbook.xml.rels', r'<Relationship [^>]*Target="calcChain\.xml"[^>]*/>')):
        data[name] = re.sub(pattern, '', data[name].decode()).encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for info in src.infolist():
            if info.filename != CALC_CHAIN:
                z.writestr(info, data[info.filename])
    return out.getvalue()
