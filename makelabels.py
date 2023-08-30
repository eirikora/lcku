import labels
import os.path
from reportlab.graphics import shapes
from reportlab.graphics.shapes import Image
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
import qrcodegen
from secrethandler import getsecret_int

base_path = os.path.dirname(__file__)
#registerFont(TTFont('Judson Bold', os.path.join(base_path, 'Judson-Bold.ttf'))) 
registerFont(TTFont('Arial', os.path.join(base_path, 'arial.ttf')))
registerFont(TTFont('Arial corsivo', os.path.join(base_path, 'arial-corsivo.ttf')))
registerFont(TTFont('Arial bold', os.path.join(base_path, 'arialbold.ttf')))
registerFont(TTFont('Times new roman', os.path.join(base_path, 'times-new-roman.ttf')))
registerFont(TTFont('Times new roman bold', os.path.join(base_path, 'times-new-roman-bold.ttf')))

# Create a function to draw each label. 
def draw_label(label, width, height, obj):
    # Just convert the object to a string and print this at the bottom left of
    # the label.
	row_size = 20
	p_bildenummer, p_bildenavn, p_kunstner, p_pris, kommentarer = obj
	makspris_uten_skatt = getsecret_int("KUNSTSKATT_MAKSPRIS_UTEN_SKATT")

	bildenummer = 'Nr. %05d' % (int(p_bildenummer))
	bildenavn = p_bildenavn.upper()
	kunstner = p_kunstner.upper()
	pris = 'Pris kr {:0,.0f}'.format(int(p_pris)).replace(',',' ')
	pris = pris + ",-"
	kunstskatt_melding = '(Kunstavgift inkludert iht. lov.)'
    
	label.add(shapes.String(2, 110, bildenavn, fontName="Arial bold", fontSize=16)) # Var 20
	label.add(shapes.String(2, 110 - row_size * 1, bildenummer, fontName="Arial", fontSize=14))
	
	label.add(shapes.String(140, 110 - row_size * .8, pris, fontName="Arial bold", fontSize=14))
	if int(p_pris) > makspris_uten_skatt:
		label.add(shapes.String(140, 110 - row_size * .8 - 10, kunstskatt_melding, fontName="Arial corsivo", fontSize=8))

	label.add(shapes.String(2, 110 - row_size * 2, kunstner, fontName="Helvetica", fontSize=14))
	
	kommentarene = (kommentarer.split('\n'))
	
	krow = 0
	comment_size = 7
	for kommentar in kommentarene:
		label.add(shapes.String(2, 110 - row_size * 3 - comment_size * krow, str(kommentar).strip(), fontName="Arial corsivo", fontSize=10))
		krow += 1
	qr_sticker = qrcodegen.make_qrcode(p_bildenummer)
	label.add(Image(200-10, 2, 60, 60, qr_sticker))

def initiate_pdf(firstlabel):
	# Create an A4 portrait (210mm x 297mm) sheets with 2 columns and 8 rows of
	# labels. Each label is 90mm x 25mm with a 2mm rounded corner. The margins are
	# automatically calculated.
	specs = labels.Specification(210, 297, 2, 4, 88, 67, corner_radius=2, left_margin=12, right_margin=16, bottom_margin=10)
	
	# Create the sheet.
	global sheet
	sheet = labels.Sheet(specs, draw_label, border=False)

	#Skip the labels that should be blank (enables printing on paper where some labels already have been used)
	numlabels = int(firstlabel.strip())
	posliste = []
	for y in [1,2,3,4]:
		for x in [1,2]:
			if numlabels > 1:
				posliste.append((y,x))
				numlabels -= 1
	# Mark selected labels on the first page as already used.
	sheet.partial_page(1, tuple(posliste))

def add_label(content):
	# Add a couple of labels.
	global sheet
	sheet.add_label(content)

def save_pdf():
	global sheet
	sheet.save('labels.pdf')
	print("{0:d} label(s) output on {1:d} page(s).".format(sheet.label_count, sheet.page_count))

