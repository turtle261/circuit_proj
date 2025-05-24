"""
Seed the database with basic electronic components.
"""
from .models import Component, get_session, create_database

def seed_basic_components():
    """Add basic components for LED circuits and simple projects."""
    session = get_session()
    
    # Basic resistors
    resistors = [
        {"name": "220Ω Resistor", "category": "resistor", "value": "220", "unit": "ohm", 
         "power_rating": 0.25, "tolerance": 5.0, "package": "through-hole",
         "description": "Standard 1/4W carbon film resistor", "cost": 0.05},
        {"name": "330Ω Resistor", "category": "resistor", "value": "330", "unit": "ohm",
         "power_rating": 0.25, "tolerance": 5.0, "package": "through-hole",
         "description": "Standard 1/4W carbon film resistor", "cost": 0.05},
        {"name": "1kΩ Resistor", "category": "resistor", "value": "1000", "unit": "ohm",
         "power_rating": 0.25, "tolerance": 5.0, "package": "through-hole",
         "description": "Standard 1/4W carbon film resistor", "cost": 0.05},
        {"name": "10kΩ Resistor", "category": "resistor", "value": "10000", "unit": "ohm",
         "power_rating": 0.25, "tolerance": 5.0, "package": "through-hole",
         "description": "Standard 1/4W carbon film resistor", "cost": 0.05},
    ]
    
    # Basic LEDs
    leds = [
        {"name": "Red LED 5mm", "category": "led", "subcategory": "standard",
         "voltage_rating": 2.0, "current_rating": 0.02, "package": "5mm",
         "description": "Standard red LED, 2V forward voltage", "cost": 0.10},
        {"name": "Green LED 5mm", "category": "led", "subcategory": "standard",
         "voltage_rating": 2.1, "current_rating": 0.02, "package": "5mm",
         "description": "Standard green LED, 2.1V forward voltage", "cost": 0.10},
        {"name": "Blue LED 5mm", "category": "led", "subcategory": "standard",
         "voltage_rating": 3.2, "current_rating": 0.02, "package": "5mm",
         "description": "Standard blue LED, 3.2V forward voltage", "cost": 0.12},
    ]
    
    # Basic capacitors
    capacitors = [
        {"name": "100nF Ceramic Capacitor", "category": "capacitor", "subcategory": "ceramic",
         "value": "100e-9", "unit": "farad", "voltage_rating": 50.0,
         "package": "through-hole", "description": "Standard ceramic capacitor", "cost": 0.08},
        {"name": "10µF Electrolytic Capacitor", "category": "capacitor", "subcategory": "electrolytic",
         "value": "10e-6", "unit": "farad", "voltage_rating": 25.0,
         "package": "through-hole", "description": "Standard electrolytic capacitor", "cost": 0.15},
    ]
    
    # Arduino boards
    arduinos = [
        {"name": "Arduino Uno R3", "category": "microcontroller", "subcategory": "arduino",
         "voltage_rating": 5.0, "current_rating": 0.5, "package": "board",
         "description": "Arduino Uno R3 development board", "cost": 25.00},
    ]
    
    # Buttons and switches
    switches = [
        {"name": "Tactile Push Button", "category": "switch", "subcategory": "momentary",
         "voltage_rating": 12.0, "current_rating": 0.05, "package": "through-hole",
         "description": "Standard tactile push button switch", "cost": 0.50},
    ]
    
    # Combine all components
    all_components = resistors + leds + capacitors + arduinos + switches
    
    # Check if components already exist
    existing_count = session.query(Component).count()
    if existing_count > 0:
        print(f"Database already has {existing_count} components. Skipping seed.")
        session.close()
        return
    
    # Add components to database
    for comp_data in all_components:
        component = Component(**comp_data)
        session.add(component)
    
    session.commit()
    print(f"Added {len(all_components)} components to database.")
    session.close()

if __name__ == "__main__":
    # Create database and seed with data
    create_database()
    seed_basic_components() 