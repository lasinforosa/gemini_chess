# src.chessboard_widget.py
import os
import chess
from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                               QGraphicsPixmapItem, QGraphicsItem)
from PySide6.QtGui import QColor, QBrush, QPen, QPixmap, QMouseEvent, QPainter
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from helpers import SQUARE_SIZE, square_to_coords, coords_to_square, piece_to_filename


class ChessboardWidget(QGraphicsView):
    """
    Widget per mostrar el tauler d'escacs i gestionar la interacció bàsica.
    Utilitza QGraphicsScene per dibuixar les caselles i les peces.
    """
    square_clicked = Signal(chess.Square) # Senyal emès quan es clica una casella
    
    def __init__(self, resources_path: str, parent=None):
        """
        Inicialitza el widget del tauler.

        Args:
            resources_path (str): La ruta absoluta al directori que conté les
                                  imatges de les peces (ex: ".../resources/pieces").
            parent: El widget pare (opcional).
        """
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # --- VERIFICACIÓ INICIAL ---
        # És una bona idea comprovar que la ruta inicial existeix
        if not os.path.isdir(resources_path):
             # Llançar un error és millor que continuar i fallar més tard
             raise FileNotFoundError(f"El directori de recursos inicial '{resources_path}' no existeix.")

        # Guarda la ruta als recursos (ara és obligatòria)
        self.resources_dir = resources_path
        print(f"ChessboardWidget inicialitzat amb resources_dir: {self.resources_dir}") # Per depuració

        
        # Configuració de la vista
        board_dimension = SQUARE_SIZE * 8
        self.setMinimumSize(board_dimension, board_dimension)
        self.setMaximumSize(board_dimension, board_dimension) # Comenta o ajusta si vols que sigui redimensionable
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Treiem els hints de renderitzat si causen problemes, sinó deixa'ls
        self.setRenderHint(QPainter.RenderHint.Antialiasing) # Millora aspecte (opcional)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform) # Millora aspecte peces

        # Estat intern
        # Estat intern
        self._board_items = []
        self._piece_items = {}
        self._highlight_squares = []
        
        # DARRERA MODIFICACIO GEMINI
        # ---------------------------
        # self._board_items: list[QGraphicsRectItem] = []             # Items de les caselles
        # self._piece_items: dict[chess.Square, QGraphicsPixmapItem] = {} # Items de les peces (mapa casella -> item)
        # selected_square ara es gestiona a MainWindow, el widget només mostra highlights
        # self._selected_square: chess.Square | None = None           # Casella seleccionada actualment
        # self._highlight_squares: list[QGraphicsRectItem] = []       # Items de ressaltat

        # Dibuixa el tauler inicial
        self._draw_board()


    def change_square_colors(self, light_color: QColor, dark_color: QColor):
        """
        Canvia el color de les caselles existents sense eliminar-les ni les peces.
        """
        if not self._board_items:
            print("Avís: S'ha intentat canviar colors però no hi ha caselles (_board_items buit).")
            return

        # print(f"Canviant colors a Light={light_color.name()}, Dark={dark_color.name()}") # Per depurar

        # Recorre totes les caselles gràfiques que vam crear a _draw_board
        for i, item in enumerate(self._board_items):
            if isinstance(item, QGraphicsRectItem): # Assegura't que és una casella
                # Determina si la casella hauria de ser clara o fosca
                # Podem refer el càlcul basat en l'índex (0-63)
                square_index = i # Suposant que _board_items es guarda en ordre 0..63
                rank = chess.square_rank(square_index)
                file = chess.square_file(square_index)

                is_dark = (rank + file) % 2 != 0 # ATENCIÓ: ajusta la lògica si a _draw_board era == 0
                # Comprova la lògica a _draw_board: color = dark_color if (rank + file) % 2 == 0 else light_color
                # Per tant, si (rank+file)%2 == 0 ÉS FOSC. La línia is_dark hauria de ser:
                # is_dark = (rank + file) % 2 == 0

                actual_color = light_color if is_dark else dark_color
                item.setBrush(QBrush(actual_color)) # Estableix el nou color de fons

            # Pot ser útil forçar una actualització visual, encara que sovint no és necessari
            self.viewport().update()

    # Opcionalment, pots fer que _draw_board també guardi rank/file a cada item
    # i així recuperar-los aquí de forma més robusta, però amb el càlcul
    # basat en 'i' sol ser suficient si no canvies l'ordre de _board_items.


    def set_piece_set(self, new_resources_dir: str):
        """
        Actualitza el directori on es buscaran les imatges de les peces.
        Verifica que el directori existeix abans de canviar-lo.
        NO redibuixa el tauler automàticament. Això s'ha de fer després
        cridant a update_board.
        """
        if not os.path.isdir(new_resources_dir):
            print(f"Error: El directori de peces especificat no existeix: '{new_resources_dir}'")
            # Podries mostrar un QMessageBox aquí si vols informar l'usuari
            # o simplement no fer el canvi.
            return False # Indica que el canvi no s'ha fet

        # print(f"Canviant el directori de recursos de peces a: {new_resources_dir}")
        self.resources_dir = new_resources_dir # <<--- AQUEST ÉS EL CANVI CLAU
        return True # Indica que el canvi s'ha fet
    
        
    def _draw_board(self):
        """Dibuixa les caselles del tauler (sense peces)."""
        self.scene.clear() # Neteja l'escena completament
        self._board_items = []
        self._piece_items = {}
        self._highlight_squares = []
        self._selected_square = None

        # Defineix els colors PREDETERMINATS aquí (per quan s'inicia)
        default_light_color = QColor("#FFFFFF") # Blanc original
        default_dark_color = QColor("#7388B6")  # Blau original
        
        for rank in range(8):
            for file in range(8):
                square_index = chess.square(file, rank)
                x, y = square_to_coords(square_index)
                color = default_light_color if (rank + file) % 2 == 0 else default_dark_color 

                rect = QGraphicsRectItem(x, y, SQUARE_SIZE, SQUARE_SIZE)
                rect.setBrush(QBrush(color))
                rect.setPen(QPen(Qt.PenStyle.NoPen)) # Sense vores per a les caselles
                self.scene.addItem(rect)
                self._board_items.append(rect)

        # Assegura que la vista estigui ajustada a l'escena
        self.setSceneRect(0, 0, SQUARE_SIZE * 8, SQUARE_SIZE * 8)

        
    def update_board(self, board: chess.Board):
        """
        Actualitza la posició de les peces al tauler gràfic segons l'estat
        del tauler de python-chess proporcionat.
        """
        # 1. Esborra les peces gràfiques anteriors
        for item in self._piece_items.values():
            if item.scene() == self.scene:
                self.scene.removeItem(item)
        self._piece_items.clear()

        
        # 2. Col·loca les peces noves segons el 'board'
        for square, piece in board.piece_map().items():
            filename = piece_to_filename(piece)
            filepath = os.path.join(self.resources_dir, filename)

            # --- IMPRESSIÓ DE DEPURACIÓ ---
            # print(f"Intentant carregar peça des de: {filepath}")
            # -------------------------------

            if os.path.exists(filepath):
                pixmap_original = QPixmap(filepath)
                if pixmap_original.isNull():
                    print(f"Avís: QPixmap és nul després de carregar: {filepath}")
                    continue             

                # Escala la imatge a la mida de la casella mantenint la relació d'aspecte
                scaled_pixmap = pixmap_original.scaled(SQUARE_SIZE, SQUARE_SIZE,
                                              Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                item = QGraphicsPixmapItem(scaled_pixmap)

                # Calcula la posició per centrar la peça dins la casella
                x, y = square_to_coords(square)
                offset_x = (SQUARE_SIZE - scaled_pixmap.width()) / 2
                offset_y = (SQUARE_SIZE - scaled_pixmap.height()) / 2
                item.setPos(x + offset_x, y + offset_y)

                # Emmagatzema la casella a l'ítem per identificar-lo posteriorment
                item.setData(0, square)
                # Assegura que les peces es dibuixin sobre les caselles i ressaltats
                item.setZValue(1.0)

                self.scene.addItem(item)
                self._piece_items[square] = item
            else:
                # --- AVIS SI NO TROBA EL FITXER ---
                print(f"Avís: No s'ha trobat la imatge per a la peça: {filepath}")
                # ----------------------------------

        # Esborra qualsevol ressaltat que pogués quedar
        self._clear_highlights()
        # self._selected_square = None # Normalment no volem deseleccionar en actualitzar

    def mousePressEvent(self, event: QMouseEvent):
        """Gestiona els clics del ratolí per seleccionar/deseleccionar caselles i intentar moviments."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint()) # Posició dins l'escena
            clicked_square = coords_to_square(scene_pos.x(), scene_pos.y())

            if clicked_square is not None:
                # Sempre emetem el clic, el controlador decidirà què fer
                self.square_clicked.emit(clicked_square)
                # Ja no gestionem la selecció ni l'intent de moviment aquí
               
                # piece_on_clicked_square = clicked_square in self._piece_items # Comprova si hi ha una peça gràfica

                # if self._selected_square is None:
                #     # PRIMER CLIC (o clic sense selecció prèvia)
                #     if piece_on_clicked_square:
                #         # Si hi ha una peça a la casella clicada, la seleccionem
                #         # (El controlador hauria de verificar si és el torn del jugador)
                #         # Ara només gestionem la part visual de la selecció
                #         # self._selected_square = clicked_square
                #         # self._highlight_square(clicked_square, QColor(0, 255, 0, 100)) # Ressaltat origen (millor fer-ho des del controlador)
                #         pass # Deixem que el controlador cridi a highlight_legal_moves si cal
                #     else:
                #         # Clic en casella buida sense selecció prèvia: no fem res visualment aquí
                #          self._clear_highlights() # Neteja qualsevol ressaltat previ
                # else:
                #     # SEGON CLIC (ja hi ha una peça seleccionada)
                #     if self._selected_square == clicked_square:
                #         # Clic a la mateixa casella seleccionada: Deseleccionar
                #         self._clear_highlights()
                #         self._selected_square = None
                #     else:
                #         # Clic a una altra casella: Intent de moviment
                #         from_sq = self._selected_square
                #         to_sq = clicked_square
                #         move = chess.Move(from_sq, to_sq)

                #         # La lògica de promoció (per exemple, afegir .promotion = chess.QUEEN)
                #         # és millor gestionar-la al controlador (MainWindow) abans
                #         # de cridar a game_logic.make_move, ja que pot requerir un diàleg.
                #         # Aquí només creem el moviment bàsic i l'emetem.

                #         self.move_attempted.emit(move)

                #         # Després de l'intent (sigui vàlid o no), netegem la selecció visual.
                #         # El controlador actualitzarà el tauler si el moviment és vàlid.
                #         self._clear_highlights()
                #         self._selected_square = None # Reseteja la selecció visual

        # Propaga l'event per si altres parts del sistema el necessiten
        super().mousePressEvent(event)


    def _highlight_square(self, square: chess.Square, color: QColor):
        """Ressalta una casella específica amb un color."""
        x, y = square_to_coords(square)
        rect = QGraphicsRectItem(x, y, SQUARE_SIZE, SQUARE_SIZE)
        rect.setBrush(QBrush(color))
        rect.setPen(QPen(Qt.PenStyle.NoPen))
        # ZValue: 0=caselles, 0.5=ressaltats, 1=peces
        rect.setZValue(0.5)
        self.scene.addItem(rect)
        self._highlight_squares.append(rect)


    def highlight_legal_moves(self, origin_square: chess.Square, legal_moves: list[chess.Move]):
        """
        Neteja ressaltats anteriors i ressalta l'origen i els destins legals.
        Ja NO gestiona _selected_square.
        """
        self._clear_highlights()
        # self._selected_square = origin_square # -> Elimina o comenta aquesta línia

        highlight_origin_color = QColor(90, 170, 90, 180)
        self._highlight_square(origin_square, highlight_origin_color)

        highlight_dest_color = QColor(30, 100, 180, 100)
        highlight_capture_color = QColor(180, 50, 50, 100)

        # Determina les caselles de destinació on hi ha peces per pintar captures
        destination_squares_with_pieces = {
            sq for sq, item in self._piece_items.items() if item is not None
        }

        for move in legal_moves:
            if move.from_square == origin_square:
                 # is_capture = move.to_square in self._piece_items # Això pot ser imprecís si update_board no s'ha executat
                 # Millor comprovar-ho amb la lògica del joc si fos necessari,
                 # però per ara podem pintar diferent si hi ha una peça *gràfica* allà.
                 is_capture_visual = move.to_square in destination_squares_with_pieces
                 dest_color = highlight_capture_color if is_capture_visual else highlight_dest_color
                 self._highlight_square(move.to_square, dest_color)


    def _clear_highlights(self):
        """Elimina tots els rectangles de ressaltat de l'escena."""
        for item in self._highlight_squares:
            if item.scene() == self.scene: # Comprova si encara està a l'escena
                self.scene.removeItem(item)
        self._highlight_squares.clear()
        # Important: NO resetejem self._selected_square aquí, només els rectangles visuals.
        # La gestió de _selected_square es fa a mousePressEvent.
        # Ja no gestionem _selected_square aquí
