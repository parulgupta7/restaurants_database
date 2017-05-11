import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

base = declarative_base()

class User(base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))

class Restaurants(base):
    __tablename__ = 'restaurant'

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """It returns the data of restaurant in easily serialized format"""
        return {
        'name': self.name,
        'id': self.id,
        }

class MenuItems(base):
    __tablename__ ='items'

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    course = Column(String(250))
    description = Column(String(250))
    price = Column(String(8))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurants)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """It returns the data of restaurant menu items in easily serialized format"""
        return {
        'name': self.name,
        'id': self.id,
        'description': self.description,
        'price': self.price,
        'course': self.course,
        }


engine = create_engine('sqlite:///restaurantdatabase.db')
base.metadata.create_all(engine)





