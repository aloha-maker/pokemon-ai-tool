// itemEditor.js - 持ち物編集機能

import { escapeHTML, showAlert } from './utils.js';
import { initFormSelects } from './formHelpers.js';

export class ItemEditor {
    constructor() {
        this.modal = document.getElementById('item-editor-modal');
        this.itemList = document.getElementById('item-list');
        this.form = document.getElementById('item-form');
        this.itemIdField = document.getElementById('item-id');
        this.itemNameField = document.getElementById('item-name');
        this.formTitle = document.getElementById('item-form-title');
        this.cancelEditBtn = document.getElementById('cancel-item-edit-btn');
        this.alertEl = document.getElementById('item-editor-alert');
        
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', () => {
            this.resetForm();
            this.loadItems();
        });

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        if (this.cancelEditBtn) {
            this.cancelEditBtn.addEventListener('click', () => this.resetForm());
        }
    }

    async loadItems() {
        try {
            const response = await fetch('/api/master/items');
            if (!response.ok) throw new Error('持ち物リストの取得に失敗しました。');
            const items = await response.json();

            this.itemList.innerHTML = '';
            if (items.length === 0) {
                this.itemList.innerHTML = '<div class="list-group-item text-muted">登録されている持ち物はありません。</div>';
                return;
            }

            items.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.className = 'list-group-item d-flex justify-content-between align-items-center';
                itemEl.innerHTML = `
                    <span>${escapeHTML(item.name_ja)}</span>
                    <div>
                        <button class="btn btn-sm btn-outline-light edit-item-btn" data-id="${item.id}" data-name="${escapeHTML(item.name_ja)}"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger delete-item-btn" data-id="${item.id}"><i class="bi bi-trash"></i></button>
                    </div>
                `;
                this.itemList.appendChild(itemEl);
            });

            this.attachActionListeners();

        } catch (error) {
            showAlert(this.alertEl.id, error.message, 'danger');
        }
    }

    attachActionListeners() {
        this.itemList.querySelectorAll('.edit-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleEditClick(e));
        });
        this.itemList.querySelectorAll('.delete-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDeleteClick(e));
        });
    }

    handleEditClick(event) {
        const id = event.currentTarget.dataset.id;
        const name = event.currentTarget.dataset.name;
        
        this.itemIdField.value = id;
        this.itemNameField.value = name;
        this.formTitle.textContent = '持ち物編集';
        this.cancelEditBtn.style.display = 'inline-block';
        this.itemNameField.focus();
    }

    async handleDeleteClick(event) {
        const id = event.currentTarget.dataset.id;
        if (confirm(`この持ち物を本当に削除しますか?`)) {
            try {
                const response = await fetch(`/api/items/${id}`, { method: 'DELETE' });
                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || '削除に失敗しました。');
                }

                showAlert(this.alertEl.id, '持ち物を削除しました。', 'success');
                await this.loadItems();
                await initFormSelects();

            } catch (error) {
                showAlert(this.alertEl.id, `削除失敗: ${error.message}`, 'danger');
            }
        }
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        const id = this.itemIdField.value;
        const name = this.itemNameField.value.trim();

        if (!name) {
            showAlert(this.alertEl.id, '持ち物名を入力してください。', 'warning');
            return;
        }

        const url = id ? `/api/items/${id}` : '/api/items';
        const method = id ? 'PUT' : 'POST';
        const body = JSON.stringify({ name_ja: name });

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: body
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || '保存に失敗しました。');
            }

            showAlert(this.alertEl.id, `持ち物を${id ? '更新' : '追加'}しました。`, 'success');
            this.resetForm();
            await this.loadItems();
            await initFormSelects();

        } catch (error) {
            showAlert(this.alertEl.id, `保存失敗: ${error.message}`, 'danger');
        }
    }

    resetForm() {
        this.form.reset();
        this.itemIdField.value = '';
        this.formTitle.textContent = '新規持ち物登録';
        this.cancelEditBtn.style.display = 'none';
        this.alertEl.style.display = 'none';
    }
}