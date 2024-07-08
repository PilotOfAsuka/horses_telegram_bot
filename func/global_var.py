import json
from CONSTANT import game_states_file, user_count_date_file



def load_json(name):
    """Функция загрузки JSON в переменную"""
    try:
        with open(name, 'r') as file_user:
            file = json.load(file_user)
            print(f"{name} - loading successful")
            return file
    except FileNotFoundError:
        # Если файл не найден, начинаем с пустого словаря
        file = {}
        print(f"{name} not found, we make a new :)")
        return file


game_states = {}
user_count_date = {}

def save_in_json(dictionary, file_dir):
    """Принимает на вход словарь (dictionary) значений и сохраняет в файл JSON"""
    with open(file_dir, 'w') as file:
        json.dump(dictionary, file)


def set_game_state(msg, state):
    """Функция установки 'user_state'"""
    chat_id = str(msg.chat.id)
    game_states[chat_id] = state
    save_in_json(game_states, game_states_file)

def set_count_state(user_id, state):
    """Функция установки 'user_state'"""
    user_count_date[user_id] = state
    save_in_json(user_count_date, user_count_date_file)
