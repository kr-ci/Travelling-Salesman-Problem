import tkinter as tk
from tkinter import messagebox
import googlemaps
from itertools import permutations
from math import factorial
from googlemaps.exceptions import ApiError
import datetime

def save_variable_to_file(variable_content):
    # Pobierz aktualną datę i godzinę
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Utwórz nazwę pliku
    file_name = f"Trasa_{formatted_time}.txt"
    
    # Zapisz zmienną do pliku
    with open(file_name, 'w') as file:
        file.write(variable_content)
    
    print(f"File '{file_name}' has been created and the content has been saved.")
    
def generate_combinations(destination_set):
    """
    Funkcja generuje wszystkie unikalne pary miejsc docelowych.
    """
    pairs = []
    for i in range(len(destination_set)):
        for j in range(i + 1, len(destination_set)):
            pair = [destination_set[i], destination_set[j]]
            if pair not in pairs:
                pairs.append(pair)
    return pairs

def check_distance(gmaps, org, dst, mode='driving'):
    """
    Funkcja oblicza odległość między dwoma miejscami korzystając z Google Maps API.
    """
    matrix = gmaps.distance_matrix(origins=org, destinations=dst, mode=mode)
    distValue = matrix['rows'][0]['elements'][0]['distance']['value']
    return distValue

def calculate_route_distance(route, dist_Dict, org_Dict):
    """
    Funkcja oblicza całkowitą długość trasy na podstawie słowników odległości.
    """
    total_distance = 0
    total_distance += org_Dict[route[0]]  # Odległość od początkowego miejsca do pierwszego miejsca w trasie
    for i in range(len(route) - 1):
        city_pair = tuple(sorted((route[i], route[i + 1])))
        if city_pair in dist_Dict:
            total_distance += dist_Dict[city_pair]
        else:
            print(f"Warning: No distance found for {city_pair}")
            return float('inf')
    total_distance += org_Dict[route[-1]]  # Odległość od ostatniego miejsca w trasie do początkowego miejsca
    return total_distance

# Globalna zmienna do śledzenia, czy działanie zostało anulowane
is_canceled = False

def center_window(window, width, height):
    """
    Funkcja wyśrodkowuje okno na ekranie.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def show_custom_message(title, message, button_text="OK", cancel_button=False):
    """
    Funkcja wyświetla niestandardowe okno komunikatu z tłem i kolorem czcionki
    odpowiadającym głównemu oknu.
    """
    global is_canceled
    is_canceled = False  # Resetuje zmienną przed wyświetleniem okna

    def on_cancel():
        global is_canceled
        is_canceled = True
        dialog.destroy()

    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.configure(bg=root.cget('bg'))
    dialog.attributes('-topmost', True)  # Ustawia okno na wierzchu

    # Ustawienie etykiety
    label = tk.Label(
        dialog,
        text=message,
        bg=root.cget('bg'),
        fg='#ce723b',
        font=("Arial", 12)
    )
    label.pack(padx=20, pady=10)

    # Przycisk OK
    ok_button = tk.Button(
        dialog,
        text=button_text,
        command=lambda: dialog.destroy(),
        bg='#1e1e1e',
        fg='#ce723b',
        font=("Arial", 12)
    )
    ok_button.pack(pady=10, side='left', padx=(10, 5))

    # Przycisk Anuluj
    if cancel_button:
        cancel_button = tk.Button(
            dialog,
            text="Anuluj",
            command=on_cancel,
            bg='#1e1e1e',
            fg='#ce723b',
            font=("Arial", 12)
        )
        cancel_button.pack(pady=10, side='right', padx=(5, 10))

    # Ustawienie rozmiaru okna na podstawie etykiety i przycisku
    dialog.update_idletasks()  # Uaktualnia wymiary widgetów
    
    dialog_width = max(label.winfo_reqwidth(), ok_button.winfo_reqwidth()) + 40  # Uwzględnia marginesy
    dialog_height = label.winfo_reqheight() + ok_button.winfo_reqheight() + 60  # Uwzględnia marginesy
    center_window(dialog, dialog_width, dialog_height)

    # Ustawienie, aby funkcja czekała na zamknięcie okna
    dialog.wait_window(dialog)

    return is_canceled

def find_shortest_route():
    """
    Funkcja oblicza najkrótszą trasę uwzględniającą wszystkie możliwe permutacje miejsc.
    """
    api_key = api_key_entry.get()
    origin = origin_entry.get()
    destinations = destination_text.get("1.0", tk.END).strip().split("\n")
    travel_mode = travel_mode_var.get()

    if not api_key or not origin or not destinations:
        if show_custom_message("Błąd", "Wszystkie pola muszą być wypełnione", cancel_button=True):
            return
        
    # Informowanie o liczbie możliwych kombinacji
    num_destinations = len(destinations)
    num_permutations = factorial(num_destinations)
    if show_custom_message("Informacja", f"Liczba możliwych permutacji: {num_permutations}", cancel_button=True):
        return

    # Ostrzeżenie o kosztach i potencjalnym skrobaniu danych
    if show_custom_message("Ostrzeżenie", 
        "Korzystanie z Google Maps API może wiązać się z kosztami.Upewnij się, że masz odpowiednie środki na koncie.\n\n"
        "PAMIĘTAJ! Google Maps API do limitu 200$/msc jest ZA DARMO.\n\n"
        "* Intensywne i niekontrolowane wykorzystywanie interfejsu API może zostać zaklasyfikowane\n"
        "jako praktyka skrobania danych (data scraping), co może naruszać warunki użytkowania usługi\n"
        "oraz regulacje dotyczące ochrony danych. Skrobanie danych polega na systematycznym\n"
        "zbieraniu dużych ilości informacji z serwisów internetowych w sposób, który może być\n"
        "niezgodny z polityką prywatności lub zasadami dostawcy usługi."
    , cancel_button=True):
        return
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        # Sprawdzanie ważności klucza API przez wykonanie prostego żądania
        gmaps.geocode("test")
    except googlemaps.exceptions.ApiError as e:
        show_custom_message("Błąd API", f"Nieprawidłowy klucz API lub błąd w komunikacji z Google Maps API: {e}")
        return
    except Exception as e:
        show_custom_message("Błąd", f"Wystąpił błąd: {e}")
        return

    dist_Dict = {}
    org_Dict = {}

    # Obliczanie odległości z miejsca początkowego do miejsc docelowych
    for destination in destinations:
        distValue = check_distance(gmaps, origin, destination, mode=travel_mode)
        org_Dict[destination] = distValue / 1000  # Przemiana na kilometry

    # Obliczanie odległości między parami miejsc
    all_combinations = generate_combinations(destinations)
    for combination in all_combinations:
        start = combination[0]
        end = combination[1]
        distValue = check_distance(gmaps, start, end, mode=travel_mode)
        dist_Dict[tuple(combination)] = distValue / 1000  # Przemiana na kilometry

    # Generowanie permutacji miejsc
    permutations_of_cities = permutations(destinations)
    shortest_route = None
    min_distance = float('inf')

    # Sprawdzanie najkrótszej trasy
    for route in permutations_of_cities:
        distance = calculate_route_distance(route, dist_Dict, org_Dict)
        if distance < min_distance:
            min_distance = distance
            shortest_route = route

    # Wyświetlanie wyniku
    if shortest_route:
        result = f"Najkrótsza trasa: {origin} -> " + " -> ".join(shortest_route) + f" -> {origin}\n"
        result += f"Długość trasy: {min_distance:.2f} km"
        save_variable_to_file(result)
    else:
        result = "Nie znaleziono możliwej trasy."

    if show_custom_message("Wynik", result, cancel_button=True):
        return


# Tworzenie GUI
root = tk.Tk()
root.title("Problem komiwojażera")
root.configure(bg='#1e1e1e')  
root.attributes('-alpha', 0.9)
#root.geometry("510x310")
window_width = 510
window_height = 310
center_window(root, window_width, window_height)

# Etykieta i pole tekstowe dla klucza API
tk.Label(root, text="Klucz Google Maps API:", bg='#1e1e1e', fg='#ce723b', font=("Arial", 12, "bold")).place(x=10, y=10)
api_key_entry = tk.Entry(root, font=("Arial", 12), fg="black", bg="lightcyan", show="*", width=30)                     
api_key_entry.place(x=220, y=10)

# Etykieta i pole tekstowe dla lokalizacji początkowej
tk.Label(root, text="Lokalizacja Początkowa:", bg='#1e1e1e', fg='#ce723b', font=("Arial", 12, "bold")).place(x=10, y=50)
origin_entry = tk.Entry(root, font=("Arial", 12), fg="black", bg="lightcyan", width=30)
origin_entry.place(x=220, y=50)

# Opcje trybu podróży
travel_mode_var = tk.StringVar(value='driving')

tk.Label(root, text="Tryb podróży:", bg='#1e1e1e', fg='#ce723b', font=("Arial", 10, "bold")).place(x=10, y=90)
modes_frame = tk.Frame(root, bg='#1e1e1e')
modes_frame.place(x=10, y=130)

travel_modes = ["Samochód", "Rower", "Pieszo", "Transport publiczny"]
mode_values = ["driving", "bicycling", "walking", "transit"]
for mode_text, mode_value in zip(travel_modes, mode_values):
    tk.Radiobutton(
        modes_frame,
        text=mode_text,                # Tekst przycisku radiowego
        variable=travel_mode_var,      # Zmienna związana z przyciskiem radiowym
        value=mode_value,              # Wartość przypisana do przycisku radiowego
        bg='#1e1e1e',                 # Kolor tła przycisku radiowego
        fg='#ce723b',                 # Kolor tekstu przycisku radiowego
        font=("Arial", 10),            # Czcionka: Arial, rozmiar 10
        selectcolor='#2e2e2e'          # Kolor tła po zaznaczeniu
    ).pack(anchor='w')
    
# Etykieta i pole tekstowe dla miejsc docelowych
tk.Label(root, text="Miejsca do objazdu (każde w nowej linii):", bg='#1e1e1e', fg='#ce723b', font=("Arial", 10, "bold")).place(x=220, y=90)
destination_text = tk.Text(root, height=10, width=30, font=("Arial", 12,), fg="black", bg="lightcyan")
destination_text.place(x=220, y=110)

#Przycisk do obliczenia najkrótszej trasy
calculate_button = tk.Button(
    root,
    text="Oblicz najkrótszą trasę",
    bg='lightcyan',      # Kolor tła przycisku
    fg='#ce723b',     # Kolor tekstu przycisku
    font=("Arial", 12, "bold"),  # Czcionka: Arial, rozmiar 12, pogrubiona
    command=find_shortest_route  # Funkcja wywoływana po kliknięciu
)

# Ustawienie pozycji przycisku za pomocą metody place
calculate_button.place(x=10, y=262)

root.mainloop() 


