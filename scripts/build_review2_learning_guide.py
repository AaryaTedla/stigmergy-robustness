"""Build the 12-page Review 2 implementation learning PDF from its Markdown source.

Purpose: give all four teammates a readable simulator-to-PPO-to-corpus walkthrough
without recreating experiments or inventing screenshots. The source is
``docs/REVIEW2_IMPLEMENTATION_GUIDE.md``; explicit PAGE separators define twelve
chapters. Inputs are that Markdown and optional committed source-revision labels.
Output is a searchable, numbered PDF with bookmarks, internal contents links,
wrapped code, readable tables and vector process diagrams. All dimensions use
PDF points. The builder measures every block and fails rather than clipping it.

Requires reportlab (document-generation tooling, not a simulator dependency).
Run from the repository root:
``python scripts/build_review2_learning_guide.py --phase2a-revision 0ec8349``.
By default the Phase 2B source revision is the current Git HEAD. This is a
learning document: recorded historical metrics remain distinct from fresh audit
checks, and no model training, policy change, or data collection is performed.
"""

import argparse
from html import escape
from pathlib import Path
import re
import subprocess
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, Paragraph, Preformatted, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
INK = colors.HexColor('#14242c')
TEAL = colors.HexColor('#168f96')
ORANGE = colors.HexColor('#bb5a28')


class ProcessDiagram(Flowable):
    """Draw an accessible-text vector diagram for either PPO or the data boundary."""
    def __init__(self, kind, width):
        Flowable.__init__(self)
        self.kind, self.width, self.height = kind, width, 107

    def draw(self):
        """Render labelled current/future boxes without images or model claims."""
        c = self.canv
        labels = ([('Simulator', 'local observation'), ('Shared PPO', 'same weights per agent'),
                   ('World transition', 'next view + reward')] if self.kind == 'PPO' else
                  [('Matched JSONL', 'clean / disabled / attacked'), ('Separated corpus', 'local tree | audit tree'),
                   ('Agent-step CSV', '70 candidate local inputs')])
        gap, width, y = 17, (self.width - 34) / 3, 43
        for index, (title, subtitle) in enumerate(labels):
            x = index * (width + gap)
            c.setFillColor(colors.HexColor('#edf7f7')); c.setStrokeColor(TEAL)
            c.roundRect(x, y, width, 52, 5, stroke=1, fill=1)
            c.setFillColor(INK); c.setFont('GuideBold', 10.1)
            c.drawCentredString(x + width / 2, y + 32, title)
            c.setFont('Guide', 8.2); c.drawCentredString(x + width / 2, y + 15, subtitle)
            if index < 2:
                c.setStrokeColor(TEAL); c.line(x + width + 2, y + 26, x + width + gap - 2, y + 26)
                end = x + width + gap - 2
                c.line(end - 4, y + 29, end, y + 26); c.line(end - 4, y + 23, end, y + 26)
        c.setFillColor(INK); c.setFont('Guide', 9)
        note = ('Rollout collection -> advantage/value estimates -> PPO updates -> checkpoint' if self.kind == 'PPO'
                else 'Audit only -> future validated labels; grouped splits -> windows -> detector (planned)')
        c.drawString(0, 18, note)


def rich(text):
    """Escape source prose, then format inline code without introducing executable markup."""
    parts = re.split(r'(`[^`]+`)', text)
    return ''.join('<font name="GuideMono">' + escape(part[1:-1]) + '</font>'
                   if part.startswith('`') and part.endswith('`') else escape(part)
                   for part in parts)


def styles(scale=1.0):
    """Create consistent readable paragraph/code/table styles, in PDF points."""
    return {
        'body': ParagraphStyle('body', fontName='Guide', fontSize=10.15 * scale,
                               leading=14.05 * scale, textColor=INK, spaceAfter=6),
        'h2': ParagraphStyle('h2', fontName='GuideBold', fontSize=13.1 * scale,
                             leading=16.4 * scale, spaceBefore=8, spaceAfter=7, textColor=TEAL),
        'source': ParagraphStyle('source', fontName='Guide', fontSize=8.1,
                                 leading=10.8, textColor=colors.HexColor('#54656c'), spaceBefore=5),
        'table': ParagraphStyle('table', fontName='Guide', fontSize=9.0 * scale,
                                leading=12.05 * scale, textColor=INK),
        'head': ParagraphStyle('head', fontName='GuideBold', fontSize=9.0 * scale,
                               leading=12.05 * scale, textColor=colors.white),
        'code': ParagraphStyle('code', fontName='GuideMono', fontSize=8.0 * scale,
                               leading=11.1 * scale, backColor=colors.HexColor('#f1f4f5'),
                               borderPadding=6, spaceBefore=5, spaceAfter=9),
    }


def chapter_blocks(source, width, scale=1.0):
    """Convert the supported Markdown subset into measured native PDF flowables."""
    st = styles(scale)
    lines, blocks, i = source.splitlines(), [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('# '):
            i += 1; continue
        if line.startswith('## '):
            blocks.append(Paragraph(rich(line[3:]), st['h2'])); i += 1; continue
        if line.startswith('[FLOW:'):
            blocks.append(ProcessDiagram(line[6:-1], width)); i += 1; continue
        if line.startswith('```'):
            code = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                raw = lines[i]
                if len(raw) > 101:
                    wrapped = textwrap.wrap(raw, width=99, break_long_words=False, break_on_hyphens=False,
                                            subsequent_indent='  ')
                    code.extend(part + (' \\' if n < len(wrapped) - 1 else '')
                                for n, part in enumerate(wrapped))
                else: code.append(raw)
                i += 1
            blocks.append(Preformatted('\n'.join(code), st['code'])); i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [cell.strip() for cell in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', cell) for cell in cells): rows.append(cells)
                i += 1
            columns = len(rows[0])
            if rows[0][:2] == ['Column family', 'Count']: widths = [width * .29, width * .10, width * .61]
            elif columns == 2: widths = [width * .29, width * .71]
            elif columns == 3: widths = [width * .25, width * .35, width * .40]
            elif columns == 4: widths = [width * .36, width * .22, width * .17, width * .25]
            else: widths = [width * .15] + [width * .85 / (columns - 1)] * (columns - 1)
            cells = [[Paragraph(rich(cell), st['head' if r == 0 else 'table'])
                      for cell in row] for r, row in enumerate(rows)]
            table = Table(cells, colWidths=widths, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), TEAL),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f7'), colors.white]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, -1), (-1, -1), .4, colors.HexColor('#c7dada')),
            ]))
            blocks.extend([table, Spacer(1, 7)]); continue
        if line.startswith('- '):
            blocks.append(Paragraph('&#8226; ' + rich(line[2:]), st['body'])); i += 1; continue
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '```', '[FLOW:', '- ')):
            paragraph.append(lines[i].strip()); i += 1
        text = ' '.join(paragraph)
        if text.startswith('Pages 2-4:'):
            text = 'Contents: ' + ' | '.join(f'<link href="#chapter{n}" color="#168f96">{label}</link>'
                for n, label in [(2, '2 Grid'), (3, '3 Local view'), (4, '4 PPO'), (5, '5 Clean gate'),
                                 (6, '6 Limits'), (7, '7 Attacks'), (8, '8 Logs'), (9, '9 Corpus/CSV'),
                                 (10, '10 Files'), (11, '11 Commands'), (12, '12 Review answers')])
            blocks.append(Paragraph(text, st['body']))
        else:
            blocks.append(Paragraph(rich(text), st['source' if text.startswith('Sources:') else 'body']))
    return blocks


def build(output, phase2a_revision, phase2b_revision):
    """Render twelve measured chapters and fail if any block exceeds its page frame."""
    fontdir = Path('/usr/share/fonts/truetype/dejavu')
    for name, file in [('Guide', 'DejaVuSans.ttf'), ('GuideBold', 'DejaVuSans-Bold.ttf'),
                       ('GuideMono', 'DejaVuSansMono.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fontdir / file)))
    sections = (ROOT / 'docs/REVIEW2_IMPLEMENTATION_GUIDE.md').read_text().split('\n---PAGE---\n')
    if len(sections) != 12: raise ValueError('The guide must contain exactly twelve chapters')
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=A4)
    c.setTitle('Review 2 - Implementation Learning Guide')
    c.setAuthor('Robust Stigmergic Coordination capstone team')
    c.setSubject(f'Source phase2a {phase2a_revision}; phase-2b {phase2b_revision}; historical outcomes not rerun')
    page_width, page_height = A4
    left, width, bottom, top = 40, page_width - 80, 53, page_height - 96
    measurements = []
    for number, section in enumerate(sections, 1):
        title = next(line[2:] for line in section.splitlines() if line.startswith('# '))
        c.bookmarkPage(f'chapter{number}'); c.addOutlineEntry(title, f'chapter{number}', level=0)
        c.setFillColor(TEAL); c.rect(left, page_height - 35, 24, 3, fill=1, stroke=0)
        c.setFont('Guide', 8.5); c.setFillColor(INK)
        c.drawString(left + 31, page_height - 34, 'ROBUST STIGMERGIC COORDINATION  /  REVIEW 2')
        if pdfmetrics.stringWidth(title, 'GuideBold', 19.5) > width:
            raise ValueError(f'Chapter {number} title is too wide; shorten it')
        c.setFont('GuideBold', 19.5); c.drawString(left, page_height - 69, title)
        c.setStrokeColor(TEAL); c.setLineWidth(1.2); c.line(left, page_height - 80, page_width - left, page_height - 80)
        blocks = chapter_blocks(section, width)
        measured = sum(block.wrap(width, 1000)[1] + block.getSpaceBefore() + block.getSpaceAfter()
                       for block in blocks)
        if measured > top - bottom:
            # A small, bounded adjustment is allowed; readability is not sacrificed to fit.
            blocks = chapter_blocks(section, width, .965)
            measured = sum(block.wrap(width, 1000)[1] + block.getSpaceBefore() + block.getSpaceAfter()
                           for block in blocks)
        if measured > top - bottom:
            raise ValueError(f'Chapter {number} overflows by {measured - (top - bottom):.1f} points; shorten prose')
        y = top
        for block in blocks:
            y -= block.getSpaceBefore()
            _, height = block.wrap(width, y - bottom)
            y -= height
            if y < bottom: raise ValueError(f'Clipped content on page {number}')
            block.drawOn(c, left, y)
            y -= block.getSpaceAfter()
        measurements.append({'page': number, 'content_height': round(measured, 1), 'bottom': round(y, 1)})
        c.setStrokeColor(colors.HexColor('#dce5e7')); c.line(left, 41, page_width - left, 41)
        c.setFillColor(colors.HexColor('#57676e')); c.setFont('Guide', 7.2)
        c.drawString(left, 28, f'5 Nov 2026 | code: 2A {phase2a_revision[:7]} / 2B {phase2b_revision[:7]} | recorded outcomes distinguished')
        c.drawRightString(page_width - left, 15, f'{number} / 12')
        c.showPage()
    c.save()
    return measurements


def main():
    """Parse output/source labels; obtain a committed code revision for the PDF metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/pdf/review2_implementation_learning_guide.pdf')
    parser.add_argument('--phase2a-revision', default='0ec8349')
    parser.add_argument('--phase2b-revision', default=None)
    args = parser.parse_args()
    revision = args.phase2b_revision or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    print(build(args.output, args.phase2a_revision, revision))


if __name__ == '__main__':
    main()
