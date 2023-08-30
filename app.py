import os
import logging
import random
from functools import wraps
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, Response, session, url_for)
from flask_table import Table, Col, LinkCol
import urllib.parse
import kunstdatabase
import kunstloader
import salesloader
import makelabels
import time
from secrethandler import getsecret, getsecret_int

google_form_url = getsecret("GOOGLE_FORM_URL")

# Path to the ad directory
directory_path = './reklame/'
# List all files in the directory
all_files = os.listdir(directory_path)
# Count ad files (with .jpg extension) 
number_of_ads = sum(1 for file in all_files if file.endswith('.jpg'))
print("Ads loaded="+str(number_of_ads))

app = Flask(__name__)
app.secret_key = getsecret("APP_SECRET_KEY")
 
# Declare resulttable and items for search result
class ItemTable(Table):
	se           = LinkCol('Se', 'se', url_kwargs=dict(kid='se'), text_fallback='SE')
	l       	 = LinkCol('Selge', 'l', url_kwargs=dict(kid='l'), text_fallback='KJØP')
	salgsnummer  = Col('Salgsnummer')
	bildenavn    = Col('Bildenavn')
	kunstnernavn = Col('Kunstnernavn')
	salgspris    = Col('Salgspris')
	kommentar    = Col('Kommentar')

class Item(object):
	def __init__(self, selge, salgsnummer, bildenavn, kunstnernavn, salgspris, kommentar):
		self.se = selge
		self.l = selge
		self.salgsnummer = salgsnummer
		self.bildenavn = bildenavn
		self.kunstnernavn = kunstnernavn
		self.salgspris = 'kr {:0,.0f}'.format(salgspris).replace(',',' ')
		self.kommentar = kommentar

# Declare table for statistics
class StatsTable(Table):
	kunstnernavn = Col('Kunstnernavn')
	antallsalg   = Col('Antall salg')
	totalsalg    = Col('Solgt for kr')
	
class PublicStatsTable(Table):
	kunstnernavn = Col('Kunstnernavn')
	antallsalg   = Col('Antall salg')
		
class StatsItem(object):
	def __init__(self, kunstnernavn, antallsalg, totalsalg):
		self.kunstnernavn = kunstnernavn
		self.antallsalg = antallsalg
		self.totalsalg = 'kr {:0,.0f}'.format(totalsalg).replace(',',' ')
		
@app.before_request
def before_request():
	#Make session variables work permanently (31 days)
	session.permanent = True

#Functions for secure access
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    accepted_username = getsecret("ADMIN_LOGIN")
    accepted_password = getsecret("ADMIN_PASSORD")
    return username == accepted_username and password == accepted_password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=['GET', 'POST'])
def index():
	logging.info('Request for root/index.')
	if 'username' in session:
		username = session['username']
	if request.method == 'POST':
		#print("WE HAVE A POST")
		#print("Value is:"+str(request.form))
		if 'Søke' in request.form:
			return redirect('search')
		if 'Statistikk' in request.form:
			return redirect('pubstatistics')
		if 'Støtte' in request.form:
			return redirect('https://www.youtube.com/watch?v=S05gLuL0a4w', code=301)
		elif 'Homepage' in request.form:
			return redirect('https://www.hoybraatenlions.no', code=301)
		elif 'Facebook' in request.form: 
			return redirect('https://www.facebook.com/hoybraatenlions/', code=301)
		elif 'Admin' in request.form: 
			# pass # do something else
			return redirect('admin')
		else:
			# pass # unknown
			return render_template("index.html")
	elif request.method == 'GET':
		pass
		# return render_template("index.html")
		#print("No Post Back Call")
	kunstdatabase.validate_database()
	kunstdatabase.validate_salesdata()
	antall_bilder = kunstdatabase.get_num_pictures()
	antall_solgt = kunstdatabase.get_num_sold()
	return render_template("index.html", antall_bilder=antall_bilder, antall_solgt = antall_solgt)

@app.route("/search")
def search():
	searchword = request.args.get('q', '')
	if searchword == None:
		return render_template("search.html")	
	elif searchword.isdigit():
		return redirect('/s/'+searchword, code=301)
	elif len(searchword) > 0:
		kunstobjekter = kunstdatabase.searchrecords_RAM(searchword)
		if kunstobjekter == None or len(kunstobjekter) < 1:
			return render_template("searchfailed.html")
		else:
			#DISPLAY RESULTS
			items = []
			for kunstobjekt in kunstobjekter:
				items.append(Item('%05d' % (kunstobjekt[0]), '%05d' % (kunstobjekt[0]), kunstobjekt[1], kunstobjekt[2], kunstobjekt[3], kunstobjekt[4]))
			table = ItemTable(items)
			return render_template("searchresults.html", resulttable = table )
	else:
		return render_template("search.html")

@app.route("/picklabels", methods=['GET', 'POST'])
@requires_auth
def picklabels(): # User picks the pictures to include
	if 'valgtebilder' in session:
		valgtebilder = session['valgtebilder']
	else:
		valgtebilder = ''
	selected = request.form.getlist('check')
	for bildenummer in selected:
		if valgtebilder == '':
			valgtebilder = bildenummer
		else:
			valgtebilder = valgtebilder + ', ' + bildenummer
	session['valgtebilder'] = valgtebilder
	return render_template("labelsearch.html", valgtebilder = valgtebilder)

@app.route("/selectlabels")
def selectlabels():
	valgtebilder = request.args.get('b', '')
	session['valgtebilder'] = valgtebilder
	
	searchword = request.args.get('q', '')
	if searchword == None:
		return render_template("labelsearch.html", valgtebilder = valgtebilder)
	elif searchword.isdigit():
		searchid = int(searchword)
		enkeltobjekt =  kunstdatabase.getrecord_RAM(searchid)
		if enkeltobjekt == None:
			return render_template("labelsearch.html", valgtebilder = valgtebilder, nofind = 1)
		else:
			searchword = '%05d' % searchid
			if valgtebilder == '':
				valgtebilder = searchword
			else:
				valgtebilder = valgtebilder + ', ' + searchword
			return render_template("labelsearch.html", valgtebilder = valgtebilder)
	elif len(searchword) > 0:
		kunstobjekter = kunstdatabase.searchrecords_RAM(searchword)
		if kunstobjekter == None or len(kunstobjekter) < 1:
			return render_template("labelsearch.html", valgtebilder = valgtebilder, nofind = 1)
		else:
			#DISPLAY RESULTS
			bildene = []
			for kunstobjekt in kunstobjekter:
				bildene.append(['%05d' % (kunstobjekt[0]), kunstobjekt[1], kunstobjekt[2], kunstobjekt[3], kunstobjekt[4] ])
			return render_template("selectlabels.html", bildesett = bildene)
	else:
		return render_template("labelsearch.html", valgtebilder = valgtebilder)
 
@app.route("/printlabels", methods=['GET', 'POST'])
def printlabels(): # User picks the pictures to include
	valgtebilder = request.args.get('b', '')
	bildeliste = valgtebilder.split(',')
	startlabel = request.args.get('firstlabel', '')
	
	bildenrliste = []
	
	for bildestreng in bildeliste:
		try:
			bildenrliste.append(int(bildestreng))
		except ValueError:
			pass      # or whatever
		
	kunstobjekter = kunstdatabase.readall_RAM() #getrecord(430)
	if kunstobjekter == None or len(kunstobjekter) < 1:
		return render_template("searchfailed.html")
	else:
		makelabels.initiate_pdf(startlabel)
		for kunstobjekt in kunstobjekter:
			if kunstobjekt[0] in bildenrliste:
				makelabels.add_label([kunstobjekt[0], kunstobjekt[1], kunstobjekt[2], kunstobjekt[3], kunstobjekt[4]])
		makelabels.save_pdf()
		
		time.sleep(3)
		# Empty list
		valgtebilder = ''
		session['valgtebilder'] = valgtebilder
		return send_from_directory(app.root_path, 'labels.pdf', mimetype='application/pdf')
		#return render_template("labelsearch.html", valgtebilder = valgtebilder, utskrift = 1 )

@app.route('/labels.pdf')
def getlabels():
	return send_from_directory(app.root_path, 'labels.pdf', mimetype='application/pdf')

@app.route('/KomplettBankDataExport.xsl')
def getKB():
	print("XSL requested!")
	return send_from_directory(app.root_path, 'KomplettBankDataExport.xsl', mimetype='text/xsl')

@app.route('/sticker/<string:stickerfile>')
def getsticker(stickerfile):
	return send_from_directory(os.path.join(app.root_path, 'sticker'), stickerfile, mimetype='image/png')

@app.route('/images/<string:imagefile>')
def images(imagefile):
	return send_from_directory(os.path.join(app.root_path, 'images'), imagefile, mimetype='image/png')

@app.route('/reklame/<string:imagefile>')
def reklame(imagefile):
	return send_from_directory(os.path.join(app.root_path, 'reklame'), imagefile, mimetype='image/jpeg')
 
@app.route('/statistics')
@requires_auth
def statistics():
	kunstdatabase.validate_salesdata()
	artist_statistics = kunstdatabase.calculate_artiststats()
	if artist_statistics != None:
		items = []
		for artist in artist_statistics:
			items.append(StatsItem(artist[0], artist[1], artist[2]))
		table = StatsTable(items)
		return render_template("statistics.html", stats_table = table, loadtime = salesloader.getloadtime() )
	else:
		return redirect('/')
		
@app.route('/pubstatistics')
def pubstatistics():
	kunstdatabase.validate_salesdata()
	artist_statistics = kunstdatabase.calculate_artiststats()
	if artist_statistics != None:
		items = []
		for artist in artist_statistics:
			items.append(StatsItem(artist[0], artist[1], artist[2]))
		table = PublicStatsTable(items)
		return render_template("statistics.html", stats_table = table, loadtime = salesloader.getloadtime() )
	else:
		return redirect('/')

@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
def admin():
	if request.method == 'POST':
		if 'LasteGS' in request.form:
			result, antallrader = kunstloader.load_kunstdb_into_RAM()
			alle_salgsnummer = kunstdatabase.getids_RAM()
			return render_template("loadresults.html", antallrader=antallrader, result = result )
		elif 'LasteSales' in request.form:
			result = salesloader.load_salesDB_into_RAM()
			# OPPDATER SALGSSTATS alle_salgsnummer = kunstdatabase.getids_RAM()
			return render_template("loadresults.html", result = result, loadtime = salesloader.getloadtime() )
		elif  'Stickers' in request.form:
			return redirect('/picklabels')
		elif 'Statistics' in request.form:
			return redirect('/statistics')
		elif 'Home' in request.form:
			return redirect('/')
		else:
			pass
	elif request.method == 'GET':
		pass
	kunstdatabase.validate_database()
	kunstdatabase.validate_salesdata()
	antall_bilder = kunstdatabase.get_num_pictures()
	antall_solgt = kunstdatabase.get_num_sold()
	total_solgt = kunstdatabase.get_total_sold()
	total_str = '{:,}'.format(total_solgt).replace(',',' ')
	return render_template("admin.html", antall_bilder=antall_bilder, antall_solgt = antall_solgt, total_solgt = total_str)

#Se på bildet
@app.route('/s/<string:kid>')
def s(kid):
	return redirect('/l/'+kid, code=301)
 
#Kjøpe bilde via Google Form		
@app.route('/l/<string:kid>')
def l(kid):
	if not 'username' in session:
		return redirect('/login', code=301)
	username = session.get('username')
	kunstid = int(kid)
	kunstobjekt = kunstdatabase.getrecord_RAM(kunstid)
	if kunstobjekt == None:
		return render_template("searchfailed.html")	
	else:
		salgsid = '%05d'%(kunstobjekt[0])
		bildenavn = urllib.parse.quote_plus(kunstobjekt[1])
		kunstner = urllib.parse.quote_plus(kunstobjekt[2])
		salgspris = kunstobjekt[3]
		kommentar = urllib.parse.quote_plus(kunstobjekt[4])
		# Gå til Google form for utfylling av salgsordre
		return redirect(google_form_url.format(kunstner, salgsid, bildenavn, salgspris, username), code=307)

@app.route('/se/<string:kid>')
def se(kid):
	kunstid = int(kid)
	kunstobjekt = kunstdatabase.getrecord_RAM(kunstid)
	if kunstobjekt == None:
		return render_template("searchfailed.html")	
	else:
		bildefil = "nopicture.png"
		salgsid = '%05d'%(kunstobjekt[0])
		bildenavn = kunstobjekt[1]
		if os.path.isfile(os.path.join(app.root_path, 'images', salgsid+'.jpg')):
			bildefil = salgsid+'.jpg'
		elif os.path.isfile(os.path.join(app.root_path, 'images', salgsid+'.jpeg')):
			bildefil = salgsid+'.jpeg'
		elif os.path.isfile(os.path.join(app.root_path, 'images', salgsid+'.png')):
			bildefil = salgsid+'.png'
		kunstner = kunstobjekt[2]
		salgspris = 'kr {:0,.0f}'.format(int(kunstobjekt[3])).replace(',',' ')
		kommentar = kunstobjekt[4]
		randomads = random.randint(1, number_of_ads)
		kunstskatt = False
		ersolgt = kunstdatabase.is_sold(kunstid)
		if ersolgt: 
			print("Bilde nr %s er SOLGT!" % (kid))
		makspris_uten_skatt = getsecret_int("KUNSTSKATT_MAKSPRIS_UTEN_SKATT")
		if int(kunstobjekt[3]) > makspris_uten_skatt:
			kunstskatt = True
		return render_template("seobjekt.html", salgsid = salgsid, bildenavn=bildenavn, kunstner=kunstner, salgspris=salgspris, kommentar=kommentar, bildefil=bildefil, randomads=randomads, kunstskatt = kunstskatt, ersolgt = ersolgt ) 

@app.route('/navigate', methods=['GET', 'POST'])
def navigate():
	if 'Kjøpe' in request.form:
		return redirect('/l/'+request.form.get('Kjøpe'), code=301)
	elif 'Inspirasjon' in request.form:
		global alle_salgsnummer
		if len(alle_salgsnummer) == 0:
			alle_salgsnummer = kunstdatabase.getids_RAM()
		random_kunstid = alle_salgsnummer[random.randint(0,len(alle_salgsnummer)-1)]
		return redirect('/se/'+str(random_kunstid), code=301)
	elif 'Søke' in request.form: 
		return redirect('search')
	else:
		redirect('/', code=301)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path), 'favicon.ico', mimetype='image/png')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		if request.form['username'] == '':
			return "Du må skrive inn ditt navn!<br><br><a href = '/login'></b>" + \
				"Klikk her for å logge på!</b></a>"
		accepted_pincode = getsecret("SELGER_PINKODE")
		if request.form['pincode'] == accepted_pincode:
			session['username'] = request.form['username']
			return render_template("loginsuccess.html") 
		return render_template("loginfailed.html")
	return render_template("login.html")

@app.route('/logout')
def logout():
	# remove the username from the session if it is there
	session.pop('username', None)
	session.pop('valgtebilder', None)
	return redirect('/', code=301) #url_for('index'))

#kunstdatabase.connect_database()
alle_salgsnummer = []  #kunstdatabase.getids_RAM()

if __name__ == '__main__':
   logging.info('Starting web application.')
   app.run()
