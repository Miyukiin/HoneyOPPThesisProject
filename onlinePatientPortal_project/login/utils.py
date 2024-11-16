import random
from Levenshtein import distance as levenshtein_distance  # Requires python-Levenshtein package
from django.http import JsonResponse
import numpy as np
from nltk.corpus import wordnet as wn
import string
from pathlib import Path
from django.conf import settings
import requests
import math
import textdistance

# Run only Once
#import nltk 
#nltk.download('wordnet')
    
class ProposedPasswordGeneration:
    def __init__(self, password: str):
        self.threshold_levenshtein:int = 3
        self.threshold_euclidean:float = 3.0
        
        self.password:str = password
        self.num_of_honeywords:int = 5 # How many honeywords to be generated? E.g 5 honeywords -> 4 sweet words, 1 sugar word.

        self.alphabet_upper_list = list(string.ascii_uppercase)
        self.alphabet_lower_list = list(string.ascii_lowercase)
        self.symbol_list = list(string.punctuation)
        self.digit_list =  list(string.digits)
        self.honeyword_list:list[str] = []
        self.capital_indexes:list[int] = []

        # Define keyboard layout positions (x, y) by row for QWERTY keyboard
        self.keyboard_layout = {
            # Row 1: Top row (Numbers and symbols)
            '`': (-1, 0),'1': (0, 0), '2': (1, 0), '3': (2, 0), '4': (3, 0), '5': (4, 0), '6': (5, 0), '7': (6, 0), '8': (7, 0), '9': (8, 0), '0': (9, 0), '-': (9, 0), '=': (10, 0),
            '~': (-1, 0),'!': (0, 0), '@': (1, 0), '#': (2, 0), '$': (3, 0), '%': (4, 0), '^': (5, 0), '&': (6, 0), '*': (7, 0), '(': (8, 0), ')': (9, 0), '_': (9, 0), '+': (10, 0),
            
            # Row 2: QWERTY row
            'q': (0, 1), 'w': (1, 1), 'e': (2, 1), 'r': (3, 1), 't': (4, 1), 'y': (5, 1), 'u': (6, 1), 'i': (7, 1), 'o': (8, 1), 'p': (9, 1), '[': (10, 1), ']': (11, 1), '\\': (12, 1),
            'Q': (0, 1), 'W': (1, 1), 'E': (2, 1), 'R': (3, 1), 'T': (4, 1), 'Y': (5, 1), 'U': (6, 1), 'I': (7, 1), 'O': (8, 1), 'P': (9, 1), '{': (10, 1), '}': (11, 1), '|': (12, 1),
            
            # Row 3: Home row
            'a': (0, 2), 's': (1, 2), 'd': (2, 2), 'f': (3, 2), 'g': (4, 2), 'h': (5, 2), 'j': (6, 2), 'k': (7, 2), 'l': (8, 2), ';': (9, 2), "'": (10, 2),
            'A': (0, 2), 'S': (1, 2), 'D': (2, 2), 'F': (3, 2), 'G': (4, 2), 'H': (5, 2), 'J': (6, 2), 'K': (7, 2), 'L': (8, 2), ':': (9, 2), '"': (10, 2),
            
            # Row 4: Bottom row
            'z': (0, 3), 'x': (1, 3), 'c': (2, 3), 'v': (3, 3), 'b': (4, 3), 'n': (5, 3), 'm': (6, 3), ',': (7, 3), '.': (8, 3), '/': (9, 3),
            'Z': (0, 3), 'X': (1, 3), 'C': (2, 3), 'V': (3, 3), 'B': (4, 3), 'N': (5, 3), 'M': (6, 3), '<': (7, 3), '>': (8, 3), '?': (9, 3),
        }
    
    # Tokenize into Letters, Digits and Symbols. Replace with Appropriate. Assess Euclidean and Levensh, Return.
    
    def tokenize(self) -> tuple[int, list[dict]]: # L3GendtyouSer4!rE4l2%7*   
        before_password = self.password
        token_list = [] # Letters, Numbers, Symbols
        lexeme_string = ""
        type = "empty"
        
        capital_index = []
        # Get the indexes where the capitalization occurs.
        for i in range(len(before_password)): 
            if before_password[i].isupper():
                capital_index.append(i)
        
        lowercase_password = before_password.lower() # l3gendtyouser4!re4l2%7*

        # Parse the password and tokenize
        for i in range(len(lowercase_password)): 
            if lowercase_password[i].isalpha():
                lexeme_string += lowercase_password[i]
                if type == "empty": # if it is the first character of the string, just set the type and go next.
                    type = "String"
                elif i == (len(lowercase_password)-1): # We have reached the last character of the password.
                    token_list.append({lexeme_string:"Letters"})
                    lexeme_string, type = "", ""
            elif lowercase_password[i].isnumeric():
                if len(lexeme_string) >= 1 and lexeme_string.isalpha(): # We have a lexeme_string of alphabetic characters, and we reached a digit.
                    token_list.append({lexeme_string:"Letters"})
                    lexeme_string, type = lowercase_password[i], "Digit"
                else: # Handle digit case.
                    lexeme_string, type = lowercase_password[i], "Digit"
                token_list.append({lexeme_string:type})
                lexeme_string, type = "", ""
            elif lowercase_password[i] in string.punctuation:
                if len(lexeme_string) >= 1 and lexeme_string.isalpha(): # We have a lexeme_string of alphabetic characters, and we reached a Symbol.
                    token_list.append({lexeme_string:"Letters"})
                    lexeme_string, type = lowercase_password[i], "Symbol"
                else: # Handle symbol case
                    lexeme_string, type = lowercase_password[i], "Symbol" 
                token_list.append({lexeme_string:type})
                lexeme_string, type = "", ""

        return capital_index, token_list
    
    def assemble_honey_password(self, token_list:list[dict]) -> str:
        def generate_replacement_word_same_length(word):
            word_length = len(word)
            synonyms = set()
            
            for synset in wn.all_synsets():
                for lemma in synset.lemmas():
                    lemma_name = lemma.name()
                    # Only add single words (no underscores) of the same length as the input word
                    if len(lemma_name) == word_length and '_' not in lemma_name:
                        synonyms.add(lemma_name)
            
            # Return a random word from the list if available
            return random.choice(list(synonyms)) if synonyms else None
        
        def generate_replacement_word_factor(word):
            """
            Generates a replacement word derived from factors of original word length.
            
            Parameters:
            - word: original word
            
            Returns:
            - A replacement word that is a combination of the two words whose length is a pair of factor of the original word.
            """
            def find_all_factors(n):
                """Finds all factors of n, excluding 1 and n itself."""
                factors = []
                for i in range(1, int(n**0.5) + 1):
                    if n % i == 0:
                        factors.append(i)
                        if i != n // i:
                            factors.append(n // i)
                return sorted(factors)

            def find_words_of_length(length):
                """Finds all single words (no underscores) of a specific length from WordNet."""
                words = [lemma.name() for synset in wn.all_synsets() for lemma in synset.lemmas()
                        if len(lemma.name()) == length and '_' not in lemma.name()]
                return words
            
            word_length = len(word)
            factors = find_all_factors(word_length)
            
            # Generate pairs of factors whose product equals the word length
            factor_pairs = [(f1, f2) for i, f1 in enumerate(factors) for f2 in factors[i:] if f1 * f2 == word_length]
            selected_factor_pair = random.choice(factor_pairs)
            
            # Try to find words of these lengths and combine them
            # If prime number e.g 1 x 11. Return original length.
            if selected_factor_pair[0] == 1:
                words = find_words_of_length(selected_factor_pair[1]) # Get original length possible words
                return random.choice(words)
            else:
                words1 = find_words_of_length(selected_factor_pair[0])
                words2 = find_words_of_length(selected_factor_pair[1])
                
            if words1 and words2:
                word1 = random.choice(words1)
                word2 = random.choice(words2)
                combined_word = word1 + word2
                return combined_word

            # Return None if no valid combination is found
            return None
        
        def to_leetspeak(word):
            # Define leetspeak mapping
            leet_mapping = {
                'A': '4', 'a': '4',
                'E': '3', 'e': '3',
                'I': '1', 'i': '1',
                'O': '0', 'o': '0',
                'S': '5', 's': '5',
                'T': '7', 't': '7',
                'L': '1', 'l': '1'
            }
            
            # Convert the word to leetspeak with random replacements
            leet_word = []
            for char in word:
                chance = (random.randint(0, 100) / 100)
                if char in leet_mapping and chance <= 0.1:
                    leet_word.append(leet_mapping[char])  # Replace with leetspeak equivalent
                else:
                    leet_word.append(char)  # Keep the original character
            
            # Join the list into a final leetspeak word
            return ''.join(leet_word)
        
        def generate_replacement_char(original_char:str, choice_list:list) -> str:
            """
            Generates a replacement character from choice_list based on proximity
            to the original character in terms of Euclidean distance.
            
            Parameters:
            - original_char: The original character to replace.
            - choice_list: List of potential replacement characters.
            
            Returns:
            - A replacement character within the threshold Euclidean distance.
            """
            def get_euclidean_distance_2d(replacement_char_coor:tuple, original_char_coor:tuple) -> str:
                """
                Calculate the Euclidean distance between two 2D points.
                
                Parameters:
                - replacement_char: tuple or list with two coordinates (x1, y1)
                - original_char: tuple or list with two coordinates (x2, y2)
                
                Returns:
                - The Euclidean distance between replacement_char and original_char.
                """
                
                if len(replacement_char_coor) != 2 or len(original_char_coor) != 2:
                    raise ValueError("Both points must have exactly two coordinates for 2D distance")
                
                # Calculate the squared differences and then the square root of the sum
                distance = math.sqrt((original_char_coor[0] - replacement_char_coor[0]) ** 2 + (original_char_coor[1] - replacement_char_coor[1]) ** 2)
                return distance
            
            if original_char not in self.keyboard_layout:
                raise ValueError("Original character is not in the keyboard layout")

            original_pos = self.keyboard_layout[original_char]

            while True:
                replacement_char = random.choice(choice_list)
                
                # Ensure the replacement character is in the layout
                if replacement_char in self.keyboard_layout:
                    replacement_pos = self.keyboard_layout[replacement_char]
                    
                    # Calculate the Euclidean distance
                    replacement_char_euc_distance = get_euclidean_distance_2d(replacement_pos, original_pos)
                    
                    if replacement_char_euc_distance > self.threshold_euclidean:
                        return replacement_char
        
        def restore_capitalization(honey_password_candidate:str) -> str:
            capitalized_honey_password_candidate = ''
            for i in range (len(honey_password_candidate)):
                try:
                    if i in self.capital_indexes:
                        capitalized_honey_password_candidate += honey_password_candidate[i].upper()
                    else:
                        capitalized_honey_password_candidate += honey_password_candidate[i]
                except:
                    capitalized_honey_password_candidate += honey_password_candidate[i]
            
            return capitalized_honey_password_candidate
                
        candidate_honey_token_list = []
        
        for token in token_list:
            for chars, char_type in token.items():
                chance:float = (random.randint(0,100) / 100)
                if chance <= 0.1 and len(chars) <=4:
                    candidate_honey_token_list.append(chars)
                elif char_type == "Letters":
                    if len(chars) == 1:
                        replacement_char:str = generate_replacement_char(chars, self.alphabet_lower_list)
                        candidate_honey_token_list.append(replacement_char)
                    elif len(chars) > 1:
                        replacement_word:str = generate_replacement_word_same_length(chars)
                        replacement_word = replacement_word.lower()
                        if replacement_word is None:
                            candidate_honey_token_list.append(chars)
                        else:
                            # Replace with leetspeak
                            #if len(chars) > 3:
                            #    replacement_word = to_leetspeak(replacement_word)
                            candidate_honey_token_list.append(replacement_word)
                elif char_type == "Digit":
                    replacement_char = generate_replacement_char(chars, self.digit_list)
                    
                    candidate_honey_token_list.append(replacement_char)
                elif char_type == "Symbol":
                    replacement_char = generate_replacement_char(chars, self.symbol_list)
                    candidate_honey_token_list.append(replacement_char)
                else:
                    raise Exception("Invalid Char Type for Assembling Honey Password")
                
        # Join each token and restore capitalization.                     
        honey_password_candidate = "".join(candidate_honey_token_list)
        honey_password_candidate = restore_capitalization(honey_password_candidate)

        
        return honey_password_candidate
        
    def generate_honeyword_list(self) -> list[str]:
        self.capital_indexes, token_list = self.tokenize()
        while len(self.honeyword_list) < self.num_of_honeywords-1:
            honey_password_candidate = self.assemble_honey_password(token_list) # Assemble token list, Euclidean Assessment, Recapitalize
            #lev_distance_between_candidate_and_orig = levenshtein_distance(honey_password_candidate, self.password) # Levenshtein Assessment
            lev_distance_between_candidate_and_orig = textdistance.damerau_levenshtein(honey_password_candidate, self.password) # Damerau-Levenshtein Assessment
            print(lev_distance_between_candidate_and_orig, levenshtein_distance(honey_password_candidate, self.password))
            if lev_distance_between_candidate_and_orig > self.threshold_levenshtein:
                self.honeyword_list.append(honey_password_candidate)
            else:
                continue
        
        self.honeyword_list.append(self.password) # Append sugarword
        random.shuffle(self.honeyword_list) # Randomize positions
        sugarword_index = self.honeyword_list.index(self.password) # Find the index of the sugarword for the API HoneyChecker 
        return self.honeyword_list, sugarword_index

    
class ExistingPasswordGeneration:
    def __init__(self, password:str):
        self.password:str = password
        self.num_of_honeywords = 5 # How many honeywords to be generated? E.g 5 honeywords -> 4 sweet words, 1 sugar word.
        self.alphabet_upper_list = list(string.ascii_uppercase)
        self.alphabet_lower_list = list(string.ascii_lowercase)
        self.symbol_list = list(string.punctuation)
        self.digit_list =  list(string.digits)
        self.honeyword_list:list[str] = []
    
    def is_unique_or_list_empty(self, honeyword):
        if not self.honeyword_list or honeyword not in self.honeyword_list:
            return True
        else:
            return False
        
    def choose_replacement_character(self, character: str) -> str:
        if character.isdigit():
            return str(random.choice(self.digit_list))
        elif character.isalpha():
            if character.isupper():
                return str(random.choice(self.alphabet_upper_list))
            else:
                return str(random.choice(self.alphabet_lower_list))
        else:
            return str(random.choice(self.symbol_list))
    
    def choose_method(self, choice: int):
        self.honeyword_list = []
        match choice:
            case 1: # Chaffing by Tail-Tweaking
                self.num_of_tweaks = 2 # How many characters from the end will be tweaked.
                
                while len(self.honeyword_list) < self.num_of_honeywords - 1: # Generate 4 sweet words
                    self.password_characters:list[str] = [*self.password] # Create a list of characters out of the password
                    
                    for i in range(self.num_of_tweaks):
                        self.password_characters[len(self.password_characters)-(i+1)] = (
                            self.choose_replacement_character(self.password_characters[len(self.password_characters)-(i+1)])
                        )
                        
                    self.possible_sweetword = "".join(self.password_characters)
                    if self.is_unique_or_list_empty(self.possible_sweetword):
                        self.honeyword_list.append(self.possible_sweetword)
                        
                self.honeyword_list.append(self.password) # Append sugarword
                random.shuffle(self.honeyword_list) # Randomize positions
                sugarword_index = self.honeyword_list.index(self.password) # Find the index of the sugarword for the API HoneyChecker 
                return self.honeyword_list, sugarword_index
            
            case 2: # Take-a-tail
                self.num_of_tail_char = 3 # How many digits do you like to append to your password?
                self.password_characters:list[str] = [*self.password]
                
                for i in range(self.num_of_tail_char): # Append digits of length num_of_tail_char
                    self.password_characters.append(random.choice(self.digit_list))
                
                self.appended_password:str = "".join(self.password_characters) # join the characters with appended digits as the new password.
                
                while len(self.honeyword_list) < self.num_of_honeywords - 1: # Generate 4 sweet words
                    self.password_characters:list[str] = [*self.appended_password] # Create a list of characters out of the password
                    
                    for i in range(self.num_of_tail_char):
                        self.password_characters[len(self.password_characters)-(i+1)] = (
                            self.choose_replacement_character(self.password_characters[len(self.password_characters)-(i+1)])
                        )
                        
                    self.possible_sweetword = "".join(self.password_characters)
                    if self.is_unique_or_list_empty(self.possible_sweetword):
                        self.honeyword_list.append(self.possible_sweetword)
                        
                self.honeyword_list.append(self.appended_password) # Append sugarword
                random.shuffle(self.honeyword_list) # Randomize positions
                sugarword_index = self.honeyword_list.index(self.appended_password) # Find the index of the sugarword for the API HoneyChecker 
                return self.honeyword_list, sugarword_index
                    
            case 3: # Chaffing with a Password-model
                file_path = Path.cwd() / 'login' / 'static' / 'password_list.txt'
               # file_path = settings.BASE_DIR / 'login' / 'static' / 'password_list.txt' 
                with file_path.open('r', encoding='utf-8', errors='ignore') as file:
                    wordlist = [line.strip() for line in file]
                    
                while len(self.honeyword_list) < self.num_of_honeywords - 1:
                    w = random.choice(wordlist)
                    d = len(w)  # Determine the length of the chosen password
                    
                    # Initialize the new password (honeyword) as a list of characters
                    sweetword_candidate = [w[0]]  # Start with c1 = w1 (first character is directly copied)

                    # Step 2: Generate each character cj for j = 2, 3, ..., d
                    for j in range(1, d):  # Using range(1, d) because we've already added the first character
                        probability = random.random()  # Generate a random number between 0 and 1 for the probability.

                        if probability < 0.1:
                            # With probability 0.1, pick a new password of the same length randomly and take the jth character
                            new_password = random.choice([p for p in wordlist if len(p) == d])
                            sweetword_candidate.append(new_password[j])
                        elif probability < 0.5:
                            # With probability 0.4, pick a password that matches the previous character and take the jth character
                            new_password = random.choice([p for p in wordlist if len(p) == d and p[j - 1] == sweetword_candidate[j - 1]])
                            sweetword_candidate.append(new_password[j])
                        else:
                            # With probability 0.5, keep the jth character the same as in the original password
                            sweetword_candidate.append(w[j])
                    
                    self.possible_sweetword = "".join(sweetword_candidate)
                    if self.is_unique_or_list_empty(self.possible_sweetword):
                        self.honeyword_list.append(self.possible_sweetword)
                        
                self.honeyword_list.append(self.password) # Append sugarword
                random.shuffle(self.honeyword_list) # Randomize positions
                sugarword_index = self.honeyword_list.index(self.password) # Find the index of the sugarword for the API HoneyChecker 
                return self.honeyword_list, sugarword_index
            case _:
                raise Exception("Choose Method. Choice not in range.")

            
    
if __name__ == "__main__": # L3GendtyouSer4!rE4l2%7*
    # instance = ExistingPasswordGeneration("Ryan123")
    # honey_word_list, sugarindex = instance.choose_method(1)
    instance = ProposedPasswordGeneration("Ryan123")
    honey_word_list, sugarindex = instance.generate_honeyword_list()
    print(f"The honey word list is {honey_word_list}, and the sugarindex is {sugarindex}")

    
   
    
    
