from stockfish import Stockfish
import os

# (La classe UCIMotor pot quedar aquí, però no l'usarem inicialment)
class UCIMotor:
    # ... (el teu codi existent) ...
    pass


class ChessEngine:
    def __init__(self, path_to_stockfish: str):
        if not os.path.exists(path_to_stockfish):
             raise FileNotFoundError(f"El fitxer del motor Stockfish no s'ha trobat a: {path_to_stockfish}")
        try:
            # Pots passar paràmetres inicials aquí si vols
            # self.stockfish = Stockfish(path=path_to_stockfish, depth=10, parameters={"Threads": 2, "Hash": 128})
            self.stockfish = Stockfish(path=path_to_stockfish)
            print(f"Stockfish inicialitzat correctament des de: {path_to_stockfish}")
            print(f"Paràmetres actuals: {self.stockfish.get_parameters()}")
        except Exception as e:
            print(f"Error inicialitzant Stockfish: {e}")
            # Pots llançar l'excepció o manejar-la d'una altra manera
            raise


    # NOU Mètode (o reemplaça get_best_move_and_eval)
    def get_analysis(self, fen: str, depth: int = 15, num_lines: int = 1) -> list | None:
        """
        Obté les 'num_lines' millors línies d'anàlisi per a una posició FEN.
        Cada línia inclou el moviment, l'avaluació i la Variant Principal (PV).
        Retorna una llista de diccionaris o None si hi ha error.
        """
        try:
            self.stockfish.set_fen_position(fen)

            # Configura els paràmetres per aquesta anàlisi específica
            # És IMPORTANT configurar MultiPV ABANS de get_top_moves
            self.stockfish.update_engine_parameters({"MultiPV": num_lines})
            self.stockfish.set_depth(depth) # Estableix la profunditat

            # Obté les millors línies
            top_moves = self.stockfish.get_top_moves(num_lines)

            # --- LÍNIA DE DEPURACIÓ ---
            print("-" * 20)
            print(f"[DEBUG engine_manager] FEN analitzat: {fen}")
            print(f"[DEBUG engine_manager] Resultat de get_top_moves({num_lines}): {top_moves}")
            print("-" * 20)
            # --- FI DEPURACIÓ ---


            if not top_moves:
                print("[engine manager] Stockfish no ha retornat cap línia.")
                return [] # Retorna llista buida en lloc de None per simplificar el maneig

            # El resultat de get_top_moves ja és una llista de diccionaris com:
            # [{'Move': 'e2e4', 'Centipawn': 30, 'Mate': None, 'PV': ['e2e4', 'e7e5', 'g1f3']}, ...]
            return top_moves

        except Exception as e:
            print(f"Error durant l'anàlisi de Stockfish (get_analysis): {e}")
            return None # Indica un error més seriós


    def set_parameters(self, params: dict):
         """Estableix paràmetres al motor Stockfish."""
         self.stockfish.update_engine_parameters(params)
         print(f"Paràmetres de Stockfish actualitzats: {self.stockfish.get_parameters()}")
        

    def get_best_move_and_eval(self, fen: str, depth: int = 10, movetime: int | None = None):
        """
        Calcula el millor moviment i l'avaluació per a una posició FEN donada.
        Retorna un diccionari {'best_move': str, 'evaluation': dict} o None si hi ha error.
        """
        try:
            self.stockfish.set_fen_position(fen)

            # --- MANERA CORRECTA d'establir paràmetres ABANS de calcular ---
            # Opcional: Estableix paràmetres que vulguis per a aquest càlcul
            # self.stockfish.set_depth(depth)
            # Pots afegir altres com self.stockfish.set_skill_level(10), etc.

            # Utilitza movetime SI es proporciona, sinó usa depth (ajusta segons preferència)
            if movetime:
                 best_move = self.stockfish.get_best_move_time(movetime)
            else:
                 # Per usar depth, estableix-la abans i fes servir get_best_move
                 self.stockfish.set_depth(depth)
                 best_move = self.stockfish.get_best_move() # Aquesta trucada usarà el depth configurat

            if best_move is None:
                print("Stockfish no ha retornat cap moviment.")
                return None # O una altra indicació d'error

            evaluation = self.stockfish.get_evaluation()

            return {
                "best_move": best_move,
                "evaluation": evaluation # Aquest ja és un diccionari {'type': 'cp'/'mate', 'value': ...}
            }
        except Exception as e:
            print(f"Error durant l'anàlisi de Stockfish: {e}")
            return None

        
    
   
