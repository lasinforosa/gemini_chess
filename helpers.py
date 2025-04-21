# src/helpers.py
import chess
import os
from PySide6.QtGui import QColor


SQUARE_SIZE = 50  # Mida de cada casella en píxels (pots ajustar-ho)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
pieces_dir = os.path.join(BASE_DIR, "pieces", "berlin")
marro_b = QColor("#F0D9B5") # estil marro
marro_n = QColor("#B58863")  
blau_b = QColor("#FFFFFF") # estil blau
blau_n = QColor("#7388B6")  
light_color = blau_b
dark_color = blau_n

def square_to_coords(square: chess.Square) -> tuple[float, float]:
    """Converteix un índex de casella (0-63) a coordenades (x, y) per QGraphicsScene."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    # QGraphicsScene té l'origen (0,0) a dalt a l'esquerra
    # Els escacs tenen a1 a baix a l'esquerra
    x = file * SQUARE_SIZE
    y = (7 - rank) * SQUARE_SIZE
    return x, y

def coords_to_square(x: float, y: float) -> chess.Square | None:
    """Converteix coordenades (x, y) de QGraphicsScene a un índex de casella (0-63)."""
    if x < 0 or x >= 8 * SQUARE_SIZE or y < 0 or y >= 8 * SQUARE_SIZE:
        return None # Fora del tauler
    file = int(x // SQUARE_SIZE)
    rank = 7 - int(y // SQUARE_SIZE)
    return chess.square(file, rank)

def piece_to_filename(piece: chess.Piece) -> str:
    """Converteix un objecte chess.Piece al nom de fitxer de la imatge SVG."""
    color = 'w' if piece.color == chess.WHITE else 'b'
    ptype = piece.symbol().lower()
    return f"{color}{ptype}.svg"
