import os

# Load environment variable STRING
def getsecret(secretname):
	thesecret = os.getenv(secretname)
	if thesecret is None:
		print("CRITICAL ERROR: FAILED to find environment variable: \"" + secretname + "\". It is not set in this environment!")
	return thesecret

# Load environment variable INTEGER
def getsecret_int(secretname):
	thesecret = os.getenv(secretname)
	if thesecret is None:
		print("CRITICAL ERROR: FAILED to find environment variable: \"" + secretname + "\". It is not set in this environment!")
	return int(thesecret.replace(" ","").replace(",","."))

# Load environment variable FLOAT
def getsecret_float(secretname):
	thesecret = os.getenv(secretname)
	if thesecret is None:
		print("CRITICAL ERROR: FAILED to find environment variable: \"" + secretname + "\". It is not set in this environment!")
	return float(thesecret.replace(" ","").replace(",","."))