import qrcode
from PIL import Image
from PIL import ImageDraw, ImageFont
import datetime

#bildenummer = '00430'
#bildenavn = 'FJELLVENNER'
#kunstner = 'SHAMAN BAMERNI'
#pris = 'Kr. 4 500,-'
# /l/ => Direct to sales form /s/ => to preview screen

#Produksjon
basisurl = 'lcku.no/s/'
#Utvikling
#basisurl = 'lcku.herokuapp.com/s/'

frame_width  = 500
frame_height = 155
header_height = 100
top_border = 16
row_height = 24

def make_header():

	logoimg = Image.open("images/Lions_blue.png")
	thumbsize = 100, 100
	logoimg.thumbnail(thumbsize, Image.ANTIALIAS)
	width, height = logoimg.size
	text_left_border = width + 10

	header = Image.new('RGBA', (frame_width, header_height), (204,229,255,255))
	draw = ImageDraw.Draw(header)
	
	# get a font
	namefnt = ImageFont.truetype('times-new-roman-bold.ttf', 22)
	textfnt = ImageFont.truetype('times-new-roman.ttf', 22)
	#topfnt = ImageFont.truetype('arialbold.ttf', 24)
	#bottomfnt = ImageFont.truetype('arial.ttf', 20)
	#italicfnt = ImageFont.truetype('arial-corsivo.ttf', 14)

	now = datetime.datetime.now()
	draw.text((text_left_border,20), 'LIONS CLUB OSLO – HØYBRÅTEN', font=namefnt, fill='#606060')
	draw.text((text_left_border + 80,50), 'Kunstutstillingen %04d' % now.year, font=textfnt, fill='#606060')
	draw.rectangle(((0, 0), (frame_width-1, header_height-1)) , outline="navy" )
	
	header.paste(logoimg, (0, 0), logoimg)

	#header.paste(logoimg, (0,0))
	#header = Image.alpha_composite(header, logoimg)

	#draw.text((text_left_border,top_border + row_height*1),bildenummer, (0,0,0), font=bottomfnt)
	#draw.text((text_left_border,top_border + row_height*2),kunstner, (0,0,0), font=bottomfnt)
	#draw.text((text_left_border,top_border + row_height*3),kommentar, (0,0,0), font=bottomfnt)
	#draw.text((text_left_border,top_border + row_height*4),pris, (0,0,0), font=bottomfnt)
	
	return header
	
def make_qrcode(p_bildenummer):
	bildenummer = '%05d' % (int(p_bildenummer))
	qr = qrcode.QRCode(
		version = 2,
		error_correction = qrcode.constants.ERROR_CORRECT_L,
		box_size = 5,
		border = 2,
	)
	qr.add_data(basisurl + bildenummer)
	qr.make(fit=True)
	
	qrimg = qr.make_image(fill_color="black", back_color="white")
	
	return qrimg



def make_qrsticker(p_bildenummer, p_bildenavn, p_kunstner, p_pris, kommentar):
	bildenummer = '%05d' % (int(p_bildenummer))
	bildenavn = p_bildenavn.upper()
	kunstner = p_kunstner.upper()
	pris = 'kr {:0,.0f}'.format(int(p_pris)).replace(',',' ')
	kunstskatt = '(Kunstavgift inkludert iht. lov.)'
	
	art_header = make_header()
	h_width, h_height = art_header.size
	
	qr = qrcode.QRCode(
		version = 2,
		error_correction = qrcode.constants.ERROR_CORRECT_L,
		box_size = 5,
		border = 2,
	)
	qr.add_data(basisurl + bildenummer)
	qr.make(fit=True)

	qrimg = qr.make_image(fill_color="black", back_color="white")

	text_left_border = qrimg.pixel_size + 10

	sticker = Image.new('RGBA', (frame_width, h_height+frame_height), (255,255,255,255))
	sticker.paste(art_header, (0, 0))
	
	draw = ImageDraw.Draw(sticker)
	draw.rectangle(((0, 0), (frame_width-1, h_height+frame_height-1)) , outline="navy" )
	# get a font
	topfnt = ImageFont.truetype('arialbold.ttf', 24)
	bottomfnt = ImageFont.truetype('arial.ttf', 20)
	italicfnt = ImageFont.truetype('arial-corsivo.ttf', 14)

	draw.text((text_left_border,h_height + 5), bildenavn, (0,0,0), font=topfnt)

	sticker.paste(qrimg, (1, h_height + 1))

	qrtop = top_border + h_height
	draw.text((text_left_border,qrtop + row_height*1),bildenummer, (0,0,0), font=bottomfnt)
	draw.text((text_left_border,qrtop + row_height*2),kunstner, (0,0,0), font=bottomfnt)
	draw.text((text_left_border,qrtop + row_height*3),kommentar, (0,0,0), font=bottomfnt)
	draw.text((text_left_border,qrtop + row_height*4),pris, (0,0,0), font=bottomfnt)
	
	if p_pris >= 2000:
		draw.text((text_left_border,qrtop + row_height*5 - 4),kunstskatt, (0,0,0), font=italicfnt)
	
	return sticker
