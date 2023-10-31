import os
import pickle
import time
import kunstloader
import salesloader

con = None

# RAM VERSION 
KUNSTDB = {}
SEARCHDB = {}
SALESDB = {}
STATSDB = {}
DB_timestamp = 0
SDB_timestamp = 0
NUM_PICTURES = 0
NUM_SOLD = 0
TOTAL_SOLD = 0

def persist_RAM():
	global KUNSTDB
	global SEARCHDB
	global DB_timestamp
	print('---PERSISTING DATABASE---')
	try:
		os.remove('KUNSTDB.pkl')
	except:
		pass
	with open('KUNSTDB.pkl', 'wb+') as f:
		pickle.dump(KUNSTDB, f, pickle.HIGHEST_PROTOCOL)
	try:
		os.remove('SEARCHDB.pkl')
	except:
		pass
	with open('SEARCHDB.pkl', 'wb+') as f:
		pickle.dump(SEARCHDB, f, pickle.HIGHEST_PROTOCOL)
	DB_timestamp = time.time()
	return
        
def load_RAM():
	global KUNSTDB
	global SEARCHDB
	global DB_timestamp
	print('---LOADING DATABASE---')
	KUNSTDB = {}
	try:
		with open('KUNSTDB.pkl', 'rb') as f:
			KUNSTDB = pickle.load(f)
	except FileNotFoundError:
		pass
	SEARCHDB = {}
	try:
		with open('SEARCHDB.pkl', 'rb') as f:
			SEARCHDB = pickle.load(f)
	except FileNotFoundError:
		pass
	global NUM_PICTURES
	NUM_PICTURES = len(KUNSTDB.keys())
	return

def validate_database():
	global KUNSTDB
	global SEARCHDB
	global DB_timestamp
	need_update = False
	stale_data = False
	if len(KUNSTDB.keys()) == 0:
		need_update = True
	if DB_timestamp + 60*10 < time.time(): # Refresh only every 10 min
		need_update = True
		stale_data = True
	if need_update:
		load_RAM()
		if stale_data or len(KUNSTDB.keys()) == 0:
			print('--- HAD TO GO TO GOOGLE SOURCE DB ---')
			kunstloader.load_kunstdb_into_RAM()
	return need_update

def maketable_RAM():
	global KUNSTDB
	global SEARCHDB
	global NUM_PICTURES
	KUNSTDB = {}
	SEARCHDB = {}
	NUM_PICTURES = 0
	 
def makesalestable():
	global SALESDB
	global NUM_SOLD
	global TOTAL_SOLD
	SALESDB = {}
	NUM_SOLD = 0
	TOTAL_SOLD = 0

def insert_database_RAM(salgsid, bildenavn, kunstner, salgspris, kommentar):
	global KUNSTDB
	global SEARCHDB
	#print("bildenavn is:" + str(bildenavn))
	#print("kunstner is:"+ str(kunstner)) 
	salgsidstr = '%05d' % (int(salgsid))
	bildenavn = bildenavn.replace("\'", "").replace("\"", "")
	kommentar = kommentar.replace("\'", "").replace("\"", "")
	searchtext = "k" + salgsidstr + " " + kunstner.lower() + " " + bildenavn.lower()
	searchtext = searchtext.replace("\'", "").replace("\"", "").replace("\n", " ")
	#print("SEARCHTEXT IS: " + searchtext)
	KUNSTDB[salgsid]     = (salgsid, bildenavn, kunstner, salgspris, kommentar)
	SEARCHDB[searchtext] = (salgsid, bildenavn, kunstner, salgspris, kommentar)
	global NUM_PICTURES
	NUM_PICTURES += 1

def getrecord_RAM(kid):
	global KUNSTDB
	validate_database()
	if kid not in KUNSTDB.keys():
		#if KUNSTDB[kid] == None:
		print("Could not find that record!")
		return None
	return KUNSTDB[kid]

def searchrecords_RAM(searchparam):
	global SEARCHDB
	validate_database()
	searchstring = searchparam.lower()
	print("SØKER ETTER: "+searchstring)
	#print(SEARCHDB.keys())
	result = [value for key, value in SEARCHDB.items() if searchstring in key.lower()]
	return result	
				
def readall_RAM():
	global KUNSTDB
	validate_database()
	return KUNSTDB.values()

def getids_RAM():
	global KUNSTDB
	validate_database()
	return list(KUNSTDB.keys())
	
def insert_salesdb(salgsid, bildenavn, kunstner, salgspris, selger, tidsmerke):
	global SALESDB
	global NUM_SOLD
	global TOTAL_SOLD
	NUM_SOLD += 1
	TOTAL_SOLD += salgspris
	kunstner = kunstner.upper()
	SALESDB[salgsid] = (salgsid, bildenavn.upper(), kunstner, salgspris, selger.upper(), tidsmerke)
	if kunstner not in STATSDB: #KUNSTNER
		STATSDB[kunstner]=[kunstner,1,salgspris]
	else:
		STATSDB[kunstner][1]+=1 #Tell antall salg
		STATSDB[kunstner][2]=(STATSDB[kunstner][2]+salgspris) # Akkumuler salgspris

def calculate_artiststats():
	global STATSDB
	sorted_by_number = sorted(STATSDB.values(), key=lambda tup: tup[1], reverse=True)
	return list(sorted_by_number)

def persist_SALES():
	global SALESDB
	global STATSDB
	global SDB_timestamp
	print('---PERSISTING SALES---')
	try:
		os.remove('SALESDB.pkl')
	except:
		pass
	with open('SALESDB.pkl', 'wb+') as f:
		pickle.dump(SALESDB, f, pickle.HIGHEST_PROTOCOL)
	try:
		os.remove('STATSDB.pkl')
	except:
		pass
	with open('STATSDB.pkl', 'wb+') as f:
		pickle.dump(STATSDB, f, pickle.HIGHEST_PROTOCOL)
	SDB_timestamp = time.time()
	return
        
def load_SALES():
	global SALESDB
	global STATSDB
	global SDB_timestamp
	print('---LOADING SALES---')
	SALESDB = {}
	try:
		with open('SALESDB.pkl', 'rb') as f:
			SALESDB = pickle.load(f)
	except FileNotFoundError:
		pass
	STATSDB = {}
	try:
		with open('STATSDB.pkl', 'rb') as f:
			STATSDB = pickle.load(f)
	except FileNotFoundError:
		pass
	SDB_timestamp = time.time()
	global NUM_SOLD
	NUM_SOLD = len(SALESDB.keys())
	global TOTAL_SOLD
	TOTAL_SOLD = 0
	for tup in SALESDB.values():
		TOTAL_SOLD += tup[3]
	return

def validate_salesdata():
	global SALESDB
	global STATSDB
	global SDB_timestamp
	need_update = False
	stale_data = False
	if len(SALESDB.keys()) == 0:
		need_update = True
	if SDB_timestamp + 60*5 < time.time():
		need_update = True
		stale_data = True
	if need_update:
		load_SALES()
		if stale_data or len(SALESDB.keys()) == 0:
			print('--- HAD TO GO TO SALES XLS DB ---')
			salesloader.load_salesDB_into_RAM()
	return need_update

def is_sold(salgsid):
	global SALESDB
	validate_salesdata()
	print("SJEKKER SALG")
	print(SALESDB.keys())
	if salgsid in SALESDB.keys():
		return True
	else:
		return False

def get_num_pictures():
	global NUM_PICTURES
	return NUM_PICTURES
	
def get_num_sold():
	global NUM_SOLD
	return NUM_SOLD

def get_total_sold():
	global TOTAL_SOLD
	return TOTAL_SOLD