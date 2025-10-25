// partyManagement.js - パーティ管理機能

import { escapeHTML, showAlert } from './utils.js';

export class PartyManagement {
    constructor() {
        this.modal = document.getElementById('party-management-modal');
        this.form = document.getElementById('party-form');
        this.partyList = document.getElementById('party-list');
        this.partyIdField = document.getElementById('party-id');
        this.partyNameField = document.getElementById('party-name');
        this.partyDescriptionField = document.getElementById('party-description');
        this.memberSelects = this.modal ? this.modal.querySelectorAll('.member-select') : [];
        this.formTitle = document.getElementById('party-form-title');
        this.submitButton = this.form ? this.form.querySelector('button[type="submit"]') : null;
        this.cancelEditBtn = document.getElementById('cancel-edit-btn');
        
        this.allTrainedPokemons = [];
        this.isDataLoaded = false;
        
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', async () => {
            if (!this.isDataLoaded) {
                await this.loadAndPopulateTrainedPokemons();
                this.isDataLoaded = true;
            } else {
                this.populateMemberSelects();
            }
            await this.loadAndDisplayParties();
        });

        this.form.addEventListener('submit', (e) => this.handlePartyFormSubmit(e));
        this.cancelEditBtn.addEventListener('click', () => this.resetPartyForm());
    }

    async loadAndPopulateTrainedPokemons() {
        try {
            const response = await fetch('/api/trained-pokemons');
            if (!response.ok) throw new Error('Failed to fetch trained pokemons');
            const responseData = await response.json();
            if (responseData.status !== 'success') {
                throw new Error(responseData.message || 'Failed to load trained pokemons');
            }
            this.allTrainedPokemons = responseData.data;
            this.populateMemberSelects();
        } catch (error) {
            console.error('Error loading trained pokemons:', error);
            this.partyList.innerHTML = '<div class="alert alert-danger">育成済みポケモンの読み込みに失敗しました。</div>';
        }
    }

    populateMemberSelects() {
        this.memberSelects.forEach(select => {
            const currentValue = select.value;
            select.innerHTML = '<option value="">メンバーを選択...</option>';
            this.allTrainedPokemons.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = `${p.nickname} (ID: ${p.id}:${p.pokemon_name})`;
                select.appendChild(option);
            });
            select.value = currentValue;
        });
    }

    async loadAndDisplayParties() {
        try {
            const response = await fetch('/api/parties');
            if (!response.ok) throw new Error('Failed to fetch parties');
            const responseData = await response.json();

            // 新しいレスポンス形式に対応
            if (responseData.status !== 'success') {
                throw new Error(responseData.message || 'Failed to load parties');
            }
            const parties = responseData.data;

            this.partyList.innerHTML = '';
            if (parties.length === 0) {
                this.partyList.innerHTML = '<p class="text-muted text-center">登録されているパーティはありません。</p>';
                return;
            }

            parties.forEach(party => {
                const partyCard = document.createElement('div');
                partyCard.className = 'col-lg-6 mb-3';
                let membersHtml = '<ul class="list-group list-group-flush small">';
                party.members.forEach(member => {
                    membersHtml += `<li class="list-group-item bg-transparent">${escapeHTML(member.nickname || member.pokemon_name)}</li>`;
                });
                if (party.members.length < 6) {
                    for(let i = party.members.length; i < 6; i++) {
                        membersHtml += `<li class="list-group-item bg-transparent text-muted">-</li>`;
                    }
                }
                membersHtml += '</ul>';

                partyCard.innerHTML = `
                    <div class="card h-100 glass-card-inside">
                        <div class="card-body p-2">
                            <h6 class="card-title">${escapeHTML(party.name)}</h6>
                            <p class="card-text text-muted small mb-1">${escapeHTML(party.description || '')}</p>
                            ${membersHtml}
                        </div>
                        <div class="card-footer bg-transparent border-top-0 text-end p-2">
                            <button class="btn btn-sm btn-outline-light edit-party-btn" data-id="${party.id}"><i class="bi bi-pencil"></i></button>
                            <button class="btn btn-sm btn-outline-danger delete-party-btn" data-id="${party.id}"><i class="bi bi-trash"></i></button>
                        </div>
                    </div>
                `;
                this.partyList.appendChild(partyCard);
            });

            this.partyList.querySelectorAll('.edit-party-btn').forEach(btn => {
                btn.addEventListener('click', (e) => this.handlePartyEditClick(e));
            });
            this.partyList.querySelectorAll('.delete-party-btn').forEach(btn => {
                btn.addEventListener('click', (e) => this.handlePartyDeleteClick(e));
            });

        } catch (error) {
            console.error('Error loading parties:', error);
            this.partyList.innerHTML = '<div class="alert alert-danger">パーティ一覧の読み込みに失敗しました。</div>';
        }
    }

    async handlePartyFormSubmit(event) {
        event.preventDefault();
        const partyId = this.partyIdField.value;
        const members = Array.from(this.memberSelects).reduce((acc, s) => {
            if (s.value) {
                acc.push(parseInt(s.value, 10));
            }
            return acc;
        }, []);

        const uniqueMembers = new Set(members);
        if (uniqueMembers.size < members.length) {
            alert('パーティに同じポケモンを複数選択することはできません。');
            return;
        }

        const partyData = {
            name: this.partyNameField.value,
            description: this.partyDescriptionField.value,
            members: members
        };

        const url = partyId ? `/api/parties/${partyId}` : '/api/parties';
        const method = partyId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(partyData)
            });

            const responseData = await response.json();
            if (!response.ok) {
                // 新しいエラー形式に対応
                const errorMessage = responseData.data ? responseData.data.message : 'Save failed';
                throw new Error(errorMessage);
            }

            this.resetPartyForm();
            await this.loadAndDisplayParties();

        } catch (error) {
            console.error('Error saving party:', error);
            alert(`保存に失敗しました: ${error.message}`);
        }
    }

    async handlePartyEditClick(event) {
        const partyId = event.currentTarget.dataset.id;
        try {
            const response = await fetch(`/api/parties/${partyId}`);
            if (!response.ok) throw new Error('Failed to fetch party details');
            const responseData = await response.json();

            // 新しいレスポンス形式に対応
            if (responseData.status !== 'success') {
                throw new Error(responseData.message || 'Failed to load party details');
            }
            const party = responseData.data;

            this.partyIdField.value = party.id;
            this.partyNameField.value = party.name;
            this.partyDescriptionField.value = party.description;
            
            this.memberSelects.forEach((select, index) => {
                const member = party.members.find(m => m.member_index === index);
                select.value = member ? member.id : '';
            });

            this.formTitle.textContent = 'パーティ編集';
            this.submitButton.textContent = '更新';
            this.cancelEditBtn.style.display = 'inline-block';

        } catch (error) {
            console.error(`Error fetching party ${partyId} for edit:`, error);
            alert('パーティ情報の読み込みに失敗しました。');
        }
    }

    async handlePartyDeleteClick(event) {
        const partyId = event.currentTarget.dataset.id;
        if (confirm(`ID: ${partyId} のパーティを本当に削除しますか?`)) {
            try {
                const response = await fetch(`/api/parties/${partyId}`, { method: 'DELETE' });
                const responseData = await response.json();

                if (!response.ok || responseData.status !== 'success') {
                    const errorMessage = responseData.data ? responseData.data.message : 'Failed to delete party';
                    throw new Error(errorMessage);
                }
                
                await this.loadAndDisplayParties();

            } catch (error) {
                console.error(`Error deleting party ${partyId}:`, error);
                alert('削除に失敗しました。');
            }
        }
    }

    resetPartyForm() {
        this.form.reset();
        this.partyIdField.value = '';
        this.formTitle.textContent = '新規パーティ登録';
        this.submitButton.textContent = '保存';
        this.cancelEditBtn.style.display = 'none';
    }
}
