import os
import base64
import datetime
import json
import gspread
import kunstdatabase
from pytz import timezone
from oauth2client.service_account import ServiceAccountCredentials
from secrethandler import getsecret, getsecret_int, getsecret_float

numProcErrors = 0

def parse_date(somedate):
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	#print("Dato oppgitt er: "+str(somedate)+"\n")
	try:
		dateobject = datetime.datetime.strptime(str(somedate),"%d.%m.%Y")
	except ValueError:
		dateobject = None
		
	if dateobject == None:
		try:
			dateobject = datetime.datetime.strptime(str(somedate),"%d.%m")
		except ValueError:
			dateobject = None
	if dateobject != None and dateobject.year == 1900:
		dateobject = dateobject.replace(year = now.year)
	return dateobject

def parse_time(sometime):
	#print("Tid oppgitt er: "+str(sometime)+"\n")
	try:
		timeobject = datetime.datetime.strptime(str(sometime),"%H:%M")
	except ValueError:
		timeobject = None
	return timeobject

def parse_mobile(somenumber):
	stringaccepted = True
	somestring = str(somenumber)
	#print("Got "+somestring+"\n")
	somestring = somestring.replace(" ","")
	somestring = somestring.replace("+","")
	somestring = somestring.replace(".","")
	if len(somestring) > 8:
		if len(somestring) == 10 and somestring[:2] == "47":
			somestring = somestring[2:]
		elif len(somestring) == 12 and somestring[:4] == "0047":
			somestring = somestring[4:]
		else:
			stringaccepted = False
	if len(somestring) < 8:
		stringaccepted = False
	if stringaccepted:
		#print("Made "+somestring+"\n")
		return somestring
	else:
		return None

def parse_email(emailstring):
	if '@' in emailstring:
		stringaccepted = True
	else:
		stringaccepted = False
	emailstring = emailstring.replace(" ","")
	if len(emailstring) <= 5:
		stringaccepted = False
	if stringaccepted:
		return emailstring
	else:
		return None
		
def date_match(date1, date2):
	if date1 == None or date2 == None:
		result = False
	else:
		if date1.day == date2.day and date1.month == date2.month and date1.year == date2.year:
			result = True
		else:
			result = False
	return result
	
def hour_match(time1, time2):
	if time1 == None or time2 == None:
		result = False
	else:
		if time1.hour == time2.hour:
			result = True
		else:
			result = False
	return result

def process_row(salgsnummer, kunstner, bildenavn, pris, kommentar):
	global numProcErrors
	acceptedrow = True
	rowerrors = ""
	#print("DEBUG: Pris er satt til " + str(pris) + "for bilde " + bildenavn + "\n")
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	
	salgsid = int(salgsnummer)
	bildenavnstr = str(bildenavn)
	kunstnerstr = str(kunstner)
	
	salgsprisfloat = 0.0
	if isinstance(pris, str):
		salgsprisfloat = float(pris.replace("kr","").replace(" ","").replace(",","."))
	elif isinstance(pris, int):
		salgsprisfloat = float(pris)
	else:
		salgsprisfloat = float(pris)
	# Vi kalkulerer her inn kunstskatten i prisen som vises i applikasjon og på labels og avrunder til hel krone.
	makspris_uten_skatt = getsecret_int("KUNSTSKATT_MAKSPRIS_UTEN_SKATT")
	kunstskatt_prosent = getsecret_float("KUNSTSKATT_PROSENT")
	if salgsprisfloat > float(makspris_uten_skatt):
		salgsprisfloat = salgsprisfloat * (1.0 + (kunstskatt_prosent / 100))
	salgspris = round(salgsprisfloat)
	
	if salgsid == None or salgsid <= 0:
		acceptedrow = False
	
	if acceptedrow:
		#kunstdatabase.insert_database(salgsid, bildenavn, kunstner, salgspris, kommentar)
		kunstdatabase.insert_database_RAM(salgsid, bildenavnstr, kunstnerstr, salgspris, kommentar)
		print('Valid entry:' + str(salgsid) + '/' + bildenavnstr + '/' + kunstnerstr + '/' + str(pris) + '/' + kommentar)
	else:
		numProcErrors = numProcErrors + 1
		print("FAILED to process entry due to: " + rowerrors + "\n")
	return acceptedrow
	
def load_kunstdb_sheet():
	global numProcErrors
	# use creds to create a client to interact with the Google Drive API
	scopes = ['https://spreadsheets.google.com/feeds']

	# Load environment variable
	encoded_key = getsecret("GOOGLE_SHEETS_CREDS_JSON")
	if encoded_key is None:
		return 'ERROR: Failed to find key in GOOGLE_SHEETS_CREDS_JSON'
	
	# Decode
	decoded_key = base64.b64decode(encoded_key).decode('utf-8')
	# Unpack JSON
	creds_dict= json.loads(decoded_key)

	creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
	creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
	client = gspread.authorize(creds)

	kunstark_url = getsecret("KUNSTARK_URL")
	spreadsheet = client.open_by_url(kunstark_url)

	sheet = spreadsheet.sheet1

	# Extract and print all of the values
	print("Requesting all data from Google Sheet")
	rows = sheet.get_all_records()
	print("Completed requesting all data from Google Sheet")
	numrows = 0
	
	#print(rows)
	if not rows:
		numProcErrors = numProcErrors + 1
		print("ERROR: No rows found. Access problems?")
		return 'No data found.'
	else:
		for row in rows:
			if row['Salgsnummer'] != None and str(row['Pris']) != "" and str(row['Salgsnummer']).strip().isdigit() and process_row(row['Salgsnummer'], row['Kunstners navn'], row['Bildets navn'], row['Pris'], row['Kommentar']):
				numrows = numrows + 1
		return numrows

def load_kunstdb_into_RAM():
	global numProcErrors
	numProcErrors = 0
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	print('RUN STARTING AT %02d:%02d CET' % (now.hour, now.minute))
	kunstdatabase.maketable_RAM()
	rows_handled=load_kunstdb_sheet()
	kunstdatabase.persist_RAM()
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	print('%d valid rows handled.' % (rows_handled))
	if numProcErrors > 0:
		print('ERROR: %d processing problems encountered. Check detailed logs!' % (numProcErrors))
		#send_email('eirik.ora@gmail.com', 'KunstDB PROBLEMER', 'Sjekk heroku logs. %d feil!' % numProcErrors)
		#send_sms('91906353', 'KunstDB PROBLEMER! Sjekk heroku logs. %d feil!' % numProcErrors)
	print('RUN ENDING AT %02d:%02d CET' % (now.hour, now.minute))
	return numProcErrors, rows_handled
	
if __name__ == '__main__':
    #app.run()
    load_kunstdb_into_RAM()
    exit(numProcErrors)
    
