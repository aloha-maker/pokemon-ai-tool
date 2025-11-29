export class MastarData {
    constructor() {
        this.typesList = [];
        this.itemsList = [];
        this.naturesList = [];
        this.CONSTANTS = {
            MY_PARTY: "my-party",
            OPPONENT_PARTY: "opponent-party"
        };
    }

    static async createAndLoad() {
        const instance = new MastarData();
        await instance.init(); // ★ ここでロード完了を待つ
        return instance;
    }

    async init() {
        await this.loadMasterData();
    }

    async loadMasterData() {
        try {
            const [typesRes, itemsRes, naturesRes] = await Promise.all([
                fetch('/api/master/types'),
                fetch('/api/master/items'),
                fetch('/api/master/natures')
            ]);
            const typesData = await typesRes.json();
            if (typesData.status === 'success') {
                this.typesList = typesData.data.types;
            }
            const itemsData = await itemsRes.json();
            if (itemsData.status === 'success') {
                this.itemsList = itemsData.data.items;
            }
            const naturesData = await naturesRes.json();
            if (naturesData.status === 'success') {
                this.naturesList = naturesData.data.natures;
            }
        } catch (error) {
            console.error("Failed to load master data:", error);
        }
    }
}
