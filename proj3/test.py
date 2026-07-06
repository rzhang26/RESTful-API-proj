import requests

BASE_URL = "http://127.0.0.1:5000/drinks"

def add_new_drink(name, description):
    payload = {
        "name": name,
        "description": description
    }
    # Sends a POST request with JSON data to add a drink
    response = requests.post(BASE_URL, json=payload)
    
    if response.status_code == 200:
        print(f"Success! Added drink. Server returned ID: {response.json()['id']}")
    else:
        print(f"Failed to add drink. Status code: {response.status_code}")

def delete_drink(drink_id):
    # Sends a DELETE request to /drinks/<id>
    response = requests.delete(f"{BASE_URL}/{drink_id}")
    
    if response.status_code == 200:
        print(f"Success! Server message: {response.json()['message']}")
    else:
        print(f"Failed to delete drink. Status code: {response.status_code}")

# --- Test the Script ---
if __name__ == "__main__":
    print("--- Adding a Drink ---")
    add_new_drink("Espresso", "Strong black coffee")
    add_new_drink("Matcha Latte", "Earthy green tea with steamed milk")

    print("\n--- Deleting Drink with ID 1 ---")
    delete_drink(1)