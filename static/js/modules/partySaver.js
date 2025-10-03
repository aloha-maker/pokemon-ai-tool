export class PartySaver {
    constructor() {
        this.savePartyBtn = document.getElementById('save-party-button');
        this.resultModalEl = document.getElementById('result-modal');
        this.resultModal = this.resultModalEl ? new bootstrap.Modal(this.resultModalEl) : null;
        this.resultButtons = document.querySelectorAll('#result-modal [data-result]');

        if (this.savePartyBtn && this.resultModal) {
            this.init();
        }
    }

    init() {
        this.savePartyBtn.addEventListener('click', () => {
            this.resultModal.show();
        });

        this.resultButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const result = e.currentTarget.dataset.result;
                this.saveParty(result);
                this.resultModal.hide();
            });
        });
    }

    gatherPartyData() {
        // This function will gather all the data from the form.
        // For now, it's a placeholder.
        console.log("Gathering party data...");
        const myPartySlots = document.querySelectorAll('#my-party-display .pokemon-slot');
        const opponentPartySlots = document.querySelectorAll('#opponent-party-display .pokemon-slot');

        const getSlotData = (slot) => {
            const pokemonName = slot.querySelector('.pokemon-input')?.value || null;
            const itemId = slot.querySelector('.item-select')?.value || null;
            const teraTypeId = slot.querySelector('.tera-type-select')?.value || null;
            // More details like ability, moves, pp will be fetched from pokemonDetailEditor's state.
            return { pokemonName, itemId, teraTypeId };
        };

        const myParty = Array.from(myPartySlots).map(getSlotData);
        const opponentParty = Array.from(opponentPartySlots).map(getSlotData);

        return { myParty, opponentParty };
    }

    async saveParty(result) {
        console.log(`Saving party with result: ${result}`);
        const partyData = this.gatherPartyData();
        
        // Here I would need to get the full details (ability, moves, etc.)
        // and send them to a new API endpoint, e.g., /api/history/add
        
        // For now, just log the data.
        console.log(partyData);
        alert(`パーティ情報を保存しました。結果: ${result}`);
    }
}
