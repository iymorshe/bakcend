from flask import Flask, jsonify, request, abort
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Returns the dictionary {DAY: {MEAL: [Dishes{}]}}
def getDCMenu(dining_common):
    url = f"https://housing.ucdavis.edu/dining/menus/dining-commons/{dining_common}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # Dictionary to hold all menu items grouped by days and meals
    weekly_menu = {}

    day_sections = soup.find_all("div", class_="menu_maincontainer")

    for section in day_sections:
        day_name = section.find("h3").text.strip() if section.find("h3") else "Unknown Day"
        weekly_menu[day_name] = {"Breakfast": [], "Lunch": [], "Dinner": []}

        # Further assumptions: each meal type is in a distinct section/class within the day's section
        meals = section.find_all("div", recursive=False)  # Adjust the tag and class based on actual structure
        for meal in meals:
            meal_name = meal.find("h4").text.strip() if meal.find("h4") else "No Meal Name"

            # Check meal name to decide where to place it
            if "breakfast" in meal_name.lower():
                meal_type = "Breakfast"
            elif "lunch" in meal_name.lower():
                meal_type = "Lunch"
            elif "dinner" in meal_name.lower():
                meal_type = "Dinner"
            else:
                continue  # If no valid meal type is found, skip to the next

            menu_items = meal.find_all("li", class_="trigger")  
            for item in menu_items:
                dish_name = item.find("span").text.strip() if item.find("span") else "No Dish Name"
                description = item.find("p")
                dish_description = description.text.strip() if description else "No Description"
                nutrition = item.find("ul", class_="nutrition")
                nutritional_details = {}
                if nutrition:
                    for detail in nutrition.find_all("p"):
                        text = detail.text.strip().split(":")
                        if len(text) == 2:
                            nutritional_details[text[0].strip()] = text[1].strip()

                # Append the collected data to the list under the correct meal and day
                weekly_menu[day_name][meal_type].append({
                    "Dish Name": dish_name,
                    "Description": dish_description,
                    "Nutritional Information": nutritional_details
                })

    return weekly_menu

def getFoodTruckMenu():
    url = "https://housing.ucdavis.edu/dining/food-trucks/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    schedule = {}
    schedule_section = soup.find("div", class_="food_trucks_schedule")

    if schedule_section:
        days = schedule_section.find_all("h3")
        for day in days:
            day_name = day.text.strip()
            schedule[day_name] = []
            
            # Get all elements until next h3 or end
            current = day.next_sibling
            while current and not (current.name == 'h3'):
                if current.name == 'p' and not 'no-trucks' in current.get('class', []):
                    truck_info = current.text.strip()
                    if '—' in truck_info:
                        truck_name, hours = truck_info.split('—')
                        schedule[day_name].append({
                            "name": truck_name.replace('strong', '').strip(),
                            "hours": hours.strip()
                        })
                current = current.next_sibling

    return schedule


@app.route('/menu/<dining_common>')
def menu(dining_common):
    menu_data = getDCMenu(dining_common)
    return jsonify(menu_data)

@app.route('/menu/trucks')
def food_truck_menu():
    food_truck_menu = getFoodTruckMenu()
    return jsonify(food_truck_menu)

if __name__ == '__main__':
    app.run(debug=False)
