
def get_stimme(input_string):

    # Get numbers in detection
    numbers = extract_numbers(input_string)

    # Get melodic in detection
    distinction = extract_melodic(input_string) # c, b, es

    return numbers, distinction

def extract_melodic(input_string):

    for i, split in enumerate(input_string.split(" ")):
        if split == "in":
            try:
                return input_string.split(" ")[i+1]
            except:
                return None


# def extract_instrument_voice(input_string):
#     # Suche nach dem Index des Substrings "in" im Eingabestring
#     index_of_in = input_string.find("in")
#     if index_of_in != -1:  # "in" gefunden
#         # Rückgabe des Substrings nach "in" (ohne Leerzeichen)
#         return input_string[index_of_in + 3:].strip()
#     else:
#         return None  # "in" nicht gefunden

# # Beispielaufruf der Funktion
# input_strings = ["Klarinette in es", "Posaune in C", "Possaune in b"]

# for input_string in input_strings:
#     voice = extract_instrument_voice(input_string)
#     print(f"Voice extracted from '{input_string}': {voice}")


def extract_numbers(input_string):
    numbers = []
    current_number = ""
    for char in input_string:
        if char.isdigit():
            current_number += char
        elif current_number:
            numbers.append(int(current_number))
            current_number = ""
    if current_number:  # Überprüfen Sie, ob am Ende der Zeichenkette eine Zahl verbleibt
        numbers.append(int(current_number))
    
    if numbers:
        if len(numbers) > 1:
            return "multiple"
    else:
        return None

    return numbers[0]

# Beispielaufruf der Funktion
input_string = "1. Klarinette in es"
numbers = get_stimme(input_string)
print("Numbers in input_string:", numbers)

input_string = "2. Klarinette"
numbers = get_stimme(input_string)
print("Numbers in input_string:", numbers)

input_string = "Klarinette in es"
numbers = get_stimme(input_string)
print("Numbers in input_string:", numbers)

input_string = "Possaune in c"
numbers = get_stimme(input_string)
print("Numbers in input_string:", numbers)