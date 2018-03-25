import os
import re
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle, ListFlowable, ListItem, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors
from PyPDF2 import PdfFileMerger


width, height = letter
styles = getSampleStyleSheet()
styleN = styles["BodyText"]
styleN.alignment = TA_LEFT

# print(os.getcwd())
# os.chdir("../g/org")
# print(os.getcwd())

DATE = sys.argv[1] # like 2017-10-18
ORG_FILENAME_PREFIX = "1718-"
ORG_FILENAME_SUFFIX = ".org"
PDF_FILENAME_SUFFIX = ".pdf"
AGENDA_DIRECTORY = "agenda-files/"
COURSE_LIST = [
    ["gcp", [
        "Berrio",
        "Biele",
        "Brown",
        "Carnehammer",
        "Olmstead",
        "Rice",
        "Saunders"
    ]],
    ["hcp", [
        "Cannon",
        "Crompton",
        "Frenchman",
        "Grots",
        "Hepler",
        "Newcity",
        "Piconi",
        "Pierce",
        "Waters"
    ]],
    ["csa", [
        "Anderson",
        "Bianchi",
        "Black",
        "Earle",
        "Gebhardt",
        "Gordon",
        "Hirschbuhl",
        "Kopf",
        "Napier",
        "Potter",
        "Powers",
        "Satterfield",
        "Seiple",
        "Shoemaker",
        "van de Ven"
    ]],
    ["csp", [
        "Dugan",
        "Ennis",
        "Gottsegen",
        "Feddersen",
        "Forgione",
        "Lessard",
        "Lyons",
        "Schwartz",
        "Tsouknakis"
    ]]]
DATE_START = "*** "
READY_STATUSES = ["READY", "TIMED", "DONE", "SCHEDULED"]
SECTIONS = ["tasks", "pfc", "goal", "agenda", "ifc", "timing"]
SECTION_START = "**** "

def getSectionInfo(sectionTitle, lines):
    gotSection = False
    sectionInfo = []
    for line in lines:
        if not gotSection:
            if line[:len(SECTION_START)] == SECTION_START and sectionTitle in line:
                gotSection = True
        else:
            if line[:1] == "*":
                break
            else:
                sectionInfo.append(line)
    return sectionInfo

def buildPdfFileName(date, course):
    return AGENDA_DIRECTORY + date + "-" + course + PDF_FILENAME_SUFFIX

def getClassInfoForDate(course, date):
    orgFileName = ORG_FILENAME_PREFIX + course + ORG_FILENAME_SUFFIX
    with open(orgFileName, "r") as file:
        lines = [line.rstrip('\n') for line in file]
        print("found %s lines in file %s" % (len(lines), orgFileName))
    correctBlockAndDate = False
    blockLines = []
    sectionDict = {}
    for line in lines:
        if not correctBlockAndDate:
            if line[:len(DATE_START)] == DATE_START and ("READY" in line or "TIMED" in line or "DONE" in line) and (date in line):
                correctBlockAndDate = True
        else:
            if line[:2] == "* " or line[:3] == "** " or line[:4] == "*** ":
                break
            else:
                blockLines.append(line)
    for s in SECTIONS:
        sectionDict[s] = getSectionInfo(s, blockLines)
    sectionDict["course"] = course
    sectionDict["date"] = date
    return sectionDict

def listify(input):
    listItems = []
    for item in input:
        listItem = ListItem(Paragraph((item), styleN), leftIndent = 35, value='-')
        listItems.append(listItem)
    output = ListFlowable(listItems, bulletType='bullet')
    return output

def buildAllPagesForDate(date):
    pages = []
    files = []
    for c in COURSE_LIST:
        courseName = c[0]
        info = getClassInfoForDate(courseName, date)
        if len(info["timing"]) > 0:
            pages.append(info)
            print("  YES: got timing info for %s" % (courseName))
        else:
            print("  no: didn't get timing info for %s" % (courseName))
    for page in pages:
        left = []
        for section in SECTIONS:
            left.append(Paragraph("<b>" + section + "</b>", styleN))
            left.append(listify(page[section]))
            left.append(Spacer(1, 12))
        right = []

        right.append(Paragraph("<b>evidence of</b>", styleN))
        right.append(Paragraph("  <b>LIS</b> = listen to understand", styleN))
        right.append(Paragraph("  <b>GEN</b> = genuine questions", styleN))
        right.append(Paragraph("  <b>PER</b> = perseverence", styleN))
        right.append(Spacer(1, 48))
        students = getStudentsForCourse(page["course"])
        right.append(Table(students))
        page["left"] = left
        page["right"] = right
        files.append(buildPdfFileName(page["date"], page["course"]))
    return files, pages

def getStudentsForCourse(courseName):
    flatList = [c[1] for c in COURSE_LIST if c[0] == courseName]
    transposedList = [[n] for n in flatList[0]]
    return transposedList
    
def pagesAreCorrect(pages):
    validPageCount = True
    validColumnCount = True
    if not len(pages) > 0:
        validPageCount = False
        print("invalid page count: %s" % (len(pages)))
    for page in pages:
        columns = ["left", "right"]
        for column in columns:
            if not len(page[column]) > 0:
                validColumnCount = False
                print("invalid column: %s in %s class" % (column, page["class"]))
                print(page[column])
                break
    return (validPageCount and validColumnCount)

def printPages(pages):
    if not pagesAreCorrect(pages):
        print("PROBLEM: pages not correct")
    else:
        print("\nok to print!")
        for i, page in enumerate(pages):
            table = Table([[page["left"], page["right"]]], colWidths=[9 * cm, 9 * cm])
            table.setStyle(TableStyle([
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP')
                                   ]))
            fileName = buildPdfFileName(page["date"], page["course"])
            c = canvas.Canvas(fileName, pagesize=letter)
            w, h = table.wrapOn(c, width, height)
            table.drawOn(c, 100, 700 - h, 0)
            c.drawString(500, 50, page["course"])
            c.drawString(500, 65, page["date"])
            c.save()
            print("  printed %s" % (fileName))

def consolidateFiles(date, files):
    merger = PdfFileMerger()
    for file in files:
        merger.append(open(file, 'rb'))
    fileName = AGENDA_DIRECTORY + date + ".pdf"
    with open(fileName, 'wb') as fout:
        merger.write(fout)
    print("  printed %s" % (fileName))

def main():
    files, pages = buildAllPagesForDate(DATE)
    printPages(pages)
    consolidateFiles(DATE, files)

if __name__ == '__main__':
    main()
