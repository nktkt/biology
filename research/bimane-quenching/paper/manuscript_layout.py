"""Word layout and result-table access shared by the two manuscript editions."""
import csv
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Inches, Mm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def data(name):
    with (RESULTS / name).open(newline="") as stream:
        return list(csv.DictReader(stream))

def text_style(style, latin, east_asian, size, bold, ink, language):
    font = style.font
    font.name, font.size, font.bold = latin, Pt(size), bold
    font.color.rgb = RGBColor.from_string(ink)
    properties = style.element.get_or_add_rPr()
    names = properties.find(qn("w:rFonts"))
    names.set(qn("w:eastAsia"), east_asian)
    for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme"):
        names.attrib.pop(qn("w:" + key), None)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), language)
    lang.set(qn("w:eastAsia"), language)
    properties.append(lang)

def spacing(style, before, after, leading):
    fmt = style.paragraph_format
    fmt.space_before, fmt.space_after, fmt.line_spacing = Pt(before), Pt(after), Pt(leading)
    fmt.widow_control = True

def settings(doc, *, language, title, subject):
    japanese = language == "ja"
    lang = "ja-JP" if japanese else "en-US"
    serif, sans = "Times New Roman", "Arial"
    text_face, heading_face = ("Hiragino Mincho ProN", "Hiragino Sans") if japanese else (serif, sans)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin, sec.right_margin = Mm(22), Mm(22)
    sec.top_margin, sec.bottom_margin, sec.footer_distance = Mm(19.5), Mm(18), Mm(8)
    normal = doc.styles["Normal"]
    text_style(normal, serif, text_face, 11.0 if japanese else 11.5, False, "192C31", lang)
    spacing(normal, 0, 5, 17 if japanese else 15.7)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for name, size, before, after, line in (("Title",23,0,3,31), ("Heading 1",16,0,8,23), ("Heading 2",12,8,3,17)):
        style = doc.styles[name]
        text_style(style,sans,heading_face,size,True,"131C20",lang)
        spacing(style,before,after,line)
        style.paragraph_format.keep_with_next = True
        props = style.element.get_or_add_pPr()
        for border in list(props.findall(qn("w:pBdr"))):
            props.remove(border)
    for name, size, before, after, line, bold, ink in (
        ("Sub",12.2,0,4,19,False,"2F484C"), ("Meta",9,0,12,14,False,"465C60"),
        ("Caption note",9.3,4,5,14,False,"354749"), ("T caption",10.2,6,4,14,True,"1C353B"),
        ("Table body",9.3,0,0,14,False,"253A42"), ("Table header",9.1,0,0,13.5,True,"253A42"),
        ("Reference entry",9.3,0,5,14,False,"20383C"), ("Front heading",12.2,7,3,18,True,"253A42"),
    ):
        style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        text_style(style,sans,heading_face,size,bold,ink,lang)
        spacing(style,before,after,line)
        if name in ("T caption","Front heading"):
            style.paragraph_format.keep_with_next = True
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    page = OxmlElement("w:fldSimple")
    page.set(qn("w:instr"), "PAGE")
    footer._p.append(page)
    metadata=doc.core_properties
    metadata.title, metadata.subject, metadata.language = title, subject, lang
    metadata.author = "Biology Research Collection"
    metadata.comments = "Secondary analysis of published data. Study version 1.0."
    metadata.created = metadata.modified = datetime(2026, 11, 25, tzinfo=timezone.utc)
    metadata.last_modified_by = metadata.author

def outline(table):
    props = table._tbl.tblPr
    lines = OxmlElement("w:tblBorders")
    for side in ("top","bottom","insideH","left","right","insideV"):
        item=OxmlElement("w:"+side)
        item.set(qn("w:val"), "single" if side in ("top","bottom","insideH") else "nil")
        item.set(qn("w:sz"), "4" if side=="insideH" else "6")
        item.set(qn("w:color"), "D6DFDF")
        lines.append(item)
    props.append(lines)
    margins=OxmlElement("w:tblCellMar")
    for side, width in (("left",75),("right",75),("top",32),("bottom",32)):
        item=OxmlElement("w:"+side)
        item.set(qn("w:w"),str(width)); item.set(qn("w:type"),"dxa")
        margins.append(item)
    props.append(margins)

def table(doc, heads, rows, fracs, left_cols=(0,)):
    result=doc.add_table(rows=len(rows)+1,cols=len(heads))
    result.autofit=False
    result.alignment=WD_TABLE_ALIGNMENT.CENTER
    sec=doc.sections[0]
    width=sec.page_width-sec.left_margin-sec.right_margin
    for col, frac in zip(result.columns,fracs,strict=True):
        col.width=int(frac*width)
    for i, values in enumerate([heads,*rows]):
        props=result.rows[i]._tr.get_or_add_trPr()
        props.append(OxmlElement("w:cantSplit"))
        if i==0:
            props.append(OxmlElement("w:tblHeader"))
        for j,value in enumerate(values):
            cell=result.cell(i,j)
            cell.width=int(width*fracs[j])
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph=cell.paragraphs[0]
            paragraph.style="Table header" if i==0 else "Table body"
            paragraph.alignment=WD_ALIGN_PARAGRAPH.LEFT if j in left_cols else WD_ALIGN_PARAGRAPH.RIGHT
            paragraph.add_run(str(value))
            if i==0:
                shade=OxmlElement("w:shd"); shade.set(qn("w:fill"),"E9EFEF")
                cell._tc.get_or_add_tcPr().append(shade)
    outline(result)
    return result

def reference(doc, number, text, label, url):
    p=doc.add_paragraph(style="Reference entry")
    p.add_run(f"[{number}]  {text} ")
    tag=OxmlElement("w:hyperlink")
    tag.set(qn("r:id"),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
    run=OxmlElement("w:r"); props=OxmlElement("w:rPr"); color=OxmlElement("w:color")
    color.set(qn("w:val"),"27645F"); props.append(color); run.append(props)
    txt=OxmlElement("w:t"); txt.text=label; run.append(txt); tag.append(run); p._p.append(tag)

def save_document(doc, destination):
    """Give identical Word package contents identical ZIP timestamps."""
    raw = BytesIO()
    doc.save(raw)
    normalized = BytesIO()
    with ZipFile(raw) as source, ZipFile(normalized, "w") as output:
        for entry in source.infolist():
            payload = source.read(entry)
            entry.date_time = (2026, 11, 25, 0, 0, 0)
            output.writestr(entry, payload)
    destination.write_bytes(normalized.getvalue())
