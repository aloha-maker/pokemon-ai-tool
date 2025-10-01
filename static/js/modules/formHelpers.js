// formHelpers.js - フォーム関連のヘルパー関数

export function populateSelect(elementId, data, defaultOptionText) {
    const select = document.getElementById(elementId);
    if (!select) return;

    select.innerHTML = '';
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = defaultOptionText;
    select.appendChild(defaultOption);

    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name_ja || item.name;
        select.appendChild(option);
    });
}

export async function updateAbilitiesForPokemon(pokemonId) {
    const abilitySelect = document.getElementById('ability-id');
    if (pokemonId) {
        try {
            const response = await fetch(`/api/pokemon/${pokemonId}/abilities`);
            if (!response.ok) throw new Error('Failed to fetch abilities');
            const abilities = await response.json();
            populateSelect('ability-id', abilities, '特性を選択');
        } catch (error) {
            console.error('Error fetching abilities:', error);
            populateSelect('ability-id', [], '特性の取得に失敗');
        }
    } else {
        populateSelect('ability-id', [], '先にポケモンを選択');
    }
}

export async function initFormSelects() {
    const resources = {
        'pokemon-master-id': 'pokemons',
        'tera-type-id': 'types',
        'held-item-id': 'items',
        'nature-id': 'natures'
    };
    const moveSelects = document.querySelectorAll('.move-select');

    try {
        const requests = Object.values(resources).map(res => fetch(`/api/master/${res}`));
        const moveRequest = fetch('/api/master/moves');
        const responses = await Promise.all([...requests, moveRequest]);

        for(const res of responses) {
            if (!res.ok) throw new Error(`Failed to fetch master data: ${res.statusText}`);
        }

        const dataPromises = responses.map(res => res.json());
        const [pokemons, types, items, natures, moves] = await Promise.all(dataPromises);

        // オートコンプリート用のdatalistを生成
        if (document.getElementById('pokemon-datalist') === null) {
            const pokemonDatalist = document.createElement('datalist');
            pokemonDatalist.id = 'pokemon-datalist';
            const pokemonNames = new Set();
            pokemons.forEach(pokemon => {
                const name = pokemon.name_ja || pokemon.name;
                if (name) pokemonNames.add(name);
            });

            pokemonNames.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                pokemonDatalist.appendChild(option);
            });
            document.body.appendChild(pokemonDatalist);
        }

        populateSelect('pokemon-master-id', pokemons, 'ポケモンを選択');
        populateSelect('tera-type-id', types, 'テラスタイプを選択');
        populateSelect('held-item-id', items, '持ち物を選択');
        populateSelect('nature-id', natures, '性格を選択');

        moveSelects.forEach(select => {
            populateSelect(select.id, moves, '技を選択');
        });

        // ポケモン選択時に特性を動的に読み込むイベントリスナー
        const pokemonMasterSelect = document.getElementById('pokemon-master-id');
        if (pokemonMasterSelect) {
            pokemonMasterSelect.addEventListener('change', (event) => {
                updateAbilitiesForPokemon(event.target.value);
            });
        }

        console.log("フォームの選択肢を初期化しました。");

    } catch (error) {
        console.error("マスターデータの初期化に失敗しました:", error);
        alert("フォームの初期化に失敗しました。ページをリロードしてみてください。");
    }
}
