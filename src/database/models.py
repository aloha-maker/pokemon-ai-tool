import datetime
from sqlalchemy import (Column, Integer, String, ForeignKey, create_engine,
                        DateTime, UniqueConstraint, Text)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

Base = declarative_base()

# マスタデータモデル
class Pokemon(Base):
    __tablename__ = 'pokemons'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    name_ja = Column(String)
    type1 = Column(String, nullable=False)
    type2 = Column(String)
    hp = Column(Integer, nullable=False)
    attack = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    sp_attack = Column(Integer, nullable=False)
    sp_defense = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)

class Move(Base):
    __tablename__ = 'moves'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    power = Column(Integer)
    accuracy = Column(Integer)

class Type(Base):
    __tablename__ = 'types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    name_ja = Column(String)

class Ability(Base):
    __tablename__ = 'abilities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    name_ja = Column(String)

class Nature(Base):
    __tablename__ = 'natures'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    name_ja = Column(String)
    increased_stat = Column(String)
    decreased_stat = Column(String)

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    name_ja = Column(String)

# 育成済みポケモンモデル (F-05)
class TrainedPokemon(Base):
    __tablename__ = 'trained_pokemons'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pokemon_id = Column(Integer, ForeignKey('pokemons.id'), nullable=False)
    nickname = Column(String)
    level = Column(Integer, nullable=False, default=50)
    tera_type_id = Column(Integer, ForeignKey('types.id'))
    ability_id = Column(Integer, ForeignKey('abilities.id'))
    nature_id = Column(Integer, ForeignKey('natures.id'))
    held_item_id = Column(Integer, ForeignKey('items.id'))
    move1_id = Column(Integer, ForeignKey('moves.id'))
    move2_id = Column(Integer, ForeignKey('moves.id'))
    move3_id = Column(Integer, ForeignKey('moves.id'))
    move4_id = Column(Integer, ForeignKey('moves.id'))
    ev_hp = Column(Integer, default=0)
    ev_atk = Column(Integer, default=0)
    ev_def = Column(Integer, default=0)
    ev_spa = Column(Integer, default=0)
    ev_spd = Column(Integer, default=0)
    ev_spe = Column(Integer, default=0)
    iv_hp = Column(Integer, default=31)
    iv_atk = Column(Integer, default=31)
    iv_def = Column(Integer, default=31)
    iv_spa = Column(Integer, default=31)
    iv_spd = Column(Integer, default=31)
    iv_spe = Column(Integer, default=31)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    pokemon = relationship("Pokemon")
    tera_type = relationship("Type")
    ability = relationship("Ability")
    nature = relationship("Nature")
    held_item = relationship("Item")
    move1 = relationship("Move", foreign_keys=[move1_id])
    move2 = relationship("Move", foreign_keys=[move2_id])
    move3 = relationship("Move", foreign_keys=[move3_id])
    move4 = relationship("Move", foreign_keys=[move4_id])

# パーティモデル (F-06)
class Party(Base):
    __tablename__ = 'parties'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    members = relationship("PartyMember", back_populates="party", cascade="all, delete-orphan", order_by="PartyMember.member_index")

class PartyMember(Base):
    __tablename__ = 'party_members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    party_id = Column(Integer, ForeignKey('parties.id', ondelete='CASCADE'), nullable=False)
    trained_pokemon_id = Column(Integer, ForeignKey('trained_pokemons.id', ondelete='CASCADE'), nullable=False)
    member_index = Column(Integer, nullable=False)

    party = relationship("Party", back_populates="members")
    trained_pokemon = relationship("TrainedPokemon")

    __table_args__ = (
        UniqueConstraint('party_id', 'trained_pokemon_id'),
        UniqueConstraint('party_id', 'member_index'),
    )
