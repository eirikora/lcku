# LCKU

Kunst Applikasjon for Lions Høybråten og deres årlige Kunstutstilling

Følgede må settes opp:

Environment variablene må settes opp lokalt (for testing) og i Azure under Web App -> Configuration -> Application Settings hvor følgende key-value par må settes opp:
- ADMIN_LOGIN : Login for administrator
- ADMIN_PASSORD : Passord for administrator
- GOOGLE_FORM_URL : URL til Google form for salgsprosess. Må ha identifisert de 6 variablene som skal fylles inn.
- GOOGLE_SHEETS_CREDS_JSON : Base64 encoded JSON av Google API key (se encodekey,py for hvordan denne skapes)
- KUNSTARK_URL : URL til Google ark med kunst (f.eks. http://sheets.google. ...)
- SALGSARK_URL : URL til Google ark med salgene (f.eks. http://sheets.google. ...)
- SELGER_PINKODE : Pin koden som selgeren må legge inn for å kunne registrere seg (f.eks. 1234)
- APP_SECRET_KEY : Secret random key for webserver sikkerhet
- KUNSTSKATT_MAKSPRIS_UTEN_SKATT : På hvilket krone-beløp slår kunstskatten inn (f.eks. 2000)
- KUNSTSKATT_PROSENT : Hvor mange prosent er kunstskatten (f.eks. 5)