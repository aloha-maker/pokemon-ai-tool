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

// ポケモン名に基づいて、技と特性のデータリストを動的に更新する
export async function updatePokemonDatalists(pokemonName, pokemons) {
    const pokemon = pokemons.find(p => p.name_ja === pokemonName);
    const abilityDatalist = document.getElementById('ability-datalist');
    const moveDatalist = document.getElementById('move-datalist');

    if (!abilityDatalist || !moveDatalist) return;

    // ポケモンが見つからない場合はリストをクリア
    if (!pokemon) {
        abilityDatalist.innerHTML = '';
        moveDatalist.innerHTML = '';
        return;
    }

    try {
        const [abilitiesRes, movesRes] = await Promise.all([
            fetch(`/api/pokemon/${pokemon.id}/abilities`),
            fetch(`/api/pokemon/${pokemon.id}/moves`)
        ]);

        if (!abilitiesRes.ok || !movesRes.ok) {
            throw new Error('Failed to fetch pokemon specific data');
        }

        const abilities = await abilitiesRes.json();
        const moves = await movesRes.json();

        // 特性データリストの更新
        abilityDatalist.innerHTML = '';
        abilities.forEach(ability => {
            const option = document.createElement('option');
            option.value = ability.name_ja || ability.name;
            abilityDatalist.appendChild(option);
        });

        // 技データリストの更新
        moveDatalist.innerHTML = '';
        moves.forEach(move => {
            const option = document.createElement('option');
            option.value = move.name_ja || move.name;
            moveDatalist.appendChild(option);
        });

    } catch (error) {
        console.error('Error updating datalists:', error);
        abilityDatalist.innerHTML = '';
        moveDatalist.innerHTML = '';
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
    };
    const moveSelects = document.querySelectorAll('.move-select');

    try {
        const requests = Object.values(resources).map(res => fetch(`/api/master/${res}`));
        const responses = await Promise.all(requests);

        for(const res of responses) {
            if (!res.ok) throw new Error(`Failed to fetch master data: ${res.statusText}`);
        }

        const dataPromises = responses.map(res => res.json());
        const [pokemons, types, items, natures] = await Promise.all(dataPromises);

        // ポケモン名のdatalistを生成
        let pokemonDatalist = document.getElementById('pokemon-datalist');
        if (pokemonDatalist === null) {
            pokemonDatalist = document.createElement('datalist');
            pokemonDatalist.id = 'pokemon-datalist';
            document.body.appendChild(pokemonDatalist);
        }
        pokemonDatalist.innerHTML = '';
        pokemons.forEach(pokemon => {
            const option = document.createElement('option');
            option.value = pokemon.name_ja || pokemon.name;
            pokemonDatalist.appendChild(option);
        });
        
        // アイテム用のdatalistを生成
        let itemDatalist = document.getElementById('item-datalist');
        if (itemDatalist === null) {
            itemDatalist = document.createElement('datalist');
            itemDatalist.id = 'item-datalist';
            document.body.appendChild(itemDatalist);
        }
        itemDatalist.innerHTML = '';
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.name_ja || item.name;
            itemDatalist.appendChild(option);
        });

        // 技と特性の空のdatalistを生成
        if (!document.getElementById('ability-datalist')) {
            const abilityDatalist = document.createElement('datalist');
            abilityDatalist.id = 'ability-datalist';
            document.body.appendChild(abilityDatalist);
        }
        if (!document.getElementById('move-datalist')) {
            const moveDatalist = document.createElement('datalist');
            moveDatalist.id = 'move-datalist';
            document.body.appendChild(moveDatalist);
        }

        // ポケモン入力フィールドのイベントリスナーを設定
        const pokemonMasterInput = document.getElementById('pokemon-master-input');
        if (pokemonMasterInput) {
            pokemonMasterInput.addEventListener('change', (event) => {
                updatePokemonDatalists(event.target.value, pokemons);
            });
        }


        // ポケモン入力時にアイコンと種族値を更新する
        const pokemonInputs = document.querySelectorAll('.pokemon-input');
        if (pokemonInputs.length > 0 && pokemons) {
            const pokemonMap = new Map(pokemons.map(p => [p.name_ja, p]));

            pokemonInputs.forEach(input => {
                const updatePokemonInfo = (event) => {
                    const inputEl = event.target;
                    const pokemonName = inputEl.value;
                    const pokemon = pokemonMap.get(pokemonName);
                    const slot = inputEl.closest('.pokemon-slot');
                    
                    if (!slot) return;

                    const imageEl = slot.querySelector('.pokemon-image');
                    const speedStatEl = slot.querySelector('.speed-stat-value');

                    if (pokemon) {
                        // ポケモンアイコンを更新
                        if (imageEl) {
                            imageEl.src = `/static/pokemon_icons/${pokemon.name_ja}.png`;
                            imageEl.alt = pokemon.name_ja;
                        }
                        // すばやさ種族値を更新
                        if (speedStatEl) {
                            speedStatEl.textContent = `S: ${pokemon.speed}`;
                            speedStatEl.classList.remove('text-muted');
                        }
                    } else {
                        // ポケモンが見つからない場合はリセット
                        if (imageEl) {
                            const slotIndex = slot.dataset.slotIndex || '?';
                            imageEl.src = `https://placehold.co/96x96/333/ccc?text=P${slotIndex}`;
                            imageEl.alt = '';
                        }
                        if (speedStatEl) {
                            speedStatEl.textContent = 'S: --';
                            speedStatEl.classList.add('text-muted');
                        }
                    }
                };

                input.addEventListener('input', updatePokemonInfo);
                input.addEventListener('change', updatePokemonInfo);
            });
        }

        populateSelect('pokemon-master-id', pokemons, 'ポケモンを選択');
        populateSelect('tera-type-id', types, 'テラスタイプを選択');
        populateSelect('held-item-id', items, '持ち物を選択', { dataAttribute: { name: 'itemName', value: 'name' } });
        populateSelect('nature-id', natures, '性格を選択');
        
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

        // Add event listener for item inputs to update icon
        const itemInputs = document.querySelectorAll('.item-input');
        if (itemInputs.length > 0 && items) {
            const itemMap = new Map(items.map(item => [item.name_ja, item.name]));

            itemInputs.forEach(input => {
                const updateItemIcon = (event) => {
                    const inputEl = event.target;
                    const inputValue = inputEl.value;
                    const iconElement = inputEl.parentElement.querySelector('.item-icon');
                    const englishName = itemMap.get(inputValue);

                    if (iconElement) {
                        if (englishName) {
                            // アイコンのファイル名は name カラムの値 (e.g., light_ball)
                            iconElement.src = `/static/item_icons/${englishName}.png`;
                            iconElement.alt = inputValue;
                        } else {
                            // 一致するものがなければプレースホルダーに戻す
                            iconElement.src = 'https://placehold.co/24x24/333/ccc?text=?';
                            iconElement.alt = '持ち物アイコン';
                        }
                    }
                };
                // 入力時とフォーカスが外れた時の両方でイベントを発火させる
                input.addEventListener('input', updateItemIcon);
                input.addEventListener('change', updateItemIcon);
            });
        }

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