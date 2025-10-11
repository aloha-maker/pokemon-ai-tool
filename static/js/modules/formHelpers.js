// formHelpers.js - フォーム関連のヘルパー関数

export function populateSelect(elementId, data, defaultOptionText, options = {}) {
    const select = document.getElementById(elementId);
    if (!select) return;

    const fragment = document.createDocumentFragment();

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = defaultOptionText;
    fragment.appendChild(defaultOption);

    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name_ja || item.name;
        if (options.dataAttribute) {
            option.dataset[options.dataAttribute.name] = item[options.dataAttribute.value];
        }
        fragment.appendChild(option);
    });

    select.innerHTML = '';
    select.appendChild(fragment);
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


document.addEventListener('DOMContentLoaded', () => {
    const loadButton = document.getElementById('load-master-data-btn');
    if (loadButton) {
        loadButton.addEventListener('click', initFormSelects);
    }
});

export async function initFormSelects() {
    const button = document.getElementById('load-master-data-btn');
    const spinner = button.querySelector('.spinner-border');
    const icon = button.querySelector('.button-icon');
    const text = button.querySelector('.button-text');

    // --- 開始処理 ---
    button.disabled = true;
    spinner.classList.remove('d-none');
    icon.classList.add('d-none');
    text.textContent = '読込中...';

    const resources = {
        'pokemon-master-id': 'pokemons',
        'tera-type-id': 'types',
        'held-item-id': 'items',
        'nature-id': 'natures',
        'ability-id': 'abilities'
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
        const [pokemons, types, items, natures, abilities, moves] = await Promise.all(dataPromises);

        // オートコンプリート用のdatalistを生成
        let pokemonDatalist = document.getElementById('pokemon-datalist');
        if (pokemonDatalist === null) {
            pokemonDatalist = document.createElement('datalist');
            pokemonDatalist.id = 'pokemon-datalist';
            document.body.appendChild(pokemonDatalist);
        }

        // 既存の選択肢をクリア
        pokemonDatalist.innerHTML = '';

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

        // アイテム用のdatalistを生成
        let itemDatalist = document.getElementById('item-datalist');
        if (itemDatalist === null) {
            itemDatalist = document.createElement('datalist');
            itemDatalist.id = 'item-datalist';
            document.body.appendChild(itemDatalist);
        }

        // 既存の選択肢をクリア
        itemDatalist.innerHTML = '';

        const itemNames = new Set();
        items.forEach(item => {
            const name = item.name_ja || item.name;
            if (name) itemNames.add(name);
        });

        itemNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            itemDatalist.appendChild(option);
        });

        // 特性用のdatalistを生成
        let abilityDatalist = document.getElementById('ability-datalist');
        if (abilityDatalist === null) {
            abilityDatalist = document.createElement('datalist');
            abilityDatalist.id = 'ability-datalist';
            document.body.appendChild(abilityDatalist);
        }
        abilityDatalist.innerHTML = '';
        const abilityNames = new Set();
        abilities.forEach(ability => {
            const name = ability.name_ja || ability.name;
            if (name) abilityNames.add(name);
        });
        abilityNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            abilityDatalist.appendChild(option);
        });

        // 技用のdatalistを生成
        let moveDatalist = document.getElementById('move-datalist');
        if (moveDatalist === null) {
            moveDatalist = document.createElement('datalist');
            moveDatalist.id = 'move-datalist';
            document.body.appendChild(moveDatalist);
        }
        moveDatalist.innerHTML = '';
        const moveNames = new Set();
        moves.forEach(move => {
            const name = move.name_ja || move.name;
            if (name) moveNames.add(name);
        });
        moveNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            moveDatalist.appendChild(option);
        });

        populateSelect('pokemon-master-id', pokemons, 'ポケモンを選択');
        populateSelect('tera-type-id', types, 'テラスタイプを選択');
        populateSelect('held-item-id', items, '持ち物を選択', { dataAttribute: { name: 'itemName', value: 'name' } });
        populateSelect('nature-id', natures, '性格を選択');
        populateSelect('ability-id', abilities, '特性を選択');

        moveSelects.forEach(select => {
            populateSelect(select.id, moves, '技を選択');
        });

        // Populate item dropdowns on the main page
        const itemSelects = document.querySelectorAll('.item-select');
        if (itemSelects.length > 0 && items) {
            itemSelects.forEach(select => {
                populateSelect(select.id, items, '持ち物', { dataAttribute: { name: 'itemName', value: 'name' } });

                // Add event listener to update icon
                select.addEventListener('change', (event) => {
                    const selectEl = event.target;
                    const selectedOption = selectEl.options[selectEl.selectedIndex];
                    const itemName = selectedOption.dataset.itemName;
                    const iconElement = selectEl.parentElement.querySelector('.item-icon');

                    if (iconElement) {
                        if (itemName) {
                            iconElement.src = `/static/item_icons/${itemName}.png`;
                            iconElement.alt = selectedOption.textContent;
                        } else {
                            // Reset to placeholder if no item is selected
                            iconElement.src = 'https://placehold.co/24x24/333/ccc?text=?';
                            iconElement.alt = '持ち物アイコン';
                        }
                    }
                });
            });
        }

        // Populate tera type dropdowns on the main page
        const teraTypeSelects = document.querySelectorAll('.tera-type-select');
        if (teraTypeSelects.length > 0 && types) {
            teraTypeSelects.forEach(select => {
                populateSelect(select.id, types, 'テラスタイプ', { dataAttribute: { name: 'typeName', value: 'name' } });

                // Add event listener to update icon
                select.addEventListener('change', (event) => {
                    const selectEl = event.target;
                    const selectedOption = selectEl.options[selectEl.selectedIndex];
                    const typeName = selectedOption.dataset.typeName;
                    const iconElement = selectEl.parentElement.querySelector('.tera-type-icon');

                    if (iconElement) {
                        if (typeName) {
                            iconElement.src = `/static/type_icons/${typeName}.png`;
                            iconElement.alt = selectedOption.textContent;
                        } else {
                            iconElement.src = 'https://placehold.co/24x24/333/ccc?text=?';
                            iconElement.alt = 'テラスタイプアイコン';
                        }
                    }
                });
            });
        }

        // ポケモン選択時に特性を動的に読み込むイベントリスナーは不要になったためコメントアウト
        // const pokemonMasterSelect = document.getElementById('pokemon-master-id');
        // if (pokemonMasterSelect) {
        //     pokemonMasterSelect.addEventListener('change', (event) => {
        //         updateAbilitiesForPokemon(event.target.value);
        //     });
        // }

        console.log("フォームの選択肢を初期化しました。");

        // --- 成功時のUI更新 ---
        button.classList.remove('btn-secondary');
        button.classList.add('btn-success');
        text.textContent = '読込完了';
        icon.className = 'button-icon bi bi-check-circle-fill'; // アイコンを変更

    } catch (error) {
        console.error("マスターデータの初期化に失敗しました:", error);
        alert("フォームの初期化に失敗しました。ページをリロードして再試行してください。");

        // --- 失敗時のUI更新 ---
        button.disabled = false; // 再試行可能にする
        button.classList.remove('btn-secondary');
        button.classList.add('btn-danger');
        text.textContent = '再試行';
        icon.className = 'button-icon bi bi-exclamation-triangle-fill';

    } finally {
        // --- 終了処理 ---
        spinner.classList.add('d-none');
        icon.classList.remove('d-none');
    }
}