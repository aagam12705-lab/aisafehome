from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = Path('/Users/aagamjain/Desktop/ai-safehome/output/documents/SafeHome_AI_Recording_Plan_and_Script.docx')
OUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = '203247'
TEAL = '1E5D78'
PALE = 'E3EEF1'
GRID = 'D9D9D9'
ALT = 'F5F7F8'
GRAY = RGBColor(89, 103, 122)

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)

def borders(table, color=GRID):
    tblPr = table._tbl.tblPr
    el = tblPr.find(qn('w:tblBorders'))
    if el is None:
        el = OxmlElement('w:tblBorders')
        tblPr.append(el)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        tag = OxmlElement(f'w:{edge}')
        tag.set(qn('w:val'), 'single')
        tag.set(qn('w:sz'), '4')
        tag.set(qn('w:color'), color)
        el.append(tag)

def set_cell_margins(cell, top=100, start=120, bottom=100, end=120):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        node = tcMar.find(qn(f'w:{m}'))
        if node is None:
            node = OxmlElement(f'w:{m}')
            tcMar.append(node)
        node.set(qn('w:w'), str(v)); node.set(qn('w:type'), 'dxa')

def set_repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    tblHeader.set(qn('w:val'), 'true')
    trPr.append(tblHeader)

def add_heading(doc, text, level=1):
    p = doc.add_paragraph(text, style=f'Heading {level}')
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(5)
    return p

def add_bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(text)
    p.paragraph_format.space_after = Pt(3)
    return p

def add_number(doc, text):
    p = doc.add_paragraph(style='List Number')
    p.add_run(text)
    p.paragraph_format.space_after = Pt(3)
    return p

doc = Document()
sec = doc.sections[0]
sec.page_width = Inches(8.5); sec.page_height = Inches(11)
sec.top_margin = Inches(0.65); sec.bottom_margin = Inches(0.65)
sec.left_margin = Inches(0.72); sec.right_margin = Inches(0.72)

styles = doc.styles
styles['Normal'].font.name = 'Aptos'; styles['Normal'].font.size = Pt(10.5); styles['Normal'].font.color.rgb = RGBColor(44,62,80)
styles['Normal'].paragraph_format.space_after = Pt(6)
styles['Title'].font.name = 'Aptos Display'; styles['Title'].font.size = Pt(28); styles['Title'].font.bold = True; styles['Title'].font.color.rgb = RGBColor(0,0,0)
styles['Subtitle'].font.name = 'Aptos'; styles['Subtitle'].font.size = Pt(13); styles['Subtitle'].font.color.rgb = GRAY
for name, size in [('Heading 1',18),('Heading 2',13)]:
    styles[name].font.name = 'Aptos Display'; styles[name].font.size = Pt(size); styles[name].font.bold = True; styles[name].font.color.rgb = RGBColor(0,0,0)

p = doc.add_paragraph(style='Title'); p.add_run('SafeHome AI Recording Plan and Script')
p = doc.add_paragraph(style='Subtitle'); p.add_run('Three minute Congressional App Challenge video')
p = doc.add_paragraph()
p.add_run('Purpose  ').bold = True
p.add_run('This document gives the exact order, timing, narration, and screen actions for recording the final video. Six presentation slides explain the project and four app clips demonstrate it. The app is on screen for 110 of the 180 seconds.')

add_heading(doc, 'Final video structure', 1)
table = doc.add_table(rows=1, cols=4)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False
widths = [Inches(1.05), Inches(1.05), Inches(1.45), Inches(3.55)]
hdr = table.rows[0].cells
for i, text in enumerate(['Time','Media','Length','Purpose']):
    hdr[i].width = widths[i]; hdr[i].text = text; shade(hdr[i], TEAL); set_cell_margins(hdr[i])
    for r in hdr[i].paragraphs[0].runs: r.font.bold=True; r.font.color.rgb=RGBColor(255,255,255)
set_repeat_header(table.rows[0])
rows = [
('0:00-0:08','Slide 1','8 sec','Introduce the problem and SafeHome AI.'),
('0:08-0:33','Clip A','25 sec','Start a Quick Safety Check and upload a photo.'),
('0:33-0:45','Slide 2','12 sec','Explain Quick Check and saved Account Check.'),
('0:45-1:20','Clip B','35 sec','Show hazards, follow-up questions, and the score.'),
('1:20-1:32','Slide 3','12 sec','Explain the full processing and backend flow.'),
('1:32-1:57','Clip C','25 sec','Show the safety plan and comparison after fixes.'),
('1:57-2:09','Slide 4','12 sec','Explain how the bounded score is calculated.'),
('2:09-2:21','Slide 5','12 sec','Present the testing results.'),
('2:21-2:46','Clip D','25 sec','Show saved progress, email, and accessibility.'),
('2:46-3:00','Slide 6','14 sec','Explain the reliability and accessibility decisions.'),
]
for ridx, row in enumerate(rows, start=1):
    cells = table.add_row().cells
    for i, text in enumerate(row):
        cells[i].width = widths[i]; cells[i].text = text; cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade(cells[i], ALT if ridx % 2 == 0 else 'FFFFFF'); set_cell_margins(cells[i])
        if i < 3: cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
borders(table)

doc.add_page_break()
add_heading(doc, 'Exact clip recording instructions', 1)

add_heading(doc, 'Preparation before every clip', 2)
add_bullet(doc, 'Record at 1920 by 1080 and 60 frames per second with the browser at 100 percent zoom.')
add_bullet(doc, 'Use light mode, the same staged bedroom photo, and the same browser size throughout.')
add_bullet(doc, 'Hide bookmarks, notifications, unrelated tabs, and personal email addresses.')
add_bullet(doc, 'Record the app silently and add narration afterward.')
add_bullet(doc, 'Leave one second still at the beginning and end of every clip.')
add_bullet(doc, 'Record each clip twice and retain the smoother take.')

add_heading(doc, 'Clip A  0 08 to 0 33  25 seconds', 2)
add_number(doc, 'Begin on the landing page and hold still for one second.')
add_number(doc, 'Click Quick Safety Check.')
add_number(doc, 'Choose Bedroom as the room type.')
add_number(doc, 'Click Continue.')
add_number(doc, 'Upload the staged bedroom photo.')
add_number(doc, 'Pause on the photo preview.')
add_number(doc, 'Show the photo quality results.')
add_number(doc, 'Click Analyze Photo.')
add_number(doc, 'End when the loading or analysis screen appears and hold still for one second.')
p = doc.add_paragraph(); p.add_run('Narration  ').bold = True; p.add_run('A first check does not require an account. The user chooses a room, uploads one photo, and the app checks image quality before analysis.')

add_heading(doc, 'Clip B  0 45 to 1 20  35 seconds', 2)
add_number(doc, 'Prepare the app so the recording begins on the AI results page.')
add_number(doc, 'Hold the marked room image for about three seconds so the numbered blue markers are visible.')
add_number(doc, 'Scroll slowly to the first hazard card and pause on its evidence, explanation, and recommendation.')
add_number(doc, 'Scroll to a second hazard card and pause again.')
add_number(doc, 'Continue to the follow up questions.')
add_number(doc, 'Answer two questions using Yes, No, Not sure, or Not applicable.')
add_number(doc, 'Continue until the room score appears.')
add_number(doc, 'Pause on the numerical score and colored risk bar for about three seconds.')
p = doc.add_paragraph(); p.add_run('Narration  ').bold = True; p.add_run('Numbered markers connect visible evidence to plain language explanations. The app asks about important details a photo cannot prove. Those answers combine with the visible hazards to produce a bounded room score.')

add_heading(doc, 'Clip C  1 32 to 1 57  25 seconds', 2)
add_number(doc, 'Begin on the final result or safety plan page.')
add_number(doc, 'Show the three priority actions and scroll slowly enough to keep each one readable.')
add_number(doc, 'Click Compare After Making Fixes.')
add_number(doc, 'Upload or select the prepared second room photo and continue through the recheck.')
add_number(doc, 'Show the before and after result.')
add_number(doc, 'Pause on Resolved, Still Present, and New.')
add_number(doc, 'Include the score change if it is visible, then end with the comparison still on screen.')
p = doc.add_paragraph(); p.add_run('Narration  ').bold = True; p.add_run('The result becomes a short action plan. A later photo shows which hazard categories were resolved, which remain, and whether anything new appeared.')

add_heading(doc, 'Clip D  2 21 to 2 46  25 seconds', 2)
add_number(doc, 'Use a signed in demo account with existing saved checks.')
add_number(doc, 'Open Room by Room Stats and pause on the unique rooms checked number.')
add_number(doc, 'Scroll to the room score trend and pause on the graph and labeled values.')
add_number(doc, 'Show the before and after comparison briefly.')
add_number(doc, 'Open an Email this summary section and click Add new email address.')
add_number(doc, 'Enter a demo address such as family@example.com. Do not send the email.')
add_number(doc, 'Open Accessibility and change one visible setting such as text size or color mode.')
add_number(doc, 'If time permits, toggle Read Aloud or Reduced Motion.')
add_number(doc, 'End with the accessibility panel visible.')
p = doc.add_paragraph(); p.add_run('Narration  ').bold = True; p.add_run('Saved checks track progress by room. The dashboard shows trends and comparisons, summaries can go to trusted people, and accessibility controls remain available throughout the app.')

doc.add_page_break()
add_heading(doc, 'Complete narration and screen directions', 1)

segments = [
('0:00-0:08  Slide 1',
 'I built SafeHome AI to help older adults and families find room hazards before those hazards become accidents.',
 'Hold the opening slide. Do not animate individual words.'),
('0:08-0:33  Clip A',
 'A first check does not require an account. The user chooses a room, uploads one photo, and the app checks image quality before analysis.',
 'Begin on the landing page. Click Quick Safety Check, choose Bedroom, continue, upload the staged room photo, pause on the preview and photo-quality result, then click Analyze. Keep the cursor slow and visible.'),
('0:33-0:45  Slide 2',
 'Quick Check removes setup from the first experience. An account uses the same analysis, then adds Room Names, history, comparisons, trends, and sharing.',
 'Hold the slide long enough for both paths to be read. Use a simple dissolve from the previous clip.'),
('0:45-1:20  Clip B',
 'Numbered markers connect visible evidence to plain-language explanations. The app asks about important details a photo cannot prove. Those answers combine with the visible hazards to produce a bounded room score.',
 'Start on the results page. Hold the marked image, then scroll through two hazard cards. Continue to the follow-up questions, answer two questions, and proceed until the numerical score and colored risk bar are visible. Pause on the score.'),
('1:20-1:32  Slide 3',
 'A Streamlit upload passes through image-quality checks and OpenAI Vision. Python rules validate the returned JSON, clamp every hazard to one through fifteen points, and create questions for uncertainty. Supabase stores accounts and structured check history, Brevo sends reset codes and text summaries, and room photos remain only in the active session.',
 'Follow the six top-row steps from left to right. Then point to the Supabase, Brevo, and active-session branches before ending on the failure-handling line.'),
('1:32-1:57  Clip C',
 'The result becomes a short action plan. A later photo shows which hazard categories were resolved, which remain, and whether anything new appeared.',
 'Show all three recommended actions. Select Compare After Making Fixes, use the prepared recheck result, then pause on Resolved, Still Present, and New. Avoid rapid scrolling.'),
('1:57-2:09  Slide 4',
 'Each visible hazard receives one to fifteen points. Follow-up answers add evidence, skipped questions can add a limited buffer, and the final room score stays capped at one hundred.',
 'Hold the score slide. The three inputs and low, moderate, and high ranges must remain readable.'),
('2:09-2:21  Slide 5',
 'I tested ten staged room images containing thirty-five reference hazards. SafeHome AI correctly reported thirty-four and missed one, for a ninety-seven point one percent detection rate.',
 'Show the full testing table without zooming or panning. Keep the total row and 97.1 percent result visible.'),
('2:21-2:46  Clip D',
 'Saved checks track progress by room. The dashboard shows trends and comparisons, summaries can go to trusted people, and accessibility controls remain available throughout the app.',
 'Open Room-by-Room Stats. Show unique rooms checked, the score trend, and the before-and-after comparison. Open an email section, add one extra recipient, then briefly open Accessibility and change one setting. Use a demo email address.'),
('2:46-3:00  Slide 6',
 'SafeHome AI is designed around consistency, uncertainty, action, and access. Python rules stabilize the score, follow-up questions prevent hidden assumptions, results become trackable fixes, and accessibility remains available throughout. The app supports room decisions without diagnosing a person or guaranteeing safety.',
 'Briefly point to each of the four design decisions, then hold on the human-review statement. Leave one second of silence before ending.'),
]

for title, narration, direction in segments:
    add_heading(doc, title, 2)
    p = doc.add_paragraph(); p.add_run('Narration  ').bold = True; p.add_run(narration)
    p = doc.add_paragraph(); p.add_run('Screen direction  ').bold = True; p.add_run(direction)

doc.add_page_break()
add_heading(doc, 'Clip recording checklist', 1)
add_bullet(doc, 'Record at 1920 by 1080 and 60 frames per second.')
add_bullet(doc, 'Use the same browser size, zoom level, light theme, staged room, and demo account throughout.')
add_bullet(doc, 'Hide bookmarks, notifications, personal email addresses, and unrelated browser tabs.')
add_bullet(doc, 'Leave about one second still at the beginning and end of every clip for clean edits.')
add_bullet(doc, 'Move the cursor slowly and perform one clear action at a time.')
add_bullet(doc, 'Do not speed up scrolling enough to make labels unreadable.')
add_bullet(doc, 'Pause on the marked image, the final score, the testing result, and the before-and-after comparison.')
add_bullet(doc, 'Record each clip at least twice and keep the smoother take.')
add_bullet(doc, 'Use a staged room photo and demo recipient addresses in the final recording.')

add_heading(doc, 'Editing checklist', 1)
add_bullet(doc, 'Use only Slides 1 through 6 from the presentation. The production-reference slides do not belong in the video.')
add_bullet(doc, 'Keep the final runtime at or below three minutes.')
add_bullet(doc, 'Use simple cuts or short dissolves. Avoid animated templates and decorative transitions.')
add_bullet(doc, 'Keep app clips at normal speed unless a very small trim is needed.')
add_bullet(doc, 'Match each narration block to its listed slide or clip before adding music or captions.')
add_bullet(doc, 'Add readable captions and check that they do not cover buttons, scores, or testing totals.')
add_bullet(doc, 'Keep background music quiet enough that every word remains clear.')
add_bullet(doc, 'Watch the complete export on a phone and a laptop before submitting.')

add_heading(doc, 'Final quality check', 1)
p = doc.add_paragraph()
p.add_run('The finished video should feel like a guided app demonstration, not a slideshow. ').bold = True
p.add_run('The viewer should see the complete path from starting a check to receiving evidence, answering follow-up questions, viewing the score, acting on recommendations, tracking progress, and sharing a summary.')

doc.core_properties.title = 'SafeHome AI Recording Plan and Script'
doc.core_properties.subject = 'Three minute Congressional App Challenge video production plan'
doc.core_properties.author = 'SafeHome AI project team'
doc.save(OUT)
print(OUT)
