"""
Database models for the circuit design assistant.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Component(Base):
    """Component model for storing electronic components."""
    __tablename__ = 'components'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # resistor, led, capacitor, etc.
    subcategory = Column(String(50))  # through-hole, smd, etc.
    value = Column(String(50))  # resistance, capacitance, etc.
    unit = Column(String(20))  # ohm, farad, volt, etc.
    voltage_rating = Column(Float)  # maximum voltage
    current_rating = Column(Float)  # maximum current
    power_rating = Column(Float)  # maximum power
    tolerance = Column(Float)  # tolerance percentage
    package = Column(String(50))  # package type
    manufacturer = Column(String(100))
    part_number = Column(String(100))
    description = Column(Text)
    datasheet_url = Column(String(500))
    cost = Column(Float)  # cost in USD
    availability = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Component(name='{self.name}', category='{self.category}', value='{self.value}')>"

class ComponentPerformance(Base):
    """Track component performance in simulations."""
    __tablename__ = 'component_performance'
    
    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, nullable=False)
    circuit_type = Column(String(100))  # led_blinker, servo_control, etc.
    performance_score = Column(Float)  # 0-1 score based on simulation results
    simulation_results = Column(Text)  # JSON string of simulation data
    user_feedback = Column(Integer)  # 1-5 rating from user
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ComponentPerformance(component_id={self.component_id}, score={self.performance_score})>"

class Circuit(Base):
    """Store generated circuits."""
    __tablename__ = 'circuits'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    user_input = Column(Text)  # original user request
    schematic_data = Column(Text)  # JSON representation of schematic
    netlist = Column(Text)  # SPICE netlist
    arduino_code = Column(Text)  # generated Arduino code
    simulation_results = Column(Text)  # JSON simulation data
    components_used = Column(Text)  # JSON list of component IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Circuit(name='{self.name}', id={self.id})>"

# Database setup
def get_database_url():
    """Get database URL from environment or use default SQLite."""
    db_path = os.path.join(os.path.dirname(__file__), 'circuit_design.db')
    return f'sqlite:///{db_path}'

def create_database():
    """Create database and tables."""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get database session."""
    engine = create_database()
    Session = sessionmaker(bind=engine)
    return Session() 