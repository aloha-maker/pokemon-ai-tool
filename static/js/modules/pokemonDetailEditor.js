export class PokemonDetailEditor {
    constructor() {
        this.modal = new bootstrap.Modal(document.getElementById('pokemon-details-modal'));
        this.pokemonSlots = document.querySelectorAll('.pokemon-slot');
        this.pokemonNameEl = document.getElementById('details-pokemon-name');
        this.currentSlot = null;

        this.init();
    }

    init() {
        this.pokemonSlots.forEach((slot, index) => {
            const gearIcon = slot.querySelector('.pokemon-settings-icon');
            if (gearIcon) {
                gearIcon.addEventListener('click', () => {
                    this.currentSlot = index;
                    this.openModalFor(slot);
                });
            }

            const img = slot.querySelector('img');
            if (img) {
                img.style.cursor = 'default';
            }
        });
    }

    openModalFor(slot) {
        const pokemonNameInput = slot.querySelector('.pokemon-input');
        const pokemonName = pokemonNameInput ? pokemonNameInput.value : '';

        if (!pokemonName) {
            alert('先にポケモン名を入力してください。');
            return;
        }

        this.pokemonNameEl.textContent = pokemonName;
        
        // For now, just open the modal.
        // Data population will be next.
        this.modal.show();
    }
}
