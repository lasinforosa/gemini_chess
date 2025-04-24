# gemini_chess
Database chess program written in Python - pyside6

TEXT IN CATALAN (Translate if needed)

Aquest ambiciós projecte em te una mica boja perquè em lio amb les versions que tinc a cada ordenador.
A veure si treballant a Github controlo el que faig a cada màquina Linux o Windows i no perdo coses que 
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
Recordar de baixar, via web, l'Stockfish, donar permisos execució i modificar el codi per apuntar
el nom precís i directori on poses el programa

EXECUCIO
$(envL)gemini_chess/src> python main.py

APP feta amb l'ajut inestimable de la IA Gemini 2.5 pro depth.... Inicialment vaig fer un altre
programa amb la IA QWEN, pero ara estic utilitzant el Gemini via Google AI Studio.
Em serveix per preguntar-li coses que no sé de Python i que em resolgui alguns embolics que jo
mateixa em creo quan escric les linies de codi.
La veritat, Gemini 2.5 es molt util pero jo m'embolico bastant amb alguns suggeriments del programa o confonc les
diferents correccions que em fa (o es confon l'IA). Però es just reconèixer una eina com aquesta
que es impressionant.
Val. D'aqui el nom que l'he possat al programa.

ESTATUS DEL PROJECTE
Aquest projecte mostra les peces i tauler grafic, permet fer jugades legals, rebre la valoració d'StockFish,
canviar peces i color casselles a uns altres predefinits i poca cosa més

PER AFEGIR
- que Stockfish mostri Multi PV (no la millor jugada i avalaució)
- Poder jugar contra StockFish
- canviar el modul o interficie d'acces a Stockfish per un generic UCI i
permetre carregar qualsevol modul UCI
- fins i tot fer partides MODUL vs MODUL
- permetre SETUP de posicio
- permetre copiar com PNG el tauler (Ho necessito pels meus articles a revistes)
- PGN: mostrar la partida, comentaris i linies al Display PGN (copia de chess...)
- PGN: carregar partida PGN i no només la primera d'un fitxer, es a dir...
- PGN: filtre i selecció de PGN amb múltiples partides
- PARTIDA: reproducció (amb o sense edició) d'una partida visionada
- PARTIDA: salvar com a nova a una colecció PGN o reemplaçar-en una existent
- PARTIDA: editar les dades Header del PGN
- BBDD: utilitzar una BBDD Sqlite3 PGN (completament de text)
- BBDD: el mateix, però amb les jugades en format BLOB (binari)
- VARIANTS: permetre Chess960, tests problemes, llibres d'escacs, repertori, entrenament
- ARBRE: mostrar arbre d'una BBDD (valoracions, freq, promigs resultats): filtre elo, dades
- ARBRE: avaluació Stockfish per cercar i crear llibre o repertori (agresiu, contra de...)

Paralelament, de moment, vaig a treballar en un projecte similar dedicat només a visionar i editar
fitxers PGN de motlyes partides, per, una cop vist com fer-ho tot, passar-ho en aquest projecte

Addicionalment, toca estudiar UCI i la llibreria chess a fons. És a dir que hi tornaré aquí passat un 
temps que espero no sigui gaire llarg (avui: 2025/04/24)



