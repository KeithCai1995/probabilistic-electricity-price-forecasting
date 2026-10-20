"""Optional PDF rendering of report/report_v110.md; requires reportlab.

This renders existing evidence only. It never runs or fabricates experiments.
"""
from pathlib import Path
from html import escape
import re
import argparse
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak, Image, KeepTogether, Spacer


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=root/'report/report_v110.md')
    parser.add_argument('--output', type=Path, default=root/'report/Corrected_Technical_Report_v110.pdf')
    args = parser.parse_args()
    fonts = Path(reportlab.__file__).parent/'fonts'
    pdfmetrics.registerFont(TTFont('Portfolio', str(fonts/'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('PortfolioBold', str(fonts/'VeraBd.ttf')))
    pdfmetrics.registerFontFamily('Portfolio', normal='Portfolio', bold='PortfolioBold', italic='Portfolio', boldItalic='PortfolioBold')
    styles = {name: ParagraphStyle(name, fontName='PortfolioBold' if name in ('title','h','sub','head') else 'Portfolio',
               fontSize=size, leading=leading, spaceAfter=7, keepWithNext=name in ('title','h','sub'))
              for name,size,leading in [('body',9.7,13.2),('title',20,25),('h',13,18),('sub',10.8,15),('cell',8,11),('head',8,11),('cap',8.5,11.5)]}
    def fmt(text):
        text = escape(text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))
        text = re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
        text = re.sub(r'`([^`]+)`',r'\1',text)
        return re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',lambda m: '<link href="'+m[2]+'" color="#204968">'+m[1]+'</link>',text)
    lines = args.source.read_text(encoding='utf-8').splitlines(); story=[]; i=0
    while i < len(lines):
        text=lines[i].strip()
        if not text: i+=1; continue
        if text=='<!-- PAGE -->': story.append(PageBreak()); i+=1; continue
        if text.startswith('<!--'): i+=1; continue
        if text.startswith('!['):
            match=re.fullmatch(r'!\[([^\]]*)\]\((.+)\)',text)
            image=Image(str((args.source.parent/match[2]).resolve()))
            scale=min(504/image.imageWidth,190/image.imageHeight)
            image.drawWidth*=scale; image.drawHeight*=scale
            story.append(KeepTogether([image,Paragraph(fmt(match[1]),styles['cap'])])); i+=1; continue
        if text.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',c) for c in row): rows.append(row)
                i+=1
            n=len(rows[0]); weights=[1.8]+[1]*(n-1)
            table=Table([[Paragraph(fmt(c),styles['head' if j==0 else 'cell']) for c in r] for j,r in enumerate(rows)],
                        colWidths=[504*w/sum(weights) for w in weights],repeatRows=1)
            table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),
               ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9EDF0')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            story.extend([table,Spacer(1,8)]); continue
        if text.startswith('```'):
            i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):
                story.append(Paragraph(fmt(lines[i]),styles['cap']));i+=1
            i+=1;continue
        key='body'
        if text.startswith('# '): text,key=text[2:],'title'
        elif text.startswith('## '): text,key=text[3:],'h'
        elif text.startswith('### '): text,key=text[4:],'sub'
        if key=='body':
            while i+1<len(lines):
                nxt=lines[i+1].strip()
                if not nxt or nxt.startswith(('#','|','![','```','<!--','- ')) or re.match(r'\d+\. ',nxt): break
                text+=' '+nxt;i+=1
        story.append(Paragraph(fmt(text),styles[key]));i+=1
    def footer(canvas,doc):
        canvas.setFont('Portfolio',7.5)
        canvas.drawString(54,27,'18 October 2026 | Corrected technical report | Local v1.1.0')
        canvas.drawRightString(558,27,str(doc.page))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(args.output),pagesize=letter,leftMargin=54,rightMargin=54,topMargin=42,bottomMargin=44,
       author='Haorui Cai',title='Corrected technical portfolio v1.1.0').build(story,onFirstPage=footer,onLaterPages=footer)
    print(args.output)


if __name__=='__main__': main()
