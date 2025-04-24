# main_window.py
import sys
import os # <<-- Necessari per construir camins (paths)
import chess # <<-- Necessari per la lògica del joc

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QPushButton, QTextEdit, QLabel, QSplitter, QSizePolicy, QMessageBox # Afegit QMessageBox per a errors
)
from PySide6.QtGui import QIcon, QColor, QPainter, QAction
from PySide6.QtCore import (Qt, QSize, Slot, QThread, Signal, QObject,
                            QMetaObject, Q_ARG)

from helpers import *
from chessboard_widget import ChessboardWidget, SQUARE_SIZE
from engine_manager import ChessEngine

path_to_stockfish = "../engines/stockfish-ubuntu-x86-64-sse41-popcnt" # <<-- Actualitza el camí al teu Stockfish

# per control·lar el DEBUG i les sortides print
debug = "cap"

# Defineix els colors fora de les funcions per reutilitzar-los fàcilment
DEFAULT_LIGHT_COLOR = QColor("#FFFFFF") # Blanc (Original)
DEFAULT_DARK_COLOR = QColor("#7388B6")  # Blau (Original)
BROWN_LIGHT_COLOR = QColor("#F0D9B5")   # Marró clar (exemple)
BROWN_DARK_COLOR = QColor("#B58863")    # Marró fosc (exemple)
GREEN_LIGHT_COLOR = QColor("#FFFFFF")  # Verd clar (exemple #A9D18E)
GREEN_DARK_COLOR = QColor("#A9D18E")   # Verd fosc (exemple #4F8C2A)

# Determina el directori base i altres directoris
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "..", "assets", "icons")
PIECES_BASE_DIR = os.path.join(BASE_DIR, "..", "assets", "pieces") # Directori que conté els subdirectoris de peces

# --- Defineix els directoris dels diferents jocs de peces ---
PIECES_DIR_BERLIN = os.path.join(PIECES_BASE_DIR, "berlin") # <<-- Usa minúscules si així es diu la carpeta!
PIECES_DIR_JULIUS = os.path.join(PIECES_BASE_DIR, "julius")
PIECES_DIR_MERIDA = os.path.join(PIECES_BASE_DIR, "merida")
PIECES_DIR_MERIDA_NEW = os.path.join(PIECES_BASE_DIR, "merida_new") # Posa els noms EXACTES de les teves carpetes
PIECES_DIR_CHESS_COM = os.path.join(PIECES_BASE_DIR, "chess_com") # Només si existeix
PIECES_DIR_CBURNETT = os.path.join(PIECES_BASE_DIR, "cburnett")
PIECES_DIR_USUAL = os.path.join(PIECES_BASE_DIR, "usual")


# --- Defineix el directori per defecte ---
DEFAULT_PIECES_DIR = PIECES_DIR_BERLIN # Estableix el teu default preferit



# Comprova si el directori de peces existeix
if debug == "peces":
  if not os.path.isdir(PIECES_BASE_DIR):
    print(f"AVÍS CRÍTIC: El directori de peces '{PIECES_DIR}' no existeix o no és un directori!")
    # Considera mostrar un error més visible a l'usuari aquí també
    QMessageBox.warning(None, "Error de Recursos", f"Directori de peces no trobat:\n{PIECES_BASE_DIR}")
    # Potencialment, hauries de sortir o carregar un conjunt d'imatges per defecte



# main.py (després de les importacions, abans de MainWindow)

class StockfishWorker(QObject):
    """
    Objecte Worker que s'executarà en un fil separat per a l'anàlisi de Stockfish.
    """
    # Senyal emès quan l'anàlisi està llesta. Passa un diccionari o None.
    analysis_ready = Signal(object) # 'object' pot ser dict o None

    def __init__(self, engine: ChessEngine):
        super().__init__()
        self.engine = engine
        self._is_running = True
        # Pots configurar valors per defecte aquí si vols
        self.default_depth = 15
        self.default_multipv = 1 # Comença mostrant només la millor línia

    # Modifica la signatura per acceptar multipv i usar els mètodes correctes
    @Slot(str, int, int) # Rep fen, depth, num_lines
    def run_analysis(self, fen: str, depth: int | None, num_lines: int | None):
        """Mètode principal que executa el càlcul en el fil del worker."""
        if not self._is_running:
             return

        current_depth = depth if depth is not None else self.default_depth
        current_multipv = num_lines if num_lines is not None else self.default_multipv

        print(f"Worker: Analitzant FEN {fen} amb depth={current_depth}, MultiPV={current_multipv}")

        # Crida al NOU mètode de l'engine
        analysis_result = self.engine.get_analysis(fen, current_depth, current_multipv)

        # Emet el senyal AMB el resultat (llista de diccionaris o None)
        self.analysis_ready.emit(analysis_result)

    def stop(self):
        """Indica al worker que s'aturi."""
        self._is_running = False


# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplicació d'Escacs (PySide6)")
        # Ajusta la mida inicial per acomodar millor tauler i panells
        initial_board_width = SQUARE_SIZE * 8
        initial_info_width = 350 # Amplada estimada pel panell dret
        estimated_height = initial_board_width + 80 # Tauler + botons + marges/barres
        self.setGeometry(100, 100, initial_board_width + initial_info_width, estimated_height)

        
        # <<-- Comprova si els directoris de peces existeixen (important fer-ho a __init__) -->>
        self.available_piece_sets = {} # Guardarem els camins vàlids
        if os.path.isdir(PIECES_DIR_BERLIN): self.available_piece_sets["Berlin (Default)"] = PIECES_DIR_BERLIN
        if os.path.isdir(PIECES_DIR_JULIUS): self.available_piece_sets["Julius"] = PIECES_DIR_JULIUS
        if os.path.isdir(PIECES_DIR_MERIDA): self.available_piece_sets["Merida"] = PIECES_DIR_MERIDA
        if os.path.isdir(PIECES_DIR_MERIDA_NEW): self.available_piece_sets["Merida New"] = PIECES_DIR_MERIDA_NEW
        if os.path.isdir(PIECES_DIR_CHESS_COM): self.available_piece_sets["Chess.com"] = PIECES_DIR_CHESS_COM
        if os.path.isdir(PIECES_DIR_CBURNETT): self.available_piece_sets["Cburnett"] = PIECES_DIR_CBURNETT
        if os.path.isdir(PIECES_DIR_USUAL): self.available_piece_sets["Usual"] = PIECES_DIR_USUAL

        if not self.available_piece_sets:
             # Error crític si no hi ha cap joc de peces
             QMessageBox.critical(self, "Error Crític", "No s'ha trobat cap directori de peces vàlid a la carpeta 'pieces'.")
             # Decideix si vols sortir o continuar amb errors visuals
             # sys.exit(1)

         # --- Configuració Stockfish ---
        self.path_to_stockfish = os.path.join(BASE_DIR, "..", "assets", "engines", "stockfish-ubuntu-x86-64-sse41-popcnt") # AJUSTA CAMÍ
        self.stockfish_active = False # Comença desactivat
        try:
            self.engine = ChessEngine(self.path_to_stockfish)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error Stockfish",
                                 f"No s'ha trobat el motor Stockfish a:\n{self.path_to_stockfish}\n"
                                 "L'anàlisi del motor estarà desactivada.")
            self.engine = None # Marca que el motor no està disponible
        except Exception as e:
             QMessageBox.critical(self, "Error Stockfish", f"Error inicialitzant Stockfish: {e}")
             self.engine = None
             
        # <<-- Lògica del Joc (Estat) -->>
        self.board = chess.Board()  # Instància del tauler de python-chess
        self.selected_square = None # Per guardar la casella seleccionada

        # --- Configuració del Threading per Stockfish ---
        self.stockfish_thread = None
        self.stockfish_worker = None
        if self.engine: # Només crea el fil si el motor s'ha inicialitzat bé
             self._setup_stockfish_thread()
        

        self._setup_ui()
        self._update_board_display() # Dibuixa l'estat inicial
        self._update_pgn_display() # Mostra info inicial del PGN
        self._update_engine_display_status() # Mostra estat inicial motor


    def _setup_stockfish_thread(self):
         """Configura el fil i el worker per a l'anàlisi de Stockfish."""
         self.stockfish_thread = QThread()
         self.stockfish_worker = StockfishWorker(self.engine)
         self.stockfish_worker.moveToThread(self.stockfish_thread)

         self.stockfish_worker.analysis_ready.connect(self._display_stockfish_result)

         # Comença el fil (estarà esperant senyals per executar run_analysis)
         self.stockfish_thread.start()
         print("Fil de Stockfish iniciat.")

        
    def _setup_ui(self):
        # --- Widget Central i Layout Principal ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget) # Layout principal horitzontal

        # --- Splitter per dividir panells ---
        splitter = QSplitter(Qt.Orientation.Horizontal) # Explicitament Horitzontal
        main_layout.addWidget(splitter)

        # --- Panell Esquerre (Tauler i Botons) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0) # Sense marges interns
        left_layout.setSpacing(5) # Un petit espai entre tauler i botons

        # -- Tauler d'Escacs --
        # <<-- IMPORTANT: Crea la instància del TEU ChessboardWidget real -->>
        # <<-- Passa la ruta al directori de peces -->>
        self.chessboard_widget = ChessboardWidget(resources_path=DEFAULT_PIECES_DIR)
        # Com que ChessboardWidget (QGraphicsView) no té una política de mida ideal per defecte,
        # la contenim dins un widget normal per controlar-ne millor l'expansió.
        board_container = QWidget()
        board_container_layout = QVBoxLayout(board_container) # Podria ser QHBoxLayout també
        board_container_layout.setContentsMargins(0,0,0,0)
        board_container_layout.addWidget(self.chessboard_widget, 0, Qt.AlignmentFlag.AlignCenter) # Centra el tauler si l'espai és més gran
        # Permet que el contenidor creixi, però el tauler (dins) està centrat
        left_layout.addWidget(board_container, 1) # El '1' permet que el contenidor s'expandeixi

        # <<-- CONNECTAR SENYAL DEL TAULER a un SLOT de MainWindow -->>
        self.chessboard_widget.square_clicked.connect(self.handle_square_click)

        # -- Barra de Botons (Horitzontal i Centrada) --
        # (El teu codi per crear botons amb addStretch ja és correcte aquí)
        self.button_bar_layout = QHBoxLayout()
        self.button_bar_layout.setContentsMargins(5, 5, 5, 5)

        self.button_bar_layout.addStretch(1)
        self.button_start = self._create_button(os.path.join(ICONS_DIR, "start.png"), "Anar al Principi", "go_to_start")
        self.button_bar_layout.addWidget(self.button_start)
        self.button_prev = self._create_button(os.path.join(ICONS_DIR, "prev.png"), "Moviment Anterior", "go_to_previous_move")
        self.button_bar_layout.addWidget(self.button_prev)
        self.button_next = self._create_button(os.path.join(ICONS_DIR, "next.png"), "Moviment Següent", "go_to_next_move")
        self.button_bar_layout.addWidget(self.button_next)
        self.button_end = self._create_button(os.path.join(ICONS_DIR, "end.png"), "Anar al Final", "go_to_end")
        self.button_bar_layout.addWidget(self.button_end)
        self.button_reset = self._create_button(os.path.join(ICONS_DIR, "reset.png"), "Reiniciar Tauler", "reset_board")
        self.button_bar_layout.addWidget(self.button_reset)
        self.button_flip = self._create_button(os.path.join(ICONS_DIR, "gira.png"), "Girar Tauler", "flip_board")
        self.button_bar_layout.addWidget(self.button_flip)
        self.button_engine = self._create_button(os.path.join(ICONS_DIR, "cpu.png"), "Anàlisi del Motor", "toggle_engine_analysis")
        self.button_bar_layout.addWidget(self.button_engine)
        self.button_bar_layout.addStretch(1)

        left_layout.addLayout(self.button_bar_layout, 0) # 0 = no expandir verticalment

        splitter.addWidget(left_panel)

        # --- Panell Dret (PGN, Info, etc.) ---
        # (Aquesta part sembla correcta, només assegura't que els widgets s'instancien bé)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.pgn_label = QLabel("PGN Notation:")
        right_layout.addWidget(self.pgn_label)
        self.pgn_display = QTextEdit()
        self.pgn_display.setReadOnly(True)
        self.pgn_display.setPlaceholderText("La notació PGN apareixerà aquí...")
        right_layout.addWidget(self.pgn_display, 1)

        self.engine_label = QLabel("Stockfish Info:")
        right_layout.addWidget(self.engine_label)
        self.engine_info_display = QTextEdit()
        self.engine_info_display.setReadOnly(True)
        self.engine_info_display.setFixedHeight(100)
        self.engine_info_display.setPlaceholderText("L'anàlisi del motor apareixerà aquí...")
        right_layout.addWidget(self.engine_info_display, 0)

        splitter.addWidget(right_panel)

        # --- Configuració final del Splitter ---
        initial_board_width_approx = SQUARE_SIZE * 8 + 40 # Amplada tauler + petits marges
        splitter.setSizes([initial_board_width_approx, 350]) # Ajusta mides inicials si cal

        # --- Barra de Menú i Estat ---
        self._create_menu()
        self.statusBar().showMessage("A punt")


    def _create_button(self, icon_path, tooltip, slot_func_name):
        # (El teu codi aquí és correcte, només s'actualitza icon_path si és relatiu)
        button = QPushButton()
        if icon_path:
            # Si la ruta no és absoluta, la construeix des de BASE_DIR
            # (Ara ja la construïm abans de cridar la funció)
            # if not os.path.isabs(icon_path):
            #      icon_path = os.path.join(BASE_DIR, icon_path)

            icon = QIcon(icon_path)
            if not icon.isNull():
                button.setIcon(icon)
                button.setIconSize(QSize(32, 32))
            else:
                button.setText(tooltip.split()[0])
                print(f"Avís: No s'ha trobat icona a '{icon_path}' per '{tooltip}'")
        else:
             button.setText(tooltip.split()[0])

        button.setToolTip(tooltip)
        button.setFixedSize(40, 40) # Mida fixa per consistència

        if hasattr(self, slot_func_name):
            button.clicked.connect(getattr(self, slot_func_name))
        else:
            print(f"Avís: El mètode (slot) '{slot_func_name}' no existeix.")

        return button


    def _create_menu(self):
        # (Aquesta part està bé, només actualitza les icones si cal)
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Fitxer")

        icon_open = QIcon(os.path.join(ICONS_DIR, "folder.png"))
        open_action = QAction(icon_open if not icon_open.isNull() else "&Obrir PGN...", self)
        open_action.setStatusTip("Obrir un fitxer PGN")
        open_action.triggered.connect(self.open_pgn_file)
        file_menu.addAction(open_action)

        icon_save = QIcon(os.path.join(ICONS_DIR, "save.png"))
        save_action = QAction(icon_save if not icon_save.isNull() else "&Desar PGN...", self)
        save_action.setStatusTip("Desar la partida actual com a fitxer PGN")
        # save_action.triggered.connect(self.save_pgn_file) # Implementa aquesta funció si cal
        file_menu.addAction(save_action)
        file_menu.addSeparator() # Separador

        icon_bd = QIcon(os.path.join(ICONS_DIR, "bbdd.png"))
        open_bbdd = QAction(icon_open if not icon_open.isNull() else "&Obrir BBDD..", self)
        open_bbdd.setStatusTip("Obrir un fitxer de BBDD")
        # open_bbdd.triggered.connect(open_bbdd)
        file_menu.addAction(open_bbdd)

        icon_saveBD = QIcon(os.path.join(ICONS_DIR, "save.png"))
        save_bbdd = QAction(icon_save if not icon_save.isNull() else "&Desar BBDD...", self)
        save_bbdd.setStatusTip("Desar la partida actual en una BBDD")
        # save_action.triggered.connect(self.save_pgn_file) # Implementa aquesta funció si cal
        file_menu.addAction(save_bbdd)
        file_menu.addSeparator() # Separador


        icon_exit = QIcon(os.path.join(ICONS_DIR, "x-circle.png"))
        exit_action = QAction(icon_exit if not icon_exit.isNull() else "&Sortir", self)
        exit_action.setStatusTip("Tancar l'aplicació")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        moduls_menu = menu_bar.addMenu("&Moduls")
        # Acció per Activar/Desactivar Stockfish
        icon_stockfish = QIcon(os.path.join(ICONS_DIR, "cpu.png")) # Reutilitza icona CPU o usa una específica
        self.action_stockfish_toggle = QAction("&Stockfish", self)
        if not icon_stockfish.isNull():
         self.action_stockfish_toggle.setIcon(icon_stockfish) # Assigna la icona si és vàlida
        self.action_stockfish_toggle.setCheckable(True) # Fes que sigui una acció activable/desactivable
        self.action_stockfish_toggle.setChecked(self.stockfish_active) # Estat inicial
        self.action_stockfish_toggle.setStatusTip("Activar/Desactivar l'anàlisi del motor Stockfish")
        # <<-- CONNECTA AL TOGGLE CORRECTE -->>
        self.action_stockfish_toggle.triggered.connect(self.toggle_engine_analysis)
        moduls_menu.addAction(self.action_stockfish_toggle)
        # Desactiva el menú si el motor no s'ha carregat
        if not self.engine:
             moduls_menu.setEnabled(False)
        
        conf_menu = menu_bar.addMenu("&Configuració")

        # --- Acció per Tauler Marró ---
        icon_marro = QIcon(os.path.join(ICONS_DIR, "marro.png")) # Assegura't que existeix 'marro.png'
        action_marro = QAction("Tauler &Marró", self)
        if not icon_marro.isNull():
            action_marro.setIcon(icon_marro)
        action_marro.setStatusTip("Canviar a l'estil de tauler marró")
        action_marro.triggered.connect(self.set_board_style_brown) # Crida al nou slot
        conf_menu.addAction(action_marro)

        # --- Acció per Tauler Blau (Original) ---
        icon_blau = QIcon(os.path.join(ICONS_DIR, "blau.png")) # Necessites 'blau.png'
        action_blau = QAction("Tauler &Blau (Default)", self)
        if not icon_blau.isNull():
            action_blau.setIcon(icon_blau)
        action_blau.setStatusTip("Restaurar l'estil de tauler original (blau/blanc)")
        action_blau.triggered.connect(self.set_board_style_default) # Crida a l'altre slot
        conf_menu.addAction(action_blau)
        
        # --- Acció per Tauler Verd ---
        icon_verd = QIcon(os.path.join(ICONS_DIR, "verd.png")) # Necessites 'verd.png'
        action_verd = QAction("Tauler &Verd", self)
        if not icon_verd.isNull():
            action_verd.setIcon(icon_verd)
        action_verd.setStatusTip("Canviar a l'estil de tauler verd")
        action_verd.triggered.connect(self.set_board_style_verd) # Crida a l'altre slot
        conf_menu.addAction(action_verd)

        conf_menu.addSeparator() # Separador

        # -- Submenú per Estils de Peces --
        pieces_menu = conf_menu.addMenu("Estil de &Peces")
        # Crear accions dinàmicament basat en els directoris trobats
        if "Berlin (Default)" in self.available_piece_sets:
            action_berlin = QAction("Figs &Berlin (Default)", self)
            # Pots afegir icones si les tens: action_berlin.setIcon(...)
            action_berlin.setStatusTip("Canviar a l'estil de peces Berlin")
            # Usa lambda per passar el camí correcte al slot genèric
            action_berlin.triggered.connect(
                lambda: self.set_piece_style(self.available_piece_sets["Berlin (Default)"], "Berlin")
            )
            pieces_menu.addAction(action_berlin)

        if "Julius" in self.available_piece_sets:
            action_julius = QAction("Figs &Julius", self)
            action_julius.setStatusTip("Canviar a l'estil de peces Julius")
            action_julius.triggered.connect(
                lambda: self.set_piece_style(self.available_piece_sets["Julius"], "Julius")
            )
            pieces_menu.addAction(action_julius)
            
        if "Merida" in self.available_piece_sets:
            action_merida = QAction("Figs &Merida", self)
            action_merida.setStatusTip("Canviar a l'estil de peces Merida")
            action_merida.triggered.connect(
                lambda: self.set_piece_style(self.available_piece_sets["Merida"], "Merida")
            )
            pieces_menu.addAction(action_merida)

        if "Merida New" in self.available_piece_sets:
            action_merida_new = QAction("Figs Merida &New", self)
            action_merida_new.setStatusTip("Canviar a l'estil de peces Merida New")
            action_merida_new.triggered.connect(
                 lambda: self.set_piece_style(self.available_piece_sets["Merida New"], "Merida New")
             )
            pieces_menu.addAction(action_merida_new)

        if "Chess.com" in self.available_piece_sets:
            action_chess_com = QAction("Figs Chess_&Com", self)
            action_chess_com.setStatusTip("Canviar a l'estil de peces Chess.com")
            action_chess_com.triggered.connect(
                 lambda: self.set_piece_style(self.available_piece_sets["Chess.com"], "Chess.com")
             )
            pieces_menu.addAction(action_chess_com)

        if "Cburnett" in self.available_piece_sets:
             action_cburnett = QAction("Figs &Cburnett", self)
             action_cburnett.setStatusTip("Canviar a l'estil de peces Cburnett")
             action_cburnett.triggered.connect(
                 lambda: self.set_piece_style(self.available_piece_sets["Cburnett"], "Cburnett")
             )
             pieces_menu.addAction(action_cburnett)

        if "Usual" in self.available_piece_sets:
             action_usual = QAction("Figs &Usual", self)
             action_usual.setStatusTip("Canviar a l'estil de peces Usual")
             action_usual.triggered.connect(
                 lambda: self.set_piece_style(self.available_piece_sets["Usual"], "Usual")
             )
             pieces_menu.addAction(action_usual)


          
        
        
    #---- defs ---------

    def _update_board_display(self):
        """Actualitza el widget del tauler amb l'estat actual de self.board."""
        self.chessboard_widget.update_board(self.board)
        # També podem netejar la selecció aquí si volem, o només netejar highlights visuals
        self.chessboard_widget._clear_highlights() # Neteja highlights visuals
        self.selected_square = None # Desselecciona lògicament

        # Potser vols afegir una variable per controlar quantes línies vols
        # de moment no va mostrar PV
        self.current_multipv = 1 # Número de línies a mostrar inicialment

        # <<-- DESPRÉS d'actualitzar el tauler, si Stockfish està actiu, demana anàlisi -->>
        if self.stockfish_active and self.stockfish_worker and self.stockfish_thread and self.stockfish_thread.isRunning():
             print("Moviment fet, demanant anàlisi a Stockfish...")
             # Neteja la pantalla mentre s'espera
             self.engine_info_display.setPlaceholderText("Stockfish analitzant...")
             self.engine_info_display.clear()
             # Crida a run_analysis via senyal/slot implícit o MetaObjectConnection
             # (passant el FEN actual) per executar-ho al fil del worker.
             # Ajusta depth i movetime com vulguis
             analysis_depth = 15
             # analysis_time = 1500 # ms
             # Use QMetaObject.invokeMethod for thread-safe call to worker slot
             QMetaObject.invokeMethod(self.stockfish_worker, "run_analysis", Qt.QueuedConnection,
                                   Q_ARG(str, self.board.fen()),
                                   Q_ARG(int, analysis_depth),
                                   Q_ARG(int, self.current_multipv)) # <<-- Passa MultiPV

    @Slot(bool) # El triggered d'una acció checkable passa l'estat (True/False)
    def toggle_engine_analysis(self, checked: bool):
         """Activa o desactiva l'anàlisi de Stockfish."""
         if not self.engine:
             print("Intent d'activar Stockfish, però el motor no està carregat.")
             self.action_stockfish_toggle.setChecked(False) # Mantén-lo desactivat
             return

         self.stockfish_active = checked # Actualitza l'estat intern
         if debug == "stockfish":
             print(f"Stockfish Actiu: {self.stockfish_active}")
         self.statusBar().showMessage(f"Anàlisi Stockfish {'Activada' if self.stockfish_active else 'Desactivada'}", 2000)

         self._update_engine_display_status() # Actualitza la pantalla

         if self.stockfish_active:
             # Si s'activa, llança una primera anàlisi de la posició actual
             self._trigger_stockfish_update_if_needed()


    def _trigger_stockfish_update_if_needed(self):
        """Helper per llançar anàlisi si està actiu i el fil funciona."""
        if self.stockfish_active and self.stockfish_worker and self.stockfish_thread and self.stockfish_thread.isRunning():
            self.engine_info_display.setPlaceholderText("Stockfish analitzant...")
            self.engine_info_display.clear()
            analysis_depth = 15 # Configurable
            QMetaObject.invokeMethod(self.stockfish_worker, "run_analysis", Qt.QueuedConnection,
                                   Q_ARG(str, self.board.fen()),
                                   Q_ARG(int, analysis_depth),
                                   Q_ARG(int, self.current_multipv)) # <<-- Passa MultiPV

    def _update_engine_display_status(self):
         """Actualitza el text del display del motor segons l'estat actiu/inactiu."""
         if not self.engine:
              self.engine_info_display.setPlainText("Motor Stockfish no disponible.")
              self.engine_info_display.setPlaceholderText("")
         elif not self.stockfish_active:
              self.engine_info_display.setPlainText("Stockfish desactivat.")
              self.engine_info_display.setPlaceholderText("Activa Stockfish des del menú Mòduls.")
         else:
              # No esborris si està actiu, espera la propera anàlisi
              if not self.engine_info_display.toPlainText(): # Si està buit, posa placeholder
                  self.engine_info_display.setPlaceholderText("Esperant moviment per analitzar...")


    @Slot(object) # Rep el diccionari (o None) des del worker
    def _display_stockfish_result(self, analysis_results: list | None):
         """Actualitza la UI amb el resultat rebut del fil de Stockfish."""
         if not self.stockfish_active: # Comprova per si s'ha desactivat mentre calculava
             return

         """
         if result:
             
             best_move_uci = result['best_move']
             evaluation = result['evaluation']

             # Intenta convertir el moviment UCI a SAN per llegibilitat
             try:
                  move = self.board.parse_uci(best_move_uci)
                  best_move_san = self.board.san(move)
             except ValueError:
                  best_move_san = best_move_uci # Mostra UCI si falla la conversió

             # Formata l'avaluació
             eval_type = evaluation.get('type', 'cp') # 'cp' o 'mate'
             eval_value = evaluation.get('value', 0)
             if eval_type == 'cp':
                  # Converteix centipeons a puntuació decimal
                  score = eval_value / 100.0
                  eval_str = f"{score:.2f}"
             elif eval_type == 'mate':
                  eval_str = f"Mate en {eval_value}"
             else:
                  eval_str = "N/A"

             analysis_text = f"Millor moviment: {best_move_san} ({best_move_uci})\nAvaluació: {eval_str}"
             self.engine_info_display.setPlainText(analysis_text)
             self.engine_info_display.setPlaceholderText("") # Treu placeholder
         else:
             # Hi ha hagut un error durant l'anàlisi
             self.engine_info_display.setPlainText("Error durant l'anàlisi de Stockfish.")
             self.engine_info_display.setPlaceholderText("")
         """
         
         if analysis_results is None:
             # Error durant l'anàlisi
             self.engine_info_display.setPlainText("Error durant l'anàlisi de Stockfish.")
             self.engine_info_display.setPlaceholderText("")
             return

         if not analysis_results:
              # No s'ha trobat cap línia (potser mat o posició rara)
              self.engine_info_display.setPlainText("Stockfish no ha trobat cap moviment/línia principal.")
              # Podries intentar mostrar només l'avaluació si està disponible per separat
              # evaluation = self.engine.get_evaluation(self.board.fen()) # Necessitaria mètode addicional
              self.engine_info_display.setPlaceholderText("")
              return


         # --- Formatació de les línies rebudes ---
         formatted_output = []
         requested_depth = 15   # es pot recuperar d'una variable

         for i, line_info in enumerate(analysis_results):
             # Extreu la informació
             move_uci = line_info.get('Move')
             centipawn_eval = line_info.get('Centipawn')
             mate_eval = line_info.get('Mate')
             
             # de moment no va
             # pv_uci_list = line_info.get('PV', []) # Llista de moviments UCI de la variant

             # 1. Formata l'avaluació
             if mate_eval is not None:
                 eval_str = f"Mat en {mate_eval}"
             elif centipawn_eval is not None:
                 # Puntuació relativa al jugador que mou (la llibreria ja ho gestiona?)
                 # Normalment, una puntuació positiva afavoreix les blanques.
                 # Si mouen negres, +100cp és dolent per a elles. Podem ajustar-ho:
                 score = centipawn_eval / 100.0
                 if self.board.turn == chess.BLACK:
                       score = -score # Inverteix el signe si mouen negres
                 eval_str = f"{score:+.2f}" # Afegeix signe explícit
             else:
                 eval_str = "N/A"

             # 2. Intenta convertir el primer moviment a SAN
             best_move_san = move_uci # Fallback
             if move_uci:
                  try:
                       move = self.board.parse_uci(move_uci)
                       best_move_san = self.board.san(move)
                  except ValueError:
                       # Pot passar si el moviment és invàlid per alguna raó o format estrany
                       print(f"Avís: No s'ha pogut parsejar UCI '{move_uci}' a SAN.")
                       best_move_san = move_uci # Mostra UCI
             # PV no disponible
             # 3. Formata la PV (la mostrem en UCI per simplicitat)
             # pv_str = " ".join(pv_uci_list)

             # 4. Construeix la línia de text
             # line_text = f"{i+1}. ({eval_str}) {best_move_san} PV: {pv_str}"
             # Millor format (més semblant a GUIs típiques):
             # line_text = f"{eval_str.rjust(6)} Depth: {requested_depth} -> {best_move_san}  [{pv_str}]"
             line_text = f"{eval_str.rjust(6)} Depth: {requested_depth} -> {best_move_san}"

             formatted_output.append(line_text)

         # Uneix totes les línies formatades i mostra-les
         final_text = "\n".join(formatted_output)
         self.engine_info_display.setPlainText(final_text)
         self.engine_info_display.setPlaceholderText("")
             
        
    def _update_pgn_display(self):
        """Actualitza el quadre de text PGN."""
        # Necessitarem construir el PGN des de l'historial del joc
        # Exemple bàsic (caldria game logic per això):
        # game = chess.pgn.Game.from_board(self.board) # Això no guarda historial correctament
        # pgn_string = str(game)
        pgn_string = f"PGN Historial pendent d'implementar.\nMoviment actual: {self.board.fullmove_number} {'Blanques' if self.board.turn == chess.WHITE else 'Negres'} mouen."
        self.pgn_display.setText(pgn_string)

        
    # --- Slot per gestionar els clics al tauler ---
    @Slot(chess.Square)
    def handle_square_click(self, clicked_square: chess.Square):
        """Gestiona la interacció quan es fa clic a una casella."""
        # print(f"Clic a la casella: {chess.square_name(clicked_square)}")
        self.statusBar().showMessage(f"Casella clicada: {chess.square_name(clicked_square)}")

        piece = self.board.piece_at(clicked_square)

        if self.selected_square is None:
            # --- Primer clic: Seleccionar peça ---
            if piece is not None and piece.color == self.board.turn:
                # Si hi ha una peça del color que mou, la seleccionem
                self.selected_square = clicked_square
                legal_moves = [m for m in self.board.legal_moves if m.from_square == self.selected_square]
                self.chessboard_widget.highlight_legal_moves(self.selected_square, legal_moves)
                print(f"Peça seleccionada a {chess.square_name(clicked_square)}. Moviments legals: {[self.board.san(m) for m in legal_moves]}")
            else:
                # Clic a casella buida o peça rival: neteja selecció visual i lògica
                self.chessboard_widget._clear_highlights()
                self.selected_square = None
                print("Clic a casella buida o peça rival. Deseleccionat.")

        else:
            # --- Segon clic: Intentar moviment ---
            # Hem de verificar si la casella clicada és un moviment legal des de la seleccionada
            move = chess.Move(self.selected_square, clicked_square)
            # TODO: Gestionar promoció (move.promotion = chess.QUEEN, etc.) si és un moviment de peó a última fila

            if move in self.board.legal_moves:
                move_san = self.board.san(move) # Notació algebraica estàndard
                self.board.push(move) # Fes el moviment al tauler lògic
                print(f"Moviment realitzat: {move_san}")
                self.statusBar().showMessage(f"Moviment: {move_san}", 2000) # Mostra per 2 segons
                self._update_board_display() # Actualitza la representació gràfica
                self._update_pgn_display()   # Actualitza el PGN (simplificat ara)
                
            else:
                # Moviment il·legal O clic a una altra peça del mateix color per canviar la selecció
                piece_on_click = self.board.piece_at(clicked_square)
                if piece_on_click is not None and piece_on_click.color == self.board.turn:
                    # Canvia la selecció a la nova peça
                    self.selected_square = clicked_square
                    legal_moves = [m for m in self.board.legal_moves if m.from_square == self.selected_square]
                    self.chessboard_widget.highlight_legal_moves(self.selected_square, legal_moves)
                    print(f"Selecció canviada a {chess.square_name(clicked_square)}. Moviments: {[self.board.san(m) for m in legal_moves]}")
                else:
                    # Clic a una casella que no és moviment legal ni canvi de selecció: deselecciona
                    self.chessboard_widget._clear_highlights()
                    self.selected_square = None
                    print(f"Moviment {chess.square_name(move.from_square)}{chess.square_name(move.to_square)} és il·legal o clic invàlid. Deseleccionat.")
                    self.statusBar().showMessage("Moviment il·legal", 2000)

    def closeEvent(self, event):
         """Atura el fil de Stockfish en tancar l'aplicació."""
         print("Tancant aplicació...")
         if self.stockfish_thread and self.stockfish_thread.isRunning():
              print("Aturant el fil de Stockfish...")
              if self.stockfish_worker:
                   self.stockfish_worker.stop() # Indica al worker que pari (si té bucles llargs)
              self.stockfish_thread.quit() # Demana al bucle d'events del fil que acabi
              if not self.stockfish_thread.wait(1000): # Espera màxim 1 segon
                    print("Avís: El fil de Stockfish no ha acabat correctament.")
              else:
                    print("Fil de Stockfish aturat.")
         event.accept() # Accepta l'event de tancament
    
    @Slot()
    def go_to_start(self):
        print("Slot: Anar al principi")
        self.statusBar().showMessage("Anant al principi...")
        while self.board.move_stack: # Retrocedeix fins l'inici
            self.board.pop()
        self.update_board_display()
        self._update_pgn_display()

    @Slot()
    def go_to_previous_move(self):
        print("Slot: Moviment anterior")
        self.statusBar().showMessage("Moviment anterior...")
        if self.board.move_stack:
             self.board.pop() # Desfés l'últim moviment
             self.update_board_display()
             self._update_pgn_display()
        else:
             self.statusBar().showMessage("Ja s'està al principi", 1500)


    @Slot()
    def go_to_next_move(self):
        # Això només té sentit si has carregat una partida i estàs navegant per ella
        # O si has desfet moviments i vols refer-los (necessita un historial de "redo")
        # Per ara, el deixem sense funcionalitat específica en mode de joc normal
        print("Slot: Moviment següent (funcionalitat per implementar si es navega per partida existent)")
        self.statusBar().showMessage("Moviment següent (no implementat per joc en curs)", 2000)


    @Slot()
    def go_to_end(self):
        # Similar a 'next', útil per navegació de partides carregades
        print("Slot: Anar al final (funcionalitat per implementar si es navega per partida existent)")
        self.statusBar().showMessage("Anar al final (no implementat per joc en curs)", 2000)

    @Slot()
    def reset_board(self):
        print("Slot: Reiniciar tauler")
        self.board.reset() # Reinicia el tauler lògic
        self.statusBar().showMessage("Tauler Reiniciat", 2000)
        self._update_board_display()
        self._update_pgn_display()

    @Slot()
    def flip_board(self):
        # Aquesta funció hauria d'estar idealment DINS de ChessboardWidget,
        # ja que afecta només la VISTA, no la lògica del joc (self.board).
        print("Slot: Girar tauler (passant a ChessboardWidget)")
        self.statusBar().showMessage("Girant el tauler...")
        # Hauries d'implementar un mètode flip() dins de ChessboardWidget
        # if hasattr(self.chessboard_widget, 'flip'):
        #      self.chessboard_widget.flip()
        # else:
        #      print("La funció flip() no està implementada al ChessboardWidget.")
        print("AVÍS: Funció flip() pendent d'implementar a ChessboardWidget")

   
    @Slot()
    def open_pgn_file(self):
        self.statusBar().showMessage("Obrint PGN...")
        # ... (codi igual que abans) ...
        self.selected_square = None # Reseteja selecció en carregar
        self.chessboard_widget._clear_highlights()
        filename, _ = QFileDialog.getOpenFileName(self, "Carregar Partida PGN", "", "Fitxers PGN (*.pgn);;Tots els fitxers (*)")
        if filename:
            self.game_logic.load_pgn(filename)

            # Lògica per llegir el fitxer PGN i carregar la partida
            # Exemple: import chess.pgn
            # try:
            #    with open(file_name) as pgn:
            #        game = chess.pgn.read_game(pgn)
            #        if game:
            #           self.board = game.board() # Carrega la posició inicial
            #           # Aquí guardaries l'historial del joc (game.mainline_moves()) per navegar
            #           self._update_board_display()
            #           self._update_pgn_display() # Podries mostrar el PGN del fitxer
            #           self.statusBar().showMessage(f"PGN carregat: {file_name}", 3000)
            #        else:
            #           QMessageBox.warning(self, "Error PGN", "No s'ha pogut llegir cap partida del fitxer.")
            # except Exception as e:
            #     QMessageBox.critical(self, "Error Obrint PGN", f"Hi ha hagut un error: {e}")

    @Slot()
    def open_bbdd_file(self):
        self.statusBar().showMessage("Obrint BBDD...")
          
    @Slot()
    def save_bbdd(self):
        self.statusBar().showMessage("Guardant BBDD...")    

   

    # --- Slot per canviar a Marró ---
    @Slot()
    def set_board_style_brown(self):
        self.statusBar().showMessage("Aplicant estil de tauler marró...", 2000)
        # Crida a la NOVA funció de chessboard_widget
        self.chessboard_widget.change_square_colors(BROWN_LIGHT_COLOR, BROWN_DARK_COLOR)

        
    # --- Slot per canviar a Blau/Blanc (Default) ---
    @Slot()
    def set_board_style_default(self):
        self.statusBar().showMessage("Aplicant estil de tauler per defecte...", 2000)
        # Crida a la NOVA funció de chessboard_widget amb els colors originals
        self.chessboard_widget.change_square_colors(DEFAULT_LIGHT_COLOR, DEFAULT_DARK_COLOR)

    # --- Slot per canviar Verd/Verd clar
    @Slot()
    def set_board_style_verd(self):
        self.statusBar().showMessage("Aplicant l'estil de tauler verd", 2000)
        # Crida a la NOVA funció de chessboard_widget amb els colors originals
        self.chessboard_widget.change_square_colors(GREEN_LIGHT_COLOR, GREEN_DARK_COLOR)

    # --- NOU Slot GENÈRIC per canviar estil de PECES ---
    @Slot(str, str) # Indiquem que rep dos strings (path, name) - Opcional però bona pràctica
    def set_piece_style(self, piece_dir_path: str, style_name: str):
        """
        Slot genèric que rep el camí al directori de peces i el nom de l'estil.
        """
        self.statusBar().showMessage(f"Aplicant estil de peces {style_name}...", 2000)
        # print(f"Intentant canviar a directori de peces: {piece_dir_path}")
        success = self.chessboard_widget.set_piece_set(piece_dir_path) # Crida a la funció del widget

        if success:
            # SI el directori és vàlid i s'ha canviat, LLAVORS actualitza la pantalla
            self._update_board_display()
        else:
            # Si set_piece_set retorna False (directori invàlid)
            self.statusBar().showMessage(f"Error: No s'ha pogut canviar a l'estil {style_name}. Verifica la carpeta.", 3000)
            QMessageBox.warning(self, "Error d'Estil de Peces",
                                f"No s'ha pogut carregar l'estil '{style_name}'.\n"
                                f"Comprova que la carpeta existeix i conté les imatges SVG:\n{piece_dir_path}")    



# --- Punt d'entrada de l'aplicació ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Comprova que existeixen els directoris abans de continuar
    if not os.path.isdir(ICONS_DIR):
        QMessageBox.warning(None, "Error de Recursos", f"Directori d'icones no trobat:\n{ICONS_DIR}\n"
                            "Algunes icones poden no aparèixer.")

    if debug == "peces":
        if not os.path.isdir(PIECES_BASE_DIR):
            # Atura si les peces no hi són, ja que són essencials
            QMessageBox.critical(None, "Error de Recursos Crític", f"Directori de peces no trobat:\n{PIECES_BASE_DIR}\n"
                              "L'aplicació no pot continuar sense les imatges de les peces.")
            print(pieces_dir)
            print(PIECES_DIR_BERLIN)
            sys.exit(1)


    window = MainWindow()
    window.show()
    sys.exit(app.exec())
