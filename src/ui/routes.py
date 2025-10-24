import traceback
import math
import uuid
from flask import Blueprint, jsonify, request
from src.database.manager import DatabaseManager
from src.services.party_service import PartyService
from src.services.trained_pokemon_service import TrainedPokemonService
from src.services.dashboard_service import DashboardService
from src.core import calculator
from src.ai import simulator

# APIエンドポイント用のBlueprintを作成
api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- シミュレーションセッション管理 ---
# 本番環境ではRedisなどを使用すべきだが、ここでは簡易的にグローバル変数で管理
simulations = {}

# --- F-05: 育成済みポケモン管理 (Trained Pokemons) ---

@api_bp.route('/trained-pokemons', methods=['GET'])
def get_trained_pokemons():
    """登録済みの育成済みポケモンを一覧で取得する。"""
    try:
        service = TrainedPokemonService()
        pokemons = service.get_all()
        return jsonify(pokemons), 200
    except Exception as e:
        return jsonify({'error': '育成済みポケモンの取得に失敗しました。'}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['GET'])
def get_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモンの詳細を取得する。"""
    try:
        service = TrainedPokemonService()
        pokemon = service.get_by_id(pokemon_id)
        if pokemon:
            return jsonify(pokemon), 200
        else:
            return jsonify({'error': '指定されたポケモンが見つかりません。'}), 404
    except Exception as e:
        return jsonify({'error': 'ポケモンの詳細取得に失敗しました。'}), 500

@api_bp.route('/trained-pokemons', methods=['POST'])
def add_trained_pokemon():
    """新しい育成済みポケモンを登録する。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '無効なデータです。'}), 400
    
    try:
        service = TrainedPokemonService()
        new_id = service.create(data)
        return jsonify({'message': 'ポケモンを登録しました。', 'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': 'ポケモンの登録に失敗しました。'}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['PUT'])
def update_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモン情報を更新する。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '無効なデータです。'}), 400

    try:
        service = TrainedPokemonService()
        updated_rows = service.update(pokemon_id, data)
        if updated_rows > 0:
            return jsonify({'message': f'ポケモンID {pokemon_id} を更新しました。'}), 200
        else:
            return jsonify({'error': '指定されたポケモンが見つからないか、更新内容がありません。'}), 404
    except Exception as e:
        return jsonify({'error': 'ポケモンの更新に失敗しました。'}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['DELETE'])
def delete_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモンを削除する。"""
    try:
        service = TrainedPokemonService()
        deleted_rows = service.delete(pokemon_id)
        if deleted_rows > 0:
            return jsonify({'message': f'ポケモンID {pokemon_id} を削除しました。'}), 200
        else:
            return jsonify({'error': '指定されたポケモンが見つかりません。'}), 404
    except Exception as e:
        return jsonify({'error': 'ポケモンの削除に失敗しました。'}), 500

# --- Master Data API Endpoints ---

@api_bp.route('/master/<resource>', methods=['GET'])
def get_master_data(resource):
    """ポケモン、技、特性などのマスターデータを取得する。"""
    valid_resources = ['pokemons', 'moves', 'items', 'abilities', 'natures', 'types']
    if resource not in valid_resources:
        return jsonify({'error': 'Invalid resource specified'}), 404

    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            if resource == 'pokemons':
                cursor.execute("SELECT MIN(id) as id, name, name_ja FROM pokemons GROUP BY name_ja ORDER BY name_ja")
            else:
                 cursor.execute(f"SELECT id, name, name_ja FROM {resource} WHERE name_ja IS NOT NULL AND name_ja != '' ORDER BY name_ja")
            items = cursor.fetchall()
        return jsonify([dict(item) for item in items]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 持ち物編集用API ---

@api_bp.route('/items', methods=['POST'])
def add_item():
    """新しい持ち物を追加する。"""
    data = request.get_json()
    if not data or not data.get('name_ja'):
        return jsonify({'error': 'Invalid data: name_ja is required.'}), 400
    
    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT id FROM items WHERE name_ja = ?", (data['name_ja'],))
            if cursor.fetchone():
                return jsonify({'error': 'Item with this name already exists.'}), 409
            
            cursor.execute(
                "INSERT INTO items (name, name_ja) VALUES (?, ?)",
                (data['name_ja'], data['name_ja'])
            )
            db.conn.commit()
            new_id = cursor.lastrowid
        return jsonify({'message': 'Item added successfully', 'id': new_id, 'name_ja': data['name_ja']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """持ち物名を更新する。"""
    data = request.get_json()
    if not data or not data.get('name_ja'):
        return jsonify({'error': 'Invalid data: name_ja is required.'}), 400

    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT id FROM items WHERE name_ja = ? AND id != ?", (data['name_ja'], item_id))
            if cursor.fetchone():
                return jsonify({'error': 'Item with this name already exists.'}), 409

            cursor.execute(
                "UPDATE items SET name = ?, name_ja = ? WHERE id = ?",
                (data['name_ja'], data['name_ja'], item_id)
            )
            db.conn.commit()
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
        return jsonify({'message': 'Item updated successfully', 'id': item_id, 'name_ja': data['name_ja']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """持ち物を削除する。"""
    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            db.conn.commit()
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
        return jsonify({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        if 'FOREIGN KEY constraint failed' in str(e):
            return jsonify({'error': 'This item is currently in use by a trained Pokémon and cannot be deleted.'}), 409
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties', methods=['GET'])
def get_parties():
    """登録済みのパーティを一覧で取得する。"""
    try:
        service = PartyService()
        parties = service.get_all()
        return jsonify(parties), 200
    except Exception as e:
        return jsonify({'error': 'パーティ一覧の取得に失敗しました。'}), 500

@api_bp.route('/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    """指定したIDのパーティ詳細を取得する。"""
    try:
        service = PartyService()
        party = service.get_by_id(party_id)
        if party:
            return jsonify(party), 200
        else:
            return jsonify({'error': '指定されたパーティが見つかりません。'}), 404
    except Exception as e:
        return jsonify({'error': 'パーティ詳細の取得に失敗しました。'}), 500

@api_bp.route('/parties', methods=['POST'])
def add_party():
    """新しいパーティを登録する。"""
    data = request.get_json()
    if not data or not data.get('name') or 'members' not in data:
        return jsonify({'error': '無効なデータです。パーティ名とメンバーは必須です。'}), 400
    
    try:
        service = PartyService()
        new_id = service.create(data)
        return jsonify({'message': 'パーティを登録しました。', 'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': 'パーティの登録に失敗しました。'}), 500

@api_bp.route('/parties/<int:party_id>', methods=['PUT'])
def update_party(party_id):
    """指定したIDのパーティ情報を更新する。"""
    data = request.get_json()
    if not data or not data.get('name') or 'members' not in data:
        return jsonify({'error': 'Invalid data: name and members are required.'}), 400

    try:
        service = PartyService()
        updated_rows = service.update(party_id, data)
        if updated_rows > 0:
            return jsonify({'message': f'パーティID {party_id} を更新しました。'}), 200
        else:
            return jsonify({'error': '指定されたパーティが見つからないか、更新内容がありません。'}), 404
    except Exception as e:
        return jsonify({'error': 'パーティの更新に失敗しました。'}), 500

@api_bp.route('/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    """指定したIDのパーティを削除する。"""
    try:
        service = PartyService()
        deleted_rows = service.delete(party_id)
        if deleted_rows > 0:
            return jsonify({'message': f'パーティID {party_id} を削除しました。'}), 200
        else:
            return jsonify({'error': '指定されたパーティが見つかりません。'}), 404
    except Exception as e:
        return jsonify({'error': 'パーティの削除に失敗しました。'}), 500

# --- F-07: 計算機 (Calculator) ---

@api_bp.route('/calculate/status', methods=['POST'])
def calculate_status_api():
    """ポケモンのステータス実数値を計算して返す。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        pokemon_id = data.get('pokemon_id')
        level = int(data.get('level', 50))
        evs = data.get('evs', {})
        ivs = {'hp': 31, 'attack': 31, 'defense': 31, 'sp_attack': 31, 'sp_defense': 31, 'speed': 31}
        nature_id = data.get('nature_id')

        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT hp, attack, defense, sp_attack, sp_defense, speed FROM pokemons WHERE id = ?", (pokemon_id,))
            base_stats_row = cursor.fetchone()
            if not base_stats_row:
                return jsonify({'error': 'Pokemon not found'}), 404
            base_stats = dict(base_stats_row)

            cursor.execute("SELECT increased_stat, decreased_stat FROM natures WHERE id = ?", (nature_id,))
            nature_row = cursor.fetchone()
            nature = dict(nature_row) if nature_row else None

        calculated_stats = calculator.calculate_status(base_stats, level, evs, ivs, nature)

        return jsonify(calculated_stats), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/calculate/damage', methods=['POST'])
def calculate_damage_api():
    """ダメージ計算を行い、結果を返す。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        attacker_level = int(data['attacker_level'])
        attack_stat = int(data['attack_stat'])
        defender_hp = int(data['defender_hp'])
        defense_stat = int(data['defense_stat'])
        move_id = int(data['move_id'])
        defender_id = int(data['defender_id'])

        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT power, type, category FROM moves WHERE id = ?", (move_id,))
            move_info = cursor.fetchone()
            if not move_info:
                return jsonify({'error': 'Move not found'}), 404
            move_power, move_type, move_category = move_info

            cursor.execute("SELECT type1, type2 FROM pokemons WHERE id = ?", (defender_id,))
            defender_types = cursor.fetchone()
            if not defender_types:
                return jsonify({'error': 'Defender not found'}), 404
            defender_type1, defender_type2 = defender_types

        min_damage, max_damage = calculator.calculate_damage(
            attacker_level=attacker_level,
            move_power=move_power,
            attack_stat=attack_stat,
            defense_stat=defense_stat,
            move_type=move_type,
            defender_type1=defender_type1,
            defender_type2=defender_type2
        )

        if min_damage > 0:
            min_hits_to_ko = math.ceil(defender_hp / max_damage) if max_damage > 0 else float('inf')
            max_hits_to_ko = math.ceil(defender_hp / min_damage) if min_damage > 0 else float('inf')
        else:
            min_hits_to_ko = float('inf')
            max_hits_to_ko = float('inf')

        return jsonify({
            'min_damage': min_damage,
            'max_damage': max_damage,
            'min_damage_percent': round((min_damage / defender_hp) * 100, 1) if defender_hp > 0 else 0,
            'max_damage_percent': round((max_damage / defender_hp) * 100, 1) if defender_hp > 0 else 0,
            'min_hits_to_ko': min_hits_to_ko,
            'max_hits_to_ko': max_hits_to_ko
        }), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --- F-08: 疑似対戦シミュレーション (Step-by-step) ---

@api_bp.route('/simulations', methods=['POST'])
def create_simulation():
    """新しい対戦シミュレーションセッションを作成する。"""
    data = request.get_json()
    if not data or 'party1_id' not in data or 'party2_id' not in data:
        return jsonify({'error': 'Invalid data: party1_id and party2_id are required.'}), 400

    try:
        party1_id = int(data['party1_id'])
        party2_id = int(data['party2_id'])

        service = PartyService()
        party1 = service.get_by_id(party1_id)
        party2 = service.get_by_id(party2_id)

        if not party1 or not party2:
            return jsonify({'error': 'One or both parties not found.'}), 404

        sim_id = str(uuid.uuid4())
        sim = simulator.BattleSimulator(party1, party2, party1_id, party2_id)
        simulations[sim_id] = sim
        
        sim.start_selection()

        return jsonify({'simulation_id': sim_id, 'state': sim.get_state()}), 201

    except Exception as e:
        print(f"Error in create_simulation: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/simulations/<sim_id>', methods=['GET'])
def get_simulation_state(sim_id):
    """指定したシミュレーションの状態を取得する。"""
    sim = simulations.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found'}), 404
    return jsonify(sim.get_state()), 200

@api_bp.route('/simulations/<sim_id>/select', methods=['POST'])
def set_simulation_selection(sim_id):
    """シミュレーションの選出を決定する。"""
    sim = simulations.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found'}), 404

    data = request.get_json()
    if not data or 'selection1' not in data or 'selection2' not in data:
        return jsonify({'error': 'Invalid data: selection1 and selection2 are required.'}), 400

    try:
        selection1 = [int(i) for i in data['selection1']]
        selection2 = [int(i) for i in data['selection2']]
        
        sim.set_selection(selection1, selection2)
        return jsonify(sim.get_state()), 200

    except Exception as e:
        print(f"Error in set_simulation_selection: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/simulations/<sim_id>/next_turn', methods=['POST'])
def advance_simulation_turn(sim_id):
    """シミュレーションを1ターン進める。"""
    sim = simulations.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        sim.next_turn()
        return jsonify(sim.get_state()), 200

    except Exception as e:
        print(f"Error in advance_simulation_turn: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --- F-12: 分析ダッシュボード (Analysis Dashboard) ---

@api_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """ダッシュボードに表示するための主要な分析データをまとめて取得する。"""
    try:
        service = DashboardService()
        dashboard_data = service.get_dashboard_data()
        return jsonify(dashboard_data), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard/customization', methods=['GET'])
def get_customization_data():
    """指定されたポケモンのカスタマイズ（技・持ち物・テラス）ランキングを取得する。"""
    pokemon_name = request.args.get('pokemon_name')
    if not pokemon_name:
        return jsonify({'error': 'pokemon_name query parameter is required.'}), 400
    
    try:
        service = DashboardService()
        customization_data = service.get_customization_data(pokemon_name)
        return jsonify(customization_data), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500