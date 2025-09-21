# F-05 育成済みポケモン管理 実装手順書

## 1. 概要

このドキュメントは、追加要件 `F-05 育成済みポケモン管理` 機能を実装するための具体的な手順を定義するものです。
ユーザーが育成したポケモンの情報をデータベースに登録・参照・編集・削除するための、データベース設計、バックエンドAPI、フロントエンドUIの各実装タスクについて記述します。

---

## 2. 実装タスク一覧

- [ ] **データベース設計:** `trained_pokemons` テーブルを新規作成する。
- [ ] **バックエンドAPI実装:** 育成済みポケモンのCRUD操作を行うAPIエンドポイントを作成する。
- [ ] **フロントエンドUI実装:** 育成済みポケモンの一覧表示、および新規登録・編集を行うためのWebページを作成する。

---

## 3. ステップ1: データベース設計

まず、育成済みポケモンの情報を格納するための新しいテーブル `trained_pokemons` をデータベースに作成します。

**アクション:**
1. 以下のSQL文を `data/schema.sql` ファイルの末尾に追記してください。

**SQL (`data/schema.sql` に追記):**
```sql
-- F-05: 育成済みポケモン管理テーブル
CREATE TABLE IF NOT EXISTS trained_pokemons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL, -- pokemons.csv のID
    nickname TEXT,
    level INTEGER NOT NULL DEFAULT 50,
    tera_type_id INTEGER, -- types.csv のID
    ability_id INTEGER, -- abilities.csv のID
    nature_id INTEGER, -- natures.csv のID
    held_item_id INTEGER, -- items.csv のID
    move1_id INTEGER, -- moves.csv のID
    move2_id INTEGER,
    move3_id INTEGER,
    move4_id INTEGER,
    ev_hp INTEGER DEFAULT 0,
    ev_atk INTEGER DEFAULT 0,
    ev_def INTEGER DEFAULT 0,
    ev_spa INTEGER DEFAULT 0,
    ev_spd INTEGER DEFAULT 0,
    ev_spe INTEGER DEFAULT 0,
    iv_hp INTEGER DEFAULT 31,
    iv_atk INTEGER DEFAULT 31,
    iv_def INTEGER DEFAULT 31,
    iv_spa INTEGER DEFAULT 31,
    iv_spd INTEGER DEFAULT 31,
    iv_spe INTEGER DEFAULT 31,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pokemon_id) REFERENCES pokemons(id),
    FOREIGN KEY (tera_type_id) REFERENCES types(id),
    FOREIGN KEY (ability_id) REFERENCES abilities(id),
    FOREIGN KEY (nature_id) REFERENCES natures(id),
    FOREIGN KEY (held_item_id) REFERENCES items(id),
    FOREIGN KEY (move1_id) REFERENCES moves(id),
    FOREIGN KEY (move2_id) REFERENCES moves(id),
    FOREIGN KEY (move3_id) REFERENCES moves(id),
    FOREIGN KEY (move4_id) REFERENCES moves(id)
);
```

2. データベースのセットアップスクリプト `scripts/setup_database.py` を再実行し、テーブルを反映させます。

---

## 4. ステップ2: バックエンドAPI実装

育成済みポケモンの情報を操作するためのCRUD (作成, 読み取り, 更新, 削除) APIを実装します。

**アクション:**
- `src/ui/routes.py` を編集し、以下のエンドポイントを追加します。
- データベース操作ロジックは `src/database/manager.py` に追記・実装します。

**APIエンドポイント仕様:**

| メソッド | エンドポイント                  | 説明                                   |
| :------- | :------------------------------ | :------------------------------------- |
| `GET`    | `/api/trained-pokemons`         | 登録済みのポケモンを一覧で取得する。   |
| `POST`   | `/api/trained-pokemons`         | 新しいポケモンを登録する。             |
| `GET`    | `/api/trained-pokemons/<id>`    | 指定したIDのポケモンの詳細を取得する。 |
| `PUT`    | `/api/trained-pokemons/<id>`    | 指定したIDのポケモン情報を更新する。   |
| `DELETE` | `/api/trained-pokemons/<id>`    | 指定したIDのポケモンを削除する。       |

**実装ファイル:**
- `src/ui/routes.py`: Flaskのルーティングを定義します。
- `src/database/manager.py`: 各APIに対応するデータベース操作（SELECT, INSERT, UPDATE, DELETE）を実装します。

---

## 5. ステップ3: フロントエンドUI実装

ユーザーがブラウザ上で育成済みポケモンを管理するためのUIを作成します。

**アクション:**
- 新しいHTMLファイル `templates/trained_pokemon_management.html` を作成します。
- `static/main.js` に、APIと通信して画面を更新するためのJavaScriptコードを追記します。

### 5.1. 新規HTMLファイルの作成

**ファイル名:** `templates/trained_pokemon_management.html`

**内容:**
- 登録済みポケモンの一覧を表示するテーブル。
- 新規登録フォーム（モーダルウィンドウまたは別ページ）。フォームには、要件定義にあるすべての入力項目（ニックネーム、技、持ち物など）を含めます。
- ポケモン名、技、特性などの選択肢は、バックエンドからマスターデータを取得し、`<select>` タグのドロップダウンとして表示するとUXが向上します。

**HTML骨子:**
```html
<!-- templates/trained_pokemon_management.html -->
{% extends "index.html" %}
{% block content %}
<div class="container">
    <h2>育成済みポケモン管理</h2>
    <button id="show-add-pokemon-modal">新規登録</button>

    <table id="trained-pokemon-list">
        <thead>
            <tr>
                <th>ポケモン名</th>
                <th>ニックネーム</th>
                <th>技</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            <!-- JavaScriptで一覧をここに描画 -->
        </tbody>
    </table>

    <!-- 新規登録・編集用モーダル (最初は非表示) -->
    <div id="pokemon-form-modal" style="display:none;">
        <h3>ポケモン情報</h3>
        <form id="pokemon-form">
            <!-- ポケモン名、ニックネーム、技、持ち物などのフォーム要素 -->
            <input type="hidden" id="pokemon-id">
            <label>ポケモン:</label><select id="pokemon-name"></select><br>
            <label>ニックネーム:</label><input type="text" id="nickname"><br>
            <!-- 他の努力値、個体値、技などのフォーム要素をここに追加 -->
            <button type="submit">保存</button>
        </form>
    </div>
</div>
{% endblock %}
```

### 5.2. JavaScriptの実装

**ファイル名:** `static/main.js`

**実装内容:**
1.  **一覧表示機能:**
    - ページ読み込み時に `GET /api/trained-pokemons` を呼び出し、取得したデータをテーブルに描画する。
2.  **新規登録機能:**
    - 「新規登録」ボタンクリックでフォームモーダルを表示する。
    - フォーム送信時に `POST /api/trained-pokemons` を呼び出し、成功したら一覧を更新する。
3.  **編集機能:**
    - 「編集」ボタンクリックで、対象のポケモンの情報をフォームに読み込み、モーダルを表示する。
    - フォーム送信時に `PUT /api/trained-pokemons/<id>` を呼び出し、成功したら一覧を更新する。
4.  **削除機能:**
    - 「削除」ボタンクリックで確認ダイアログを表示し、OKなら `DELETE /api/trained-pokemons/<id>` を呼び出し、成功したら一覧を更新する。
