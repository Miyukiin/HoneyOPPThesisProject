import random
from typing import List
from Levenshtein import distance as levenshtein_distance  # Requires python-Levenshtein package
import numpy as np

class PasswordGeneration:
    def __init__(self, threshold_levenshtein: int, threshold_euclidean: float, sugarword: str):
        self.threshold_levenshtein = threshold_levenshtein
        self.threshold_euclidean = threshold_euclidean
        self.sugarword = sugarword
        
        # Define keyboard layout positions (x, y)
        self.keyboard_layout = {
            'q': (0, 0), 'w': (1, 0), 'e': (2, 0), 'r': (3, 0), 't': (4, 0), 'y': (5, 0), 'u': (6, 0), 'i': (7, 0), 'o': (8, 0), 'p': (9, 0),
            'a': (0, 1), 's': (1, 1), 'd': (2, 1), 'f': (3, 1), 'g': (4, 1), 'h': (5, 1), 'j': (6, 1), 'k': (7, 1), 'l': (8, 1),
            'z': (0, 2), 'x': (1, 2), 'c': (2, 2), 'v': (3, 2), 'b': (4, 2), 'n': (5, 2), 'm': (6, 2),
            ' ': (0, 3)  # Space character for completeness
        }

    def generate_sweetwords(self, password: str) -> List[str]:
        sweetwords = []
        for _ in range(5):  # Generate 5 sweetwords
            tail = str(random.randint(100, 999))  # Random tail for demonstration
            sweetword = f"{password}{tail}"  # Combine password with tail
            sweetwords.append(sweetword)
        return sweetwords

    def euclidean_distance(self, char1: str, char2: str) -> float:
        # Get positions from keyboard layout
        pos1 = self.keyboard_layout.get(char1.lower(), (0, 0))
        pos2 = self.keyboard_layout.get(char2.lower(), (0, 0))
        # Calculate Euclidean distance
        return np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def assess_passwords(self, password: str) -> List[str]:
        sweetwords = self.generate_sweetwords(password)
        valid_sweetwords = []
        
        for sweetword in sweetwords:
            lev_dist = levenshtein_distance(password, sweetword)
            euc_dist = sum(self.euclidean_distance(c1, c2) for c1, c2 in zip(password, sweetword))
            
            if lev_dist <= self.threshold_levenshtein and euc_dist <= self.threshold_euclidean:
                valid_sweetwords.append(sweetword)
        
        return valid_sweetwords
