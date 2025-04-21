# gemini_chess
Batabase chess program writtrn in Python -pyside6

TEXT IN CATALAN (Translate if needed)

Aquest ambiciós projecte em te una mica boja perquè em lio amb les versions que tinc a cada ordenador.
A veure si treballant a Github controlo el que faig a cada màquina LInux o Windows i no perdo coses que 
ja he solventat previament

Aquest projecte es una barreja de diferents previs que havia fet per mi mateixa, mes o menys funcionals
i que amb Python (finalment) pretenia construir-se bàsicament fent servir llibreries existents, com
exercici i per ser pràctics.

La idea es utilitzar python-chess (chess) fins on pugui

ENTORN
Utilitzo venv. L'exemple a Linux es:
$> python -m venv envL

virtualenv o venv s'ha d'instal.ar via apt

LLIBRERIES
pyside6
sqlite3 (inclòs a python per defecte)
chess
stockfish

$(envL)> pip install nom_llibreria

INSTAL·LACIO
Doncs baixar al directori de replicació els fitxers i directoris de l'App.
Recordar de baixar via web l'Stockfish, donar permisos execució i modificar el codi per apuntar
al nom precís i directori on poses el programa

EXECUCIO
$(venev)gemini_chess/src> python main.py

APP feta amb l'ajut inestimable de la IA Gemini 2.5 pro depth.... Inicialment vaig fer un altre
programa amb la IA QWEN, pero ara estic utilitzant el Gemini via Google AI Studio.
EM serveix per preguntar-li coses que no sé de Python i que em resolgui alguns embolics que jo
mateixa em creo quan escric les linies de codi.
La veritat, Gemini 2.5 es molt util pero jo m'embolico bastant amb alguns suggeriments del programa o confonc les
diferents correccions que em fa (o es confon l'IA). Però es just reconèixer una eina com aquesta
que es impressionant.
Val. D'aqui el nom que l'he possat al programa.






