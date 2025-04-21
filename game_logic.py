# core/game_logic.py
import chess
import chess.pgn
from PySide6.QtCore import QObject, Signal

class GameLogic(QObject):
    """
    Gestiona l'estat del joc d'escacs (Model).
    Conté el tauler de python-chess i la lògica de validació/execució.
    """
    board_changed = Signal() # Senyal emès quan el tauler canvia
    game_over = Signal(str)  # Senyal emès quan la partida acaba (amb el resultat)
    move_made = Signal(chess.Move, str) # Senyal emès després de fer un moviment (moviment, san)

    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self._game = chess.pgn.Game() # Per guardar la partida
        self._game.setup(self.board)
        self._current_node = self._game # Node actual per replay PGN

    def reset(self):
        """Reinicia el tauler a la posició inicial."""
        self.board.reset()
        self._game = chess.pgn.Game()
        self._game.setup(self.board)
        self._current_node = self._game
        print("Tauler reiniciat.")
        self.board_changed.emit()

    def get_legal_moves(self, square: chess.Square) -> list[chess.Move]:
        """Retorna els moviments legals des d'una casella donada."""
        return [move for move in self.board.legal_moves if move.from_square == square]

    def make_move(self, move: chess.Move) -> bool:
        """
        Intenta fer un moviment. Retorna True si és legal i s'ha fet, False altrament.
        Gestiona la promoció (per defecte a Reina si no s'especifica).
        """
        # Comprova si el moviment és potencialment una promoció
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            target_rank = chess.square_rank(move.to_square)
            is_promotion = (piece.color == chess.WHITE and target_rank == 7) or \
                           (piece.color == chess.BLACK and target_rank == 0)
            # Si és promoció però no s'ha especificat la peça, posa Reina per defecte
            # El controlador hauria d'interceptar això i demanar a l'usuari
            if is_promotion and move.promotion is None:
                print("Avís: Promoció detectada, seleccionant Reina per defecte.")
                move.promotion = chess.QUEEN

        if move in self.board.legal_moves:
            san = self.board.san(move) # Obté la notació abans de fer el push
            self.board.push(move)
            # Actualitza el joc PGN
            self._current_node = self._current_node.add_variation(move)
            print(f"Moviment realitzat: {san}")
            self.move_made.emit(move, san) # Emet senyal amb el moviment i SAN
            self.check_game_over()
            self.board_changed.emit() # Notifica que el tauler ha canviat
            return True
        else:
            print(f"Moviment il·legal: {move.uci()}")
            return False

    def check_game_over(self):
        """Comprova si la partida ha acabat i emet el senyal corresponent."""
        result = None
        if self.board.is_checkmate():
            result = f"Escac i mat! Guanyen {'negres' if self.board.turn == chess.WHITE else 'blanques'} ({self.board.result()})"
        elif self.board.is_stalemate():
            result = f"Ofegat! Taules ({self.board.result()})"
        elif self.board.is_insufficient_material():
            result = f"Material insuficient! Taules ({self.board.result()})"
        elif self.board.can_claim_draw():
            # Això inclou la regla dels 50 moviments i la triple repetició
            # En una app real, es podria donar l'opció de reclamar les taules
            result = f"Taules per regla (50 mov/repetició) ({self.board.result()})"

        if result:
            print(f"Partida acabada: {result}")
            self.game_over.emit(result)

    def undo_move(self) -> bool:
        """Desfà l'últim moviment."""
        if self.board.move_stack:
            try:
                # Desfà al tauler
                self.board.pop()
                # Mou el node actual del PGN al pare
                if self._current_node.parent:
                     # Important: Elimina la variació que es va afegir
                    move_to_remove = self._current_node.move
                    parent_node = self._current_node.parent
                    parent_node.remove_variation(move_to_remove)
                    self._current_node = parent_node
                print("Moviment desfet.")
                self.check_game_over() # L'estat pot canviar
                self.board_changed.emit()
                return True
            except IndexError: # Pot passar si l'stack està buit inesperadament
                print("Error: No es pot desfer el moviment.")
                return False
        else:
            print("No hi ha moviments per desfer.")
            return False

    # --- Mètodes per PGN (inicials) ---
    def load_pgn(self, filename: str):
        """Carrega el primer joc d'un fitxer PGN."""
        try:
            with open(filename, 'r') as pgn_file:
                game = chess.pgn.read_game(pgn_file)
                if game:
                    self._game = game
                    self.board = self._game.board() # Comença al principi
                    # Navega fins a la posició inicial si hi ha moviments
                    for move in self._game.mainline_moves():
                        self.board.push(move)
                    # Situa el node actual al final de la línia principal
                    self._current_node = self._game.end()
                    # Opcionalment, podries anar al principi per replay:
                    # self.board = self._game.board()
                    # self._current_node = self._game
                    print(f"PGN carregat: {filename}")
                    self.board_changed.emit()
                    # Emetre senyals per actualitzar la llista de moviments, etc.
                else:
                    print(f"Error: No s'ha pogut llegir cap partida del PGN: {filename}")
        except FileNotFoundError:
            print(f"Error: Fitxer PGN no trobat: {filename}")
        except Exception as e:
            print(f"Error en carregar PGN: {e}")

    def save_pgn(self, filename: str):
        """Guarda la partida actual en un fitxer PGN."""
        try:
            # Afegir capçaleres estàndard (pots personalitzar-les)
            self._game.headers["Event"] = "Partida Casual"
            self._game.headers["Site"] = "Aplicació Escacs PySide6"
            # ... altres capçaleres ...
            with open(filename, 'w') as pgn_file:
                exporter = chess.pgn.FileExporter(pgn_file)
                self._game.accept(exporter)
            print(f"Partida guardada a: {filename}")
        except Exception as e:
            print(f"Error en guardar PGN: {e}")

    # --- Mètodes per Replay (inicials) ---
    def go_to_start(self):
        """Va a la posició inicial de la partida carregada."""
        if self._game:
            self.board = self._game.board()
            self._current_node = self._game
            self.board_changed.emit()

    def go_to_end(self):
        """Va a la posició final de la partida carregada."""
        if self._game:
            # Refés tots els moviments des de la posició actual
            node = self._current_node
            while not node.is_end():
                 next_node = node.variation(0) # Pren la línia principal
                 if not next_node: break
                 self.board.push(next_node.move)
                 node = next_node
            self._current_node = node # Actualitza el node actual
            self.board_changed.emit()


    def next_move(self):
        """Avança un moviment en el replay."""
        if self._current_node and not self._current_node.is_end():
            # Pren la primera variació (línia principal per defecte)
            next_node = self._current_node.variation(0)
            if next_node:
                self.board.push(next_node.move)
                self._current_node = next_node
                self.board_changed.emit()
                # Emetre senyal per ressaltar el moviment a la llista?

    def previous_move(self):
        """Retrocedeix un moviment en el replay (equivalent a undo)."""
        # Per a replay, és millor desfer des del tauler associat al node pare
        if self._current_node and self._current_node.parent:
            self._current_node = self._current_node.parent
            # Crea un nou tauler a partir de la posició FEN del node pare
            # Això evita problemes si s'ha jugat després de carregar un PGN
            fen = self._current_node.board().fen()
            self.board.set_fen(fen)
            self.board_changed.emit()
            # O més simple si només fem replay sense jugar:
            # self.undo_move() # Reutilitza la lògica de desfer
