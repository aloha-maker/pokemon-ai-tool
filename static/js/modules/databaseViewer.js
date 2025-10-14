export class DatabaseViewer {
    constructor() {
        this.tableSelect = document.getElementById('table-select');
        this.keywordInput = document.getElementById('search-keyword');
        this.searchButton = document.getElementById('search-button');
        this.resultCount = document.getElementById('result-count');
        this.tableHead = document.getElementById('result-table-head');
        this.tableBody = document.getElementById('result-table-body');
        this.paginationContainer = document.getElementById('pagination-container');

        this.currentPage = 1;
        this.perPage = 50;

        this.init();
    }

    async init() {
        if (!this.tableSelect) return; // このページでない場合は何もしない

        await this.populateTableSelect();
        this.searchButton.addEventListener('click', () => {
            this.currentPage = 1;
            this.performSearch();
        });
        
        // 初期表示として最初のテーブルのデータを表示
        if (this.tableSelect.options.length > 0) {
            this.performSearch();
        }
    }

    async populateTableSelect() {
        try {
            const response = await fetch('/api/db/tables');
            const tables = await response.json();
            this.tableSelect.innerHTML = '';
            tables.forEach(table => {
                const option = document.createElement('option');
                option.value = table;
                option.textContent = table;
                this.tableSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching table list:', error);
        }
    }

    async performSearch() {
        const tableName = this.tableSelect.value;
        const keyword = this.keywordInput.value;

        if (!tableName) return;

        try {
            const response = await fetch(`/api/db/search?table=${tableName}&keyword=${keyword}&page=${this.currentPage}&per_page=${this.perPage}`);
            const data = await response.json();

            if (data.error) {
                alert(`Error: ${data.error}`);
                return;
            }
            
            this.renderTable(data);
            this.renderPagination(data.total);

        } catch (error) {
            console.error('Error performing search:', error);
        }
    }

    renderTable(data) {
        // Clear previous results
        this.tableHead.innerHTML = '';
        this.tableBody.innerHTML = '';
        this.resultCount.textContent = `${data.total}件の結果`;

        if (data.records.length === 0) {
            this.tableBody.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">データが見つかりません。</td></tr>';
            return;
        }

        // Render header
        const headerRow = document.createElement('tr');
        data.columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        this.tableHead.appendChild(headerRow);

        // Render body
        data.records.forEach(record => {
            const row = document.createElement('tr');
            data.columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = record[col];
                row.appendChild(td);
            });
            this.tableBody.appendChild(row);
        });
    }

    renderPagination(total) {
        this.paginationContainer.innerHTML = '';
        const totalPages = Math.ceil(total / this.perPage);

        if (totalPages <= 1) return;

        const ul = document.createElement('ul');
        ul.className = 'pagination pagination-sm';

        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            const a = document.createElement('a');
            a.className = 'page-link';
            a.href = '#';
            a.textContent = i;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = i;
                this.performSearch();
            });
            li.appendChild(a);
            ul.appendChild(li);
        }
        this.paginationContainer.appendChild(ul);
    }
}
