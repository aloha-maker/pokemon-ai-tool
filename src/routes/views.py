# src/routes/views.py
from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    return render_template('index.html')

@views_bp.route('/trained_pokemon_management')
def trained_pokemon_management():
    """育成済みポケモン管理ページを表示する。"""
    return render_template('trained_pokemon_management.html')
