import sqlite3
import os
import json
import time

class DatabaseManager:
    """
    データベースへの接続と操作を管理するクラス。
    アプリケーションの他モジュールは、このクラスを通じてデータベースにアクセスする。
    """
    def __init__(self, db_path=None):
        """
        DatabaseManagerを初期化する。
        db_pathが指定されない場合、プロジェクトルートからの相対パスを使用する。
        """
        if db_path is None:
            # プロジェクトのルートディレクトリを基準にDBファイルのパスを構築
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'pokemon_ai.db')
        else:
            self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """コンテキストマネージャの開始時にデータベースに接続する。"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了時にデータベース接続を閉じる。"""
        self.close()

    def connect(self):
        """データベースに接続する。"""
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                print(f"Error connecting to database: {e}")
                raise

    def close(self):
        """データベース接続を閉じる。"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_cursor(self):
        """
        接続からカーソルを取得する。
        接続が存在しない場合は、まず接続を試みる。
        """
        self.connect()
        return self.conn.cursor()

    def get_pokemon_by_name(self, name: str) -> dict | None:
        """ポケモン名から詳細データを取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM pokemons WHERE name_ja = ? OR name = ?", (name, name))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_move_by_name(self, name: str) -> dict | None:
        """技名から詳細データを取得する。"""
        cursor = self.get_cursor()
        # 完全一致または前方一致で検索（例：「１０まんばりき」）
        cursor.execute("SELECT * FROM moves WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_battle_history(self, limit: int = 50) -> list[dict]:
        """対戦履歴の一覧を取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM battle_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        # JSONデータをパースして返す
        logs = []
        for row in rows:
            log_data = dict(row)
            if log_data.get('battle_data'):
                try:
                    log_data['battle_data'] = json.loads(log_data['battle_data'])
                except (json.JSONDecodeError, TypeError):
                    log_data['battle_data'] = {} # パース失敗時は空のdict
            if log_data.get('opponent_party'):
                try:
                    log_data['opponent_party'] = json.loads(log_data['opponent_party'])
                except (json.JSONDecodeError, TypeError):
                    log_data['opponent_party'] = {} # パース失敗時は空のdict
            logs.append(log_data)
        return logs

    def get_battle_log_by_id(self, log_id: int) -> dict | None:
        """IDを指定して対戦ログを取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM battle_logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        log_data = dict(row)
        # battle_data と opponent_party はJSON文字列なのでパースする
        if log_data.get('battle_data'):
            try:
                log_data['battle_data'] = json.loads(log_data['battle_data'])
            except (json.JSONDecodeError, TypeError):
                log_data['battle_data'] = {}
        if log_data.get('opponent_party'):
            try:
                log_data['opponent_party'] = json.loads(log_data['opponent_party'])
            except (json.JSONDecodeError, TypeError):
                log_data['opponent_party'] = {}
            
        return log_data

    def get_all_battle_logs(self) -> list[dict]:
        """
        すべての対戦履歴をDBから取得する。
        JSONデータはパースして返す。
        """
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM battle_logs ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            log_data = dict(row)
            if log_data.get('battle_data'):
                try:
                    log_data['battle_data'] = json.loads(log_data['battle_data'])
                except (json.JSONDecodeError, TypeError):
                    log_data['battle_data'] = {}
            if log_data.get('opponent_party'):
                try:
                    log_data['opponent_party'] = json.loads(log_data['opponent_party'])
                except (json.JSONDecodeError, TypeError):
                    log_data['opponent_party'] = {}
            logs.append(log_data)
        return logs

    def get_battle_stats(self) -> dict:
        """勝率などの統計データを計算して取得する。"""
        cursor = self.get_cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM battle_logs")
        total_matches = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as wins FROM battle_logs WHERE result = 'win'")
        total_wins = cursor.fetchone()['wins']

        win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        return {
            "total_matches": total_matches,
            "total_wins": total_wins,
            "win_rate": round(win_rate, 1)
        }

    def get_latest_battle_id_for_today(self, date_str: str) -> str | None:
        """
        指定された日付の最新のバトルIDを取得する (例: BATTLE-20231027-005)
        """
        cursor = self.get_cursor()
        pattern = f'BATTLE-{date_str}-%'
        cursor.execute(
            "SELECT battle_id FROM battles WHERE battle_id LIKE ? ORDER BY battle_id DESC LIMIT 1",
            (pattern,)
        )
        row = cursor.fetchone()
        return row['battle_id'] if row else None

    def add_battle_log(self, log_data: dict) -> int:
        """
        対戦履歴を `battle_logs` テーブルに追加する。
        log_dataには result, opponent_party, my_party, my_selection が含まれることを想定。
        戻り値は追加されたレコードのID。
        """
        cursor = self.get_cursor()

        # my_partyとmy_selectionをbattle_dataにJSONとして格納
        battle_data = {
            "my_party": log_data.get('my_party'),
            "my_selection": log_data.get('my_selection')
        }

        # my_party_idは暫定的に1とする。将来的にはpartiesテーブルへの登録とID取得が必要。
        my_party_id = 1 

        cursor.execute(
            "INSERT INTO battle_logs (result, opponent_party, my_party_id, battle_data) VALUES (?, ?, ?, ?)",
            (
                log_data['result'],
                json.dumps(log_data.get('opponent_party')),
                my_party_id,
                json.dumps(battle_data)
            )
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_battle_log_from_video(self, video_task_id: str, turn_data: dict) -> int:
        """
        動画解析結果から対戦ログを `battle_logs` テーブルに追加する。
        video_task_id とターンごとのデータ(turn_data)を受け取る。
        戻り値は追加されたレコードのID。
        """
        cursor = self.get_cursor()

        # battle_data をJSON文字列に変換
        battle_data_json = json.dumps(turn_data, ensure_ascii=False, indent=2)

        # TODO: 動画からパーティを特定する機能が実装されるまで、暫定的に1をセットする
        my_party_id = 1 

        # 新しいログを挿入
        cursor.execute(
            "INSERT INTO battle_logs (video_task_id, battle_data, result, my_party_id) VALUES (?, ?, ?, ?)",
            (
                video_task_id,
                battle_data_json,
                'unknown', # 解析直後は結果不明
            )
        )
        self.conn.commit()
        return cursor.lastrowid

    def save_battle_result(self, my_party_id: int, opponent_party: list[str], result: str) -> int:
        """
        正規化されたテーブル構成で対戦結果を保存する。
        """
        if result not in ['win', 'lose']:
            raise ValueError("result must be either 'win' or 'lose'")

        cursor = self.get_cursor()
        try:
            # 1. battles テーブルに対戦記録を作成
            # battle_format はUIにないため 'シングル' 固定とする
            cursor.execute(
                "INSERT INTO battles (result, battle_format) VALUES (?, ?)",
                (result, 'シングル')
            )
            battle_id = cursor.lastrowid

            # 2. 自分のパーティを parties_log に記録
            my_pokemon_names = self.get_party_pokemon_names(my_party_id)
            my_party_log_data = []
            for name in my_pokemon_names:
                # 自分のポケモンは pokemon_id を NULL にする
                my_party_log_data.append((battle_id, None, name, 0, 0))
            
            cursor.executemany(
                "INSERT INTO parties_log (battle_id, pokemon_id, pokemon_name, is_opponent, is_selected) VALUES (?, ?, ?, ?, ?)",
                my_party_log_data
            )

            # 3. 相手のパーティを pokemons_log と parties_log に記録
            opponent_party_log_data = []
            for name in opponent_party:
                # 3a. pokemons_log に同じポケモンがいないか確認 (詳細不明なので名前のみで判断)
                cursor.execute(
                    "SELECT pokemon_id FROM pokemons_log WHERE pokemon_name = ? AND nickname IS NULL AND moves IS NULL AND terastal_type IS NULL AND item IS NULL AND ability IS NULL", 
                    (name,)
                )
                row = cursor.fetchone()
                
                if row:
                    pokemon_id = row['pokemon_id']
                else:
                    # 3b. いなければ pokemons_log に新規登録
                    cursor.execute("INSERT INTO pokemons_log (pokemon_name) VALUES (?)", (name,))
                    pokemon_id = cursor.lastrowid
                
                opponent_party_log_data.append((battle_id, pokemon_id, name, 1, 0))

            cursor.executemany(
                "INSERT INTO parties_log (battle_id, pokemon_id, pokemon_name, is_opponent, is_selected) VALUES (?, ?, ?, ?, ?)",
                opponent_party_log_data
            )

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def save_battle_result_with_log(self, battle_id: str, my_party_id: int, my_party: list[dict], opponent_party: list[dict], result: str, raw_events: list[dict]) -> str:
        """
        正規化されたテーブル構成で対戦結果とリアルタイムOCRログを保存する。
        提供された battle_id を使用して battles テーブルにレコードを作成または更新する。
        """
        if result not in ['win', 'lose']:
            raise ValueError("result must be either 'win' or 'lose'")
        if not battle_id or not battle_id.startswith("BATTLE-"):
            raise ValueError("Invalid battle_id format")

        cursor = self.get_cursor()

        # --- マスターデータを事前に一括で取得 ---
        types_map = {row['id']: row['name_ja'] for row in self.get_master_data_by_resource('types')}
        abilities_map = {row['id']: row['name_ja'] for row in self.get_master_data_by_resource('abilities')}
        moves_map = {row['id']: row['name_ja'] for row in self.get_master_data_by_resource('moves')}

        try:
            # 1. battles テーブルに対戦記録を作成または更新
            cursor.execute(
                "INSERT OR IGNORE INTO battles (battle_id, result, battle_format) VALUES (?, ?, ?)",
                (battle_id, result, 'シングル')
            )
            cursor.execute(
                "UPDATE battles SET result = ?, battle_format = ? WHERE battle_id = ?",
                (result, 'シングル', battle_id)
            )

            # 2. 既存の関連ログを削除 (冪等性を保つため)
            cursor.execute("DELETE FROM parties_log WHERE battle_id = ?", (battle_id,))
            cursor.execute("DELETE FROM raw_battle_events WHERE battle_id = ?", (battle_id,))

            # 3. パーティ処理の内部関数
            def _process_party_log(party_list, is_opponent):
                parties_log_tuples = []
                for pokemon in party_list:
                    name = pokemon.get('name')
                    if not name: continue

                    item_name = pokemon.get('item')
                    tera_type_id = pokemon.get('terastal_type_id')
                    ability_id = pokemon.get('ability_id')

                    tera_type_name = types_map.get(int(tera_type_id)) if tera_type_id else None
                    ability_name = abilities_map.get(int(ability_id)) if ability_id else None
                    
                    move_ids = pokemon.get('moves', [])
                    move_names = [moves_map.get(int(move_id)) for move_id in move_ids if move_id in moves_map]
                    moves_json = json.dumps(move_names, ensure_ascii=False)

                    # pokemons_logに常に新しいレコードとして挿入
                    cursor.execute(
                        """INSERT INTO pokemons_log (pokemon_name, item, terastal_type, ability, moves)
                           VALUES (?, ?, ?, ?, ?)""",
                        (name, item_name, tera_type_name, ability_name, moves_json)
                    )
                    pokemon_id = cursor.lastrowid

                    is_selected = 1 if pokemon.get('is_selected') else 0
                    parties_log_tuples.append((battle_id, pokemon_id, name, 1 if is_opponent else 0, is_selected))
                return parties_log_tuples

            # 4. 自パーティと相手パーティのログを生成・保存
            my_parties_log_tuples = _process_party_log(my_party, is_opponent=False)
            if my_parties_log_tuples:
                cursor.executemany(
                    "INSERT INTO parties_log (battle_id, pokemon_id, pokemon_name, is_opponent, is_selected) VALUES (?, ?, ?, ?, ?)",
                    my_parties_log_tuples
                )

            opponent_parties_log_tuples = _process_party_log(opponent_party, is_opponent=True)
            if opponent_parties_log_tuples:
                cursor.executemany(
                    "INSERT INTO parties_log (battle_id, pokemon_id, pokemon_name, is_opponent, is_selected) VALUES (?, ?, ?, ?, ?)",
                    opponent_parties_log_tuples
                )

            # 5. 先発ポケモンをbattlesテーブルに記録
            my_starter = next((p['name'] for p in my_party if p.get('is_starter')), None)
            opponent_starter = next((p['name'] for p in opponent_party if p.get('is_starter')), None)

            if my_starter or opponent_starter:
                cursor.execute(
                    "UPDATE battles SET my_first_pokemon = ?, opponent_first_pokemon = ? WHERE battle_id = ?",
                    (my_starter, opponent_starter, battle_id)
                )

            # 6. raw_battle_events テーブルにリアルタイムログを記録
            if raw_events:
                event_log_data = [
                    (battle_id, event['sequence'], event['roi_name'], event['ocr_text'])
                    for event in raw_events
                ]
                cursor.executemany(
                    "INSERT INTO raw_battle_events (battle_id, sequence, roi_name, ocr_text) VALUES (?, ?, ?, ?)",
                    event_log_data
                )

            self.conn.commit()
            return battle_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def prepare_battle_log(self, my_party_id: int, opponent_party: list[str]) -> int:
        """
        対戦前のパーティ情報で `battle_logs` テーブルにレコードを作成する。
        resultは'unknown'で登録される。
        戻り値は追加されたレコードのID。
        """
        cursor = self.get_cursor()
        try:
            cursor.execute(
                "INSERT INTO battle_logs (my_party_id, opponent_party, result) VALUES (?, ?, ?)",
                (
                    my_party_id,
                    json.dumps(opponent_party, ensure_ascii=False),
                    'unknown'
                )
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_pokemons_by_names(self, names: list[str]) -> list[dict]:
        """複数のポケモン名から詳細データのリストを取得する。"""
        if not names:
            return []
        cursor = self.get_cursor()
        placeholders = ', '.join('?' for _ in names)
        query = f"SELECT * FROM pokemons WHERE name_ja IN ({placeholders}) OR name IN ({placeholders})"
        # name_jaとnameの両方で検索するため、リストを2回渡す
        params = names + names
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # --- F-05: 育成済みポケモン管理 (Trained Pokemons) ---

    def get_all_trained_pokemons(self) -> list[dict]:
        """登録済みのすべての育成済みポケモンを、関連情報と共に取得する。"""
        cursor = self.get_cursor()
        # 技関連のJOINは一覧では不要なため削除し、クエリを安定させる
        query = """
            SELECT
                tp.id,
                tp.nickname,
                tp.level,
                p.name_ja as pokemon_name,
                p.type1 as pokemon_type1,
                p.type2 as pokemon_type2,
                t.name_ja as tera_type_name,
                a.name_ja as ability_name,
                n.name_ja as nature_name,
                i.name_ja as item_name
            FROM
                trained_pokemons tp
            LEFT JOIN pokemons p ON tp.pokemon_id = p.id
            LEFT JOIN types t ON tp.tera_type_id = t.id
            LEFT JOIN abilities a ON tp.ability_id = a.id
            LEFT JOIN natures n ON tp.nature_id = n.id
            LEFT JOIN items i ON tp.held_item_id = i.id
            ORDER BY tp.updated_at DESC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_trained_pokemon_by_id(self, pokemon_id: int) -> dict | None:
        """IDで指定した育成済みポケモンの詳細データを取得する。技情報も詳細を含めて取得する。"""
        cursor = self.get_cursor()
        
        # trained_pokemons から基本情報を取得
        cursor.execute("SELECT * FROM trained_pokemons WHERE id = ?", (pokemon_id,))
        row = cursor.fetchone()
        if not row:
            return None
        pokemon_data = dict(row)

        # pokemons テーブルから追加情報を取得
        cursor.execute(
            "SELECT name_ja, type1, type2 FROM pokemons WHERE id = ?", 
            (pokemon_data['pokemon_id'],)
        )
        pokemon_master_data = cursor.fetchone()
        if pokemon_master_data:
            # フロントエンドが期待するキー 'pokemon_name' と、シミュレーションに必要なタイプ情報を追加
            pokemon_data['pokemon_name'] = pokemon_master_data['name_ja']
            pokemon_data['type1'] = pokemon_master_data['type1']
            pokemon_data['type2'] = pokemon_master_data['type2']

        # 持ち物名を取得
        if pokemon_data.get('held_item_id'):
            cursor.execute(
                "SELECT name_ja FROM items WHERE id = ?",
                (pokemon_data['held_item_id'],)
            )
            item_row = cursor.fetchone()
            if item_row:
                pokemon_data['item_name'] = item_row['name_ja']

        # 技情報を取得
        move_ids = [
            pokemon_data.get('move1_id'),
            pokemon_data.get('move2_id'),
            pokemon_data.get('move3_id'),
            pokemon_data.get('move4_id')
        ]
        
        moves_details = []
        for move_id in move_ids:
            if move_id:
                # 技のシミュレーションに必要な情報をすべて取得
                cursor.execute("SELECT id, name, type, category, power, accuracy FROM moves WHERE id = ?", (move_id,))
                move_row = cursor.fetchone()
                if move_row:
                    moves_details.append(dict(move_row))
        
        pokemon_data['moves'] = moves_details
        
        return pokemon_data

    def add_trained_pokemon(self, data: dict) -> int:
        """新しい育成済みポケモンをデータベースに登録する。"""
        cursor = self.get_cursor()
        
        try:
            # dataに値がない場合は登録対象から除外する
            insert_data = {k: v for k, v in data.items() if v is not None and v != '' and k != 'id'}
            columns = list(insert_data.keys())
            placeholders = ', '.join('?' for _ in columns)
            values = list(insert_data.values())
            
            query = f"""
                INSERT INTO trained_pokemons ({', '.join(columns)})
                VALUES ({placeholders})
            """
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_trained_pokemon(self, pokemon_id: int, data: dict) -> int:
        """指定したIDの育成済みポケモン情報を更新する。"""
        cursor = self.get_cursor()
        
        # 'id'キーを削除し、updated_atを更新
        data.pop('id', None)
        data['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

        try:
            # dataに値がない場合は更新対象から除外する
            update_data = {k: v for k, v in data.items() if v is not None and v != ''}
            if not update_data:
                return 0 # 更新対象がない

            set_clauses = [f"{col} = ?" for col in update_data.keys()]
            values = list(update_data.values())
            values.append(pokemon_id)

            query = f"""
                UPDATE trained_pokemons
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_trained_pokemon(self, pokemon_id: int) -> int:
        """指定したIDの育成済みポケモンを削除する。"""
        cursor = self.get_cursor()
        cursor.execute("DELETE FROM trained_pokemons WHERE id = ?", (pokemon_id,))
        self.conn.commit()
        return cursor.rowcount

    # --- F-06: パーティ管理 (Parties) ---

    def get_all_parties(self) -> list[dict]:
        """登録済みのすべてのパーティを、メンバー情報付きで取得する。"""
        cursor = self.get_cursor()
        
        # まずは全パーティを取得
        cursor.execute("SELECT * FROM parties ORDER BY updated_at DESC")
        parties = [dict(row) for row in cursor.fetchall()]
        
        # 各パーティのメンバーを取得
        for party in parties:
            party['members'] = self._get_party_members(party['id'])
            
        return parties

    def get_party_by_id(self, party_id: int) -> dict | None:
        """IDで指定したパーティの情報を、メンバー付きで取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM parties WHERE id = ?", (party_id,))
        party = cursor.fetchone()
        if not party:
            return None
        
        party_dict = dict(party)
        party_dict['members'] = self._get_party_members(party_id)
        return party_dict

    def _get_party_members(self, party_id: int) -> list[dict]:
        """指定されたパーティIDのメンバー（育成済みポケモン）の詳細リストを取得する。"""
        cursor = self.get_cursor()
        # まずはパーティに属する trained_pokemon_id と index を取得
        cursor.execute(
            "SELECT trained_pokemon_id, member_index FROM party_members WHERE party_id = ? ORDER BY member_index",
            (party_id,)
        )
        members_info = cursor.fetchall()
        
        # 各メンバーの詳細情報を取得
        members_details = []
        for info in members_info:
            # get_trained_pokemon_by_id を使って完全なデータを取得
            pokemon_details = self.get_trained_pokemon_by_id(info['trained_pokemon_id'])
            if pokemon_details:
                # シミュレータが必要とするかもしれないので、member_index も追加
                pokemon_details['member_index'] = info['member_index']
                members_details.append(pokemon_details)
                
        return members_details

    def add_party(self, data: dict) -> int:
        """新しいパーティをデータベースに登録する。"""
        cursor = self.get_cursor()
        
        try:
            # パーティ名を登録
            cursor.execute(
                "INSERT INTO parties (name, description) VALUES (?, ?)",
                (data['name'], data.get('description', ''))
            )
            party_id = cursor.lastrowid
            
            # パーティメンバーを登録
            members = data.get('members', [])
            if members:
                member_values = [
                    (party_id, member_id, index)
                    for index, member_id in enumerate(members)
                    if member_id is not None
                ]
                cursor.executemany(
                    "INSERT INTO party_members (party_id, trained_pokemon_id, member_index) VALUES (?, ?, ?)",
                    member_values
                )
            
            self.conn.commit()
            return party_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_party(self, party_id: int, data: dict) -> int:
        """指定したIDのパーティ情報を更新する。"""
        cursor = self.get_cursor()
        
        try:
            # パーティ名と説明を更新
            cursor.execute(
                "UPDATE parties SET name = ?, description = ?, updated_at = ? WHERE id = ?",
                (data['name'], data.get('description', ''), time.strftime('%Y-%m-%d %H:%M:%S'), party_id)
            )
            
            # 既存のメンバーを一旦削除
            cursor.execute("DELETE FROM party_members WHERE party_id = ?", (party_id,))
            
            # 新しいメンバーを登録
            members = data.get('members', [])
            if members:
                member_values = [
                    (party_id, member_id, index)
                    for index, member_id in enumerate(members)
                    if member_id is not None
                ]
                cursor.executemany(
                    "INSERT INTO party_members (party_id, trained_pokemon_id, member_index) VALUES (?, ?, ?)",
                    member_values
                )
            
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_party(self, party_id: int) -> int:
        """指定したIDのパーティを削除する。ON DELETE CASCADEによりメンバーも削除される。"""
        cursor = self.get_cursor()
        try:
            cursor.execute("DELETE FROM parties WHERE id = ?", (party_id,))
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_party_pokemon_names(self, party_id: int) -> list[str]:
        """指定されたパーティIDのポケモンの名前（日本語）のリストを取得する。"""
        cursor = self.get_cursor()
        query = """
            SELECT p.name_ja
            FROM party_members pm
            JOIN trained_pokemons tp ON pm.trained_pokemon_id = tp.id
            JOIN pokemons p ON tp.pokemon_id = p.id
            WHERE pm.party_id = ?
            ORDER BY pm.member_index
        """
        cursor.execute(query, (party_id,))
        rows = cursor.fetchall()
        return [row['name_ja'] for row in rows]

    def get_master_data_by_resource(self, resource: str) -> list[dict]:
        """指定されたリソース（テーブル名）からマスターデータをすべて取得する。"""
        if resource not in ['items', 'natures', 'abilities', 'moves', 'types', 'pokemons']:
            raise ValueError(f"Invalid resource: {resource}")
        
        cursor = self.get_cursor()
        # pokemonsテーブルはname_jaでソート
        order_column = 'name_ja' if resource == 'pokemons' else 'name'
        cursor.execute(f"SELECT * FROM {resource} ORDER BY {order_column}")
        return [dict(row) for row in cursor.fetchall()]

    def get_abilities_by_pokemon_id(self, pokemon_id: int) -> list[dict]:
        """指定されたポケモンIDが持つ特性をすべて取得する。"""
        cursor = self.get_cursor()
        query = """
            SELECT a.id, a.name, a.name_ja, a.description
            FROM abilities a
            JOIN pokemon_abilities pa ON a.id = pa.ability_id
            WHERE pa.pokemon_id = ?
        """
        cursor.execute(query, (pokemon_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_moves_by_type(self, move_type: str, category: str, limit: int = 10) -> list[dict]:
        """指定されたタイプとカテゴリの技を取得する（威力順）。"""
        cursor = self.get_cursor()
        query = """
            SELECT *
            FROM moves
            WHERE type = ? AND category = ? AND power > 0
            ORDER BY power DESC
            LIMIT ?
        """
        return [dict(row) for row in cursor.fetchall()]

    # --- Dashboard ---
    def get_dashboard_summary(self, season: int = None) -> dict:
        """ダッシュボードのサマリー情報を取得する。"""
        cursor = self.get_cursor()
        
        # 勝率
        base_query = "SELECT result, COUNT(*) as count FROM battles"
        params = []
        if season:
            base_query += " WHERE season = ?"
            params.append(season)
        base_query += " GROUP BY result"
        
        cursor.execute(base_query, params)
        results = {row['result']: row['count'] for row in cursor.fetchall()}
        
        wins = results.get('勝ち', 0)
        losses = results.get('負け', 0)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0

        # ランク推移
        rank_query = "SELECT battle_date, my_rank FROM battles"
        rank_params = []
        if season:
            rank_query += " WHERE season = ?"
            rank_params.append(season)
        rank_query += " ORDER BY battle_date ASC"
        cursor.execute(rank_query, rank_params)
        rank_history = [{'date': row['battle_date'], 'rank': row['my_rank']} for row in cursor.fetchall() if row['my_rank'] is not None]

        return {
            "win_rate": round(win_rate, 1),
            "wins": wins,
            "losses": losses,
            "total_matches": total,
            "rank_history": rank_history
        }

    def get_opponent_pokemon_ranking(self, limit: int = 10) -> list[dict]:
        """相手のパーティによく含まれるポケモンのランキングを取得する。"""
        cursor = self.get_cursor()
        query = """
            SELECT pokemon_name, COUNT(*) as count
            FROM parties_log
            WHERE is_opponent = 1
            GROUP BY pokemon_name
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_win_rate_by_opponent(self) -> list[dict]:
        """相手のポケモンごとの勝率を計算する。"""
        cursor = self.get_cursor()
        # このクエリは複雑になるため、複数ステップで実行するか、より洗練されたSQLが必要です。
        # ここでは簡略化のため、Pythonで処理します。
        cursor.execute("SELECT battle_id, pokemon_name FROM parties_log WHERE is_opponent = 1")
        opponent_pokemons = cursor.fetchall()
        
        cursor.execute("SELECT battle_id, result FROM battles")
        battle_results = {row['battle_id']: row['result'] for row in cursor.fetchall()}

        stats = {}
        for battle_id, name in opponent_pokemons:
            if name not in stats:
                stats[name] = {'wins': 0, 'losses': 0, 'total': 0}
            
            result = battle_results.get(battle_id)
            if result == '勝ち':
                stats[name]['wins'] += 1
            elif result == '負け':
                stats[name]['losses'] += 1
            stats[name]['total'] += 1

        win_rate_list = []
        for name, data in stats.items():
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            win_rate_list.append({
                'pokemon_name': name,
                'win_rate': round(win_rate, 1),
                'total_matches': data['total']
            })
        
        return win_rate_list

    def get_my_pokemon_selection_rate(self) -> list[dict]:
        """自分のポケモンの選出率を計算する。"""
        cursor = self.get_cursor()
        query = """
            SELECT 
                pokemon_name, 
                SUM(CASE WHEN is_selected = 1 THEN 1 ELSE 0 END) as selected_count,
                COUNT(*) as total_count
            FROM parties_log
            WHERE is_opponent = 0
            GROUP BY pokemon_name
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        selection_rates = []
        for row in rows:
            rate = (row['selected_count'] / row['total_count'] * 100) if row['total_count'] > 0 else 0
            selection_rates.append({
                'pokemon_name': row['pokemon_name'],
                'selection_rate': round(rate, 1),
                'selected_count': row['selected_count'],
                'total_count': row['total_count']
            })
        
        return sorted(selection_rates, key=lambda x: x['selection_rate'], reverse=True)

    def get_selection_pattern_win_rate(self) -> list[dict]:
        """自分の選出パターン（3体）ごとの勝率を計算する。"""
        cursor = self.get_cursor()
        query = """
            SELECT p.battle_id, p.pokemon_name, b.result
            FROM parties_log p
            JOIN battles b ON p.battle_id = b.battle_id
            WHERE p.is_opponent = 0 AND p.is_selected = 1
            ORDER BY p.battle_id, p.pokemon_name
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        patterns = {}
        from collections import defaultdict
        battle_selections = defaultdict(list)
        for row in rows:
            battle_selections[row['battle_id']].append(row['pokemon_name'])

        for battle_id, selection in battle_selections.items():
            if len(selection) == 3:
                pattern = tuple(sorted(selection))
                if pattern not in patterns:
                    patterns[pattern] = {'wins': 0, 'losses': 0, 'total': 0}
                
                # battlesテーブルから結果を取得（既にある情報を使う）
                cursor.execute("SELECT result FROM battles WHERE battle_id = ?", (battle_id,))
                result = cursor.fetchone()['result']

                if result == '勝ち':
                    patterns[pattern]['wins'] += 1
                elif result == '負け':
                    patterns[pattern]['losses'] += 1
                patterns[pattern]['total'] += 1

        win_rate_list = []
        for pattern, data in patterns.items():
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            win_rate_list.append({
                'pattern': list(pattern),
                'win_rate': round(win_rate, 1),
                'total_matches': data['total']
            })

        return sorted(win_rate_list, key=lambda x: x['total_matches'], reverse=True)

    def get_opponent_pokemon_customization_ranking(self, pokemon_name: str, limit: int = 5) -> dict:
        """指定された相手ポケモンの技、持ち物、テラスタイプの採用率ランキングを取得する。"""
        cursor = self.get_cursor()
        
        # pokemon_id を取得
        cursor.execute("SELECT pokemon_id FROM pokemons_log WHERE pokemon_name = ?", (pokemon_name,))
        pokemon_ids = [row['pokemon_id'] for row in cursor.fetchall()]
        if not pokemon_ids:
            return {'moves': [], 'items': [], 'terastal_types': []}

        placeholders = ', '.join('?' for _ in pokemon_ids)

        # 技
        # movesはJSON配列なので、この方法では集計できない。要件を見直すか、テーブル構造の変更が必要。
        # ここでは仮実装として、movesカラムのテキスト自体をカウントする。
        moves_query = f"""
            SELECT moves, COUNT(*) as count
            FROM pokemons_log
            WHERE pokemon_id IN ({placeholders}) AND moves IS NOT NULL
            GROUP BY moves
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(moves_query, pokemon_ids + [limit])
        moves = [dict(row) for row in cursor.fetchall()]

        # 持ち物
        items_query = f"""
            SELECT item, COUNT(*) as count
            FROM pokemons_log
            WHERE pokemon_id IN ({placeholders}) AND item IS NOT NULL
            GROUP BY item
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(items_query, pokemon_ids + [limit])
        items = [dict(row) for row in cursor.fetchall()]

        # テラスタイプ
        terastal_query = f"""
            SELECT terastal_type, COUNT(*) as count
            FROM pokemons_log
            WHERE pokemon_id IN ({placeholders}) AND terastal_type IS NOT NULL
            GROUP BY terastal_type
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(terastal_query, pokemon_ids + [limit])
        terastal_types = [dict(row) for row in cursor.fetchall()]

        return {
            'moves': moves,
            'items': items,
            'terastal_types': terastal_types
        }




