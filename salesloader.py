import os
import base64
import datetime
import json
import gspread
import kunstdatabase
from pytz import timezone
from oauth2client.service_account import ServiceAccountCredentials
from secrethandler import getsecret

numProcErrors = 0
loadtime = ''

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

def process_row(salgsnummer, kunstner, bildenavn, pris, selger, tidsmerke):
	global numProcErrors
	acceptedrow = True
	rowerrors = ""
	
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	
	salgsid = int(salgsnummer)
	salgspris = int(pris)
	
	if salgsid == None or salgsid <= 0:
		acceptedrow = False
	
	if acceptedrow:
		kunstdatabase.insert_salesdb(salgsid, bildenavn, kunstner.upper(), salgspris, selger, tidsmerke)
		print('Valid entry:' + str(salgsid) + '/' + bildenavn + '/' + kunstner + '/' + str(pris) + '/' + selger)
	else:
		numProcErrors = numProcErrors + 1
		print("FAILED to process entry due to: " + rowerrors + "\n")
	return acceptedrow

def load_sales_sheet():
	global numProcErrors
	# use creds to create a client to interact with the Google Drive API
	scopes = ['https://spreadsheets.google.com/feeds']

	# Get encoded key for accessing Google Sheet
	encoded_key = getsecret("GOOGLE_SHEETS_CREDS_JSON")
	if encoded_key is None:
		return 'Failed to find key in GOOGLE_SHEETS_CREDS_JSON'
	
	# Decode key
	decoded_key = base64.b64decode(encoded_key).decode('utf-8')
	# Unpack JSON inside key
	creds_dict= json.loads(decoded_key)

	creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
	creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
	client = gspread.authorize(creds)

	# Access Sales spreadsheet
	salgsark_url = getsecret("SALGSARK_URL")
	spreadsheet = client.open_by_url(salgsark_url)
	sheet = spreadsheet.sheet1

	# Extract and print all of the values
	rows = sheet.get_all_records()
	numrows = 0
	
	#print(rows)
	if not rows:
		numProcErrors = numProcErrors + 1
		print("ERROR: No rows found. Access problems?")
		return 'No data found.'
	else:
		for row in rows:
			if row['Tidsmerke'] != None and process_row(row['Salgsnummer'], row['Kunstnerens navn'], row['Bildets tittel'], row['Pris for bildet/objekt'], row['Lions selger'], row['Tidsmerke']):
				numrows = numrows + 1
		return numrows

def load_salesDB_into_RAM():
	global numProcErrors
	global loadtime
	numProcErrors = 0
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	loadtime = '%04d-%02s-%02d kl %02d:%02d CET' % (now.year, now.month, now.day, now.hour, now.minute)
	print('RUN STARTING AT %02d:%02d CET' % (now.hour, now.minute))
	kunstdatabase.makesalestable()
	rows_handled=load_sales_sheet()
	now = datetime.datetime.now(timezone('Europe/Berlin'))
	print('%d valid rows handled.' % (rows_handled))
	if numProcErrors > 0:
		print('ERROR: %d processing problems encountered in reading sales stats. Check detailed logs!' % (numProcErrors))
		#send_email('eirik.ora@gmail.com', 'KunstDB PROBLEMER', 'Sjekk heroku logs. %d feil!' % numProcErrors)
		#send_sms('91906353', 'KunstDB PROBLEMER! Sjekk heroku logs. %d feil!' % numProcErrors)
	print('RUN ENDING AT %02d:%02d CET' % (now.hour, now.minute))
	return numProcErrors

def getloadtime():
	global loadtime
	return loadtime

if __name__ == '__main__':
    #app.run()
    load_salesDB_into_RAM()
    exit(numProcErrors)
    
