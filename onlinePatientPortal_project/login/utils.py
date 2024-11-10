import random
from Levenshtein import distance as levenshtein_distance  # Requires python-Levenshtein package
from django.http import JsonResponse
import numpy as np
from PyDictionary import PyDictionary
import string
from pathlib import Path
from django.conf import settings
import requests
from .models import *
    
dictionary = PyDictionary()

def is_word_in_dictionary(word):
    meaning = dictionary.meaning(word)  
    if meaning: 
        return True
    else:
        return False

class ProposedPasswordGeneration:
    def __init__(self, threshold_levenshtein: int, threshold_euclidean: float, sugarword: str):
        self.threshold_levenshtein = threshold_levenshtein
        self.threshold_euclidean = threshold_euclidean
        self.sugarword = sugarword
        self.num = 5 # Number of sweetwords denoted by k-1 where k is the amount of honeywords
        
        # Define keyboard layout positions (x, y) by row for QWERTY keyboard
        self.keyboard_layout = {
            # Row 1: Top row (Numbers and symbols)
            '`': (1, 1),'1': (0, 0), '2': (1, 0), '3': (2, 0), '4': (3, 0), '5': (4, 0), '6': (5, 0), '7': (6, 0), '8': (7, 0), '9': (8, 0), '0': (9, 0),
            '~': (0, 1),'!': (0, 0), '@': (1, 0), '#': (2, 0), '$': (3, 0), '%': (4, 0), '^': (5, 0), '&': (6, 0), '*': (7, 0), '(': (8, 0), ')': (9, 0),
            
            # Row 2: QWERTY row
            'q': (0, 1), 'w': (1, 1), 'e': (2, 1), 'r': (3, 1), 't': (4, 1), 'y': (5, 1), 'u': (6, 1), 'i': (7, 1), 'o': (8, 1), 'p': (9, 1), '-': (10, 1), '=': (11, 1),
            'Q': (0, 1), 'W': (1, 1), 'E': (2, 1), 'R': (3, 1), 'T': (4, 1), 'Y': (5, 1), 'U': (6, 1), 'I': (7, 1), 'O': (8, 1), 'P': (9, 1), '_': (10, 1), '+': (11, 1),
            
            # Row 3: Home row
            'a': (0, 2), 's': (1, 2), 'd': (2, 2), 'f': (3, 2), 'g': (4, 2), 'h': (5, 2), 'j': (6, 2), 'k': (7, 2), 'l': (8, 2), ';': (9, 2), "'": (10, 2),
            'A': (0, 2), 'S': (1, 2), 'D': (2, 2), 'F': (3, 2), 'G': (4, 2), 'H': (5, 2), 'J': (6, 2), 'K': (7, 2), 'L': (8, 2), ':': (9, 2), '"': (10, 2),
            
            # Row 4: Bottom row
            'z': (0, 3), 'x': (1, 3), 'c': (2, 3), 'v': (3, 3), 'b': (4, 3), 'n': (5, 3), 'm': (6, 3), ',': (7, 3), '.': (8, 3), '/': (9, 3),
            'Z': (0, 3), 'X': (1, 3), 'C': (2, 3), 'V': (3, 3), 'B': (4, 3), 'N': (5, 3), 'M': (6, 3), '<': (7, 3), '>': (8, 3), '?': (9, 3),
            
            # Row 5: Space bar and other keys
            ' ': (4, 4), '\\': (11, 3), '|': (11, 3)
        }
    
    def tokenize(self) -> tuple[list[str], list[str], list[str]]: # L3GendtyouSer4!rE4l2%7*
        def process_word(lexeme_string):
            while len(lexeme_string) > 1:
                temp_lexeme_string = "" # gendtyouser is our lexeme_string  
                count = 0
                
                for char in lexeme_string: # We continuously check by going through the lexeme_string to see if we get a word.
                    temp_lexeme_string += char
                    count += 1
                    if is_word_in_dictionary(temp_lexeme_string) and len(temp_lexeme_string) > 1:
                        token_list.append({temp_lexeme_string:"Word"})
                        temp_lexeme_string = "" 
                        lexeme_string = lexeme_string[count:]
                        count = 0
                        break
                    
                if temp_lexeme_string == lexeme_string:
                    token_list.append({lexeme_string[0]:"Letter"})
                    lexeme_string = lexeme_string[1:]
                    
            if lexeme_string == 1:
                token_list.append({lexeme_string:"Letter"})
                lexeme_string, type = "", ""
            
        before_password = self.sugarword
        token_list = [] # Letter, Word, Numbers, Special Character
        lexeme_string = ""
        type = "empty"
        
        capital_index = []
        for i in range(len(before_password)): # Get the indexes where the capitalization occurs.
            if before_password[i].isupper():
                capital_index.append(i)
        
        lowercase_password = before_password.lower() # l3gendtyouser4!re4l2%7*
    
        for i in range(len(lowercase_password)): # Parse the password and tokenize
            if lowercase_password[i].isalpha():
                lexeme_string += lowercase_password[i]
                if type == "1": # if it is the first character of the string.
                    type = "String"
                elif i == (len(lowercase_password)-1):
                    token_list.append({lexeme_string:"Word"})
                    lexeme_string, type = "", ""
            elif lowercase_password[i].isnumeric():
                if type == "1":
                    type = "Digit"
                elif len(lexeme_string) > 2 and lexeme_string.isalpha(): # We have a lexeme_string, and we reached a digit. But we don't know if there are words.
                    process_word(lexeme_string)
                    lexeme_string, type = lowercase_password[i], "Digit"
                elif len(lexeme_string) == 1 and lexeme_string.isalpha(): # This is a single letter in the lexeme_string. We append and reset.
                    token_list.append({lexeme_string:"Letter"})
                    lexeme_string, type = lowercase_password[i], "Digit"
                else: # Handle digit case.
                    lexeme_string, type = lowercase_password[i], "Digit"
                token_list.append({lexeme_string:type})
                lexeme_string, type = "", ""
            elif lowercase_password[i] in string.punctuation:
                lexeme_string += lowercase_password[i]
                if type == "1":
                    type = "Symbol"
                elif len(lexeme_string) > 2 and lexeme_string.isalpha(): # We have a lexeme_string, and we reached a Symbol. But we don't know if there are words.
                    process_word(lexeme_string)
                    lexeme_string, type = lowercase_password[i], "Symbol"
                elif lexeme_string == 1 and lexeme_string.isalpha(): # This is not a word. We append and reset.
                    token_list.append({lexeme_string:"Letter"})
                    lexeme_string = lowercase_password[i]
                    type = "Symbol"
                else: # Handle symbol case
                    lexeme_string, type = lowercase_password[i], "Symbol"
                token_list.append({lexeme_string:type})
                lexeme_string, type = "", ""
                
        print(token_list)
                
        
 

    def generate_sweetwords(self, password: str) -> list[str]:
        sweetwords = []
        for _ in range(self.num): 
            
            tail = str(random.randint(100, 999))  # Random tail for demonstration
            sweetword = f"{password}{tail}"  # Combine password with tail
            sweetwords.append(sweetword)
        return sweetwords

    def manhattan_distance(char1: str, char2: str, keyboard_layout: dict) -> float:
        if char1 in keyboard_layout and char2 in keyboard_layout:
            # Get coordinates of each character
            x1, y1 = keyboard_layout[char1]
            x2, y2 = keyboard_layout[char2]
            
            # Calculate Manhattan distance
            return abs(x2 - x1) + abs(y2 - y1)
        else:
            # If character not found in layout, return an infinite distance
            return float('inf')

    def assess_passwords(self, password: str) -> list[str]:
        sweetwords = self.generate_sweetwords(password)
        valid_sweetwords = []
        
        for sweetword in sweetwords:
            lev_dist = levenshtein_distance(password, sweetword)
            euc_dist = sum(self.euclidean_distance(c1, c2) for c1, c2 in zip(password, sweetword))
            
            if lev_dist <= self.threshold_levenshtein and euc_dist <= self.threshold_euclidean:
                valid_sweetwords.append(sweetword)
        
        return valid_sweetwords
    
class ExistingPasswordGeneration:
    def __init__(self, password:str):
        self.password:str = password
        self.num_of_honeywords = 5 # How many honeywords to be generated? E.g 5 honeywords -> 4 sweet words, 1 sugar word.
        self.alphabet_upper_list = list(string.ascii_uppercase)
        self.alphabet_lower_list = list(string.ascii_lowercase)
        self.symbol_list = list(string.punctuation)
        self.digit_list =  list(string.digits)
        self.honeyword_list = []
    
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

            
    
if __name__ == "__main__":
    instance = ExistingPasswordGeneration("henl12oY#")
    print(instance.choose_method(1))
    print(instance.choose_method(2))
    print(instance.choose_method(3))
    
   
    
    
