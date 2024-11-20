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
import json

import numpy as np
import os

import tensorflow as tf
import keras
from keras.src.utils.sequence_utils import pad_sequences
from keras.src.utils import to_categorical, plot_model
from keras.src.models import Sequential
from keras.src.layers import LSTM, Dense, Embedding
from keras.src.callbacks import EarlyStopping




# Run only Once for proposed method
#import nltk 
#nltk.download('wordnet')

class MLHoneywordGenerator:
    def __init__(self, password_list:list[str]=None, embedding_dim=50, lstm_units=100):
        """
        Initialize the Honeyword Generator with parameters.
        """
        self.threshold_damerau_levenshtein:int = 3
        self.num_of_honeywords:int = 5 # How many honeywords to be generated? E.g 5 honeywords -> 4 sweet words, 1 sugar word.
        self.password_list:list[str] = password_list
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.char_to_idx:dict[str,int] = {} 
        self.idx_to_char:dict[int,str] = {}
        self.model = None
        self.max_length_password_list:int = 0
        self.version:str = "honeyword_model_phpbb"
        self.dataset_name:str = "honeyword_dataset_phpbb"
        self.inp, self.out = None, None
        self.epochs = 100
        self.batch_size = 128
        self.seed_text_length = 2 # Zero-based

        # Only prepare dataset if passwords are provided
        if password_list:
            self._prepare_dataset()
            self.build_model()
            self.train()
        else:
            self._prepare_dataset()
    
    def visualize_model(self):
        plot_model(self.model, to_file='static/tf_resources/honey_model_architecture.png', show_shapes=True, show_layer_names=True)

    def _prepare_dataset(self):
        """
        Prepare the dataset by analyzing passwords, generating sequences, 
        and creating input-output pairs.
        """
        def _save_dataset():
            """
            Save preprocessed dataset and mappings to files.
            """
            # Save mappings and metadata as JSON
            with open(f"static/tf_resources/{self.dataset_name}", "w") as f:
                json.dump({
                    "char_to_idx": self.char_to_idx,
                    "idx_to_char": self.idx_to_char,
                    "max_length_password_list": self.max_length_password_list,
                    "inp": self.inp.tolist(),
                    "out": self.out.tolist() 
                }, f)

        def _load_dataset():
            """
            Load preprocessed dataset and mappings from files if they exist.
            """
            try:
                with open(f"static/tf_resources/{self.dataset_name}", "r") as f:
                    mappings: dict[str, dict | int | list]  = json.load(f)
                    self.char_to_idx = mappings["char_to_idx"]
                    self.idx_to_char = {int(idx): char for idx, char in mappings["idx_to_char"].items()}
                    self.max_length_password_list = mappings["max_length_password_list"]
                    self.inp = np.array(mappings["inp"]) 
                    self.out = np.array(mappings["out"])  
                return True
            except (FileNotFoundError, KeyError, json.JSONDecodeError):
                return False
        
        if _load_dataset(): # Load, else run rest of code.
            return
        
        # Set all possible characters in a password.
        chars = sorted(
                    list(string.ascii_letters)  + 
                    list(string.punctuation) + 
                    list(string.digits)
                )

        # Generate character-to-index and index-to-character mappings
        self.char_to_idx:dict[str,int] = {char: idx for idx, char in enumerate(chars)} # {'char': idx}  
        self.idx_to_char:dict[int,str] = {idx: char for char, idx in self.char_to_idx.items()} # {'idx': char}

        # Convert passwords to sequences of indices
        sequences:list[list[int]] = [] 
        for password in self.password_list:
            seq:list[int] = [self.char_to_idx[char] for char in password] # example mapping is word = [25,23,52,32]
            sequences.append(seq)
            
        # Create input-output pairs
        self.max_length_password_list = max(len(seq) for seq in sequences) # Find the longest password length in given dataset
        inp:list[list[int]] =  []
        out:list[int] = []
        for seq in sequences: # each password-index sequence
            for i in range(1, len(seq)): # create subsequence
                inp.append(seq[:i])
                out.append(seq[i])

        # Pad sequences and one-hot encode outputs
        self.inp = pad_sequences(inp, maxlen=self.max_length_password_list, padding='post') # Ensure all inputs have same length by padding using 0
        self.out = to_categorical(out, num_classes=len(self.char_to_idx))
        
        # Save dataset for future use
        _save_dataset()

    def build_model(self):
        """
        Build the LSTM model for honeyword generation.
        """
        self.model = Sequential([
            Embedding(input_dim=len(self.char_to_idx), # Vocabulary Size, length of unique chars
                      output_dim=self.embedding_dim, # Embedding Dimensions, default 50 dimensional vector
                      input_length=self.max_length_password_list), # Consistent length
            LSTM(self.lstm_units, return_sequences=True), # Identify temporal dependencies or patterns, returns hidden state sequences
            LSTM(self.lstm_units), # Return a single vector representing the entire input sequence.
            Dense(len(self.char_to_idx), activation='softmax') # Generate probability distribution, probability of a specific character being the next in the sequence.
        ])
        self.model.compile(optimizer='adam', loss='categorical_crossentropy') # Specify optimizer and loss function

    def train(self, epochs=100, batch_size=32):
        """
        Train the LSTM model.
        """
        if not self.model:
            raise ValueError("Model has not been built. Call build_model() first.")
        early_stopping = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True) # Define early stoppage, halt training when the validation loss stops improving.
        self.model.fit(self.inp, self.out, epochs=self.epochs, batch_size=self.batch_size, verbose=1, callbacks=[early_stopping])
        self.visualize_model() # Visualize Model
        self.model.save(f"static/tf_resources/{self.version}.keras")


    def generate_honeyword(self, seed_text:str, sugarword_length:int, temperature=0.7) -> str:
        """
        Generate a honeyword based on the seed text with added randomness.
        """
        def sample_with_temperature(predictions, temperature=1.0):
            """
            Sample an index from a probability distribution with temperature scaling.
            """
            predictions = np.log(predictions + 1e-8) / temperature  # Avoid log(0)
            exp_preds = np.exp(predictions)
            probabilities = exp_preds / np.sum(exp_preds)
            return np.random.choice(len(probabilities), p=probabilities)
        
        def load_model():
            try:
                self.model = keras.models.load_model(f"static/tf_resources/{self.version}.keras")
            except Exception as e:
                raise Exception(f"Can not load model. (Path:static/tf_resources/{self.version}.keras) (Reason: {str(e)})")
            
        honeyword = seed_text
        
        if not self.model:
            load_model()  # Load the model only if not already loaded
        for _ in range(sugarword_length - len(seed_text)):
            input_seq = [self.char_to_idx[char] for char in honeyword[-self.max_length_password_list:]] # Negative Indexing in the case that entered Password Longer Case, and Password Shorter Case than longest assword in list.
            input_seq = pad_sequences([input_seq], maxlen=self.max_length_password_list, padding='post')
            predictions = self.model.predict(input_seq, verbose=0)[0]
            next_index = sample_with_temperature(predictions, temperature)
            next_char = self.idx_to_char[next_index]
            honeyword += next_char
        return honeyword

    def generate_honeywords(self, sugarword) -> tuple[list,int]:
        """
        Generate multiple honeywords for a given sugarword.
        """
        seed_text = sugarword[:self.seed_text_length]  # Start with a seed text
        honeyword_list = []

        while len(honeyword_list) < self.num_of_honeywords-1:
            
            honey_password_candidate = self.generate_honeyword(seed_text, len(sugarword))
            lev_distance_between_candidate_and_orig = textdistance.damerau_levenshtein(honey_password_candidate, sugarword) # Damerau-Levenshtein Assessment
            # print(honey_password_candidate, lev_distance_between_candidate_and_orig) # Debugging
            if lev_distance_between_candidate_and_orig >= self.threshold_damerau_levenshtein and honey_password_candidate not in honeyword_list:
                honeyword_list.append(honey_password_candidate)
            else:
                continue
        
        honeyword_list.append(sugarword)
        random.shuffle(honeyword_list) # Randomize positions
        sugarword_index = honeyword_list.index(sugarword) # Find the index of the sugarword for the API HoneyChecker 
        return honeyword_list, sugarword_index
    
    
class ProposedPasswordGeneration:
    def __init__(self, password: str):
        self.threshold_damerau_levenshtein:int = 3
        self.threshold_euclidean:float = 3.0
        
        self.password:str = password
        self.num_of_honeywords:int = 5 # How many honeywords to be generated? E.g 5 honeywords -> 4 sweet words, 1 sugar word.

        self.alphabet_upper_list = list(string.ascii_uppercase)
        self.alphabet_lower_list = list(string.ascii_lowercase)
        self.symbol_list = list(string.punctuation)
        self.digit_list =  list(string.digits)
        self.honeyword_list:list[str] = []
        self.capital_indexes:list[int] = []

        # Define keyboard layout positions (x, out) by row for QWERTY keyboard
        self.keyboard_layout = {
            # Row 1: Top row (Numbers and symbols)
            '`': (-1, 0),'1': (0, 0), '2': (1, 0), '3': (2, 0), '4': (3, 0), '5': (4, 0), '6': (5, 0), '7': (6, 0), '8': (7, 0), '9': (8, 0), '0': (9, 0), '-': (9, 0), '=': (10, 0),
            '~': (-1, 0),'!': (0, 0), '@': (1, 0), '#': (2, 0), '$': (3, 0), '%': (4, 0), '^': (5, 0), '&': (6, 0), '*': (7, 0), '(': (8, 0), ')': (9, 0), '_': (9, 0), '+': (10, 0),
            
            # Row 2: QWERTY row
            'q': (0, 1), 'w': (1, 1), 'e': (2, 1), 'r': (3, 1), 't': (4, 1), 'out': (5, 1), 'u': (6, 1), 'i': (7, 1), 'o': (8, 1), 'p': (9, 1), '[': (10, 1), ']': (11, 1), '\\': (12, 1),
            'Q': (0, 1), 'W': (1, 1), 'E': (2, 1), 'R': (3, 1), 'T': (4, 1), 'Y': (5, 1), 'U': (6, 1), 'I': (7, 1), 'O': (8, 1), 'P': (9, 1), '{': (10, 1), '}': (11, 1), '|': (12, 1),
            
            # Row 3: Home row
            'a': (0, 2), 's': (1, 2), 'd': (2, 2), 'f': (3, 2), 'g': (4, 2), 'h': (5, 2), 'j': (6, 2), 'k': (7, 2), 'l': (8, 2), ';': (9, 2), "'": (10, 2),
            'A': (0, 2), 'S': (1, 2), 'D': (2, 2), 'F': (3, 2), 'G': (4, 2), 'H': (5, 2), 'J': (6, 2), 'K': (7, 2), 'L': (8, 2), ':': (9, 2), '"': (10, 2),
            
            # Row 4: Bottom row
            'z': (0, 3), 'x': (1, 3), 'c': (2, 3), 'v': (3, 3), 'b': (4, 3), 'n': (5, 3), 'm': (6, 3), ',': (7, 3), '.': (8, 3), '/': (9, 3),
            'Z': (0, 3), 'inp': (1, 3), 'C': (2, 3), 'V': (3, 3), 'B': (4, 3), 'N': (5, 3), 'M': (6, 3), '<': (7, 3), '>': (8, 3), '?': (9, 3),
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
            if lev_distance_between_candidate_and_orig > self.threshold_damerau_levenshtein:
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
    """
    # instance = ExistingPasswordGeneration("Ryan123")
    # honey_word_list, sugarindex = instance.choose_method(1)
    instance = ProposedPasswordGeneration("Ryan123")
    honey_word_list, sugarindex = instance.generate_honeyword_list()
    print(f"The honey word list is {honey_word_list}, and the sugarindex is {sugarindex}")
    """
    
    # Temporary
    passwords = []
    file_path = Path.cwd() / 'static' / 'phpbb-cleaned-up-listed-python.json'
    
    with file_path.open('r', encoding='utf-8', errors='ignore') as file:
        passwords = json.load(file)
            
    # Initialize and train the Honeyword Generator
    generator = MLHoneywordGenerator(passwords)
    print(generator.generate_honeywords("password123"))
    
 
  

    
   
    
    
