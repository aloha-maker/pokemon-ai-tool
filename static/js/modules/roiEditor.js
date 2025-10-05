// roiEditor.js - ROI(関心領域)編集機能

export class ROIEditor {
    constructor() {
        this.modal = document.getElementById('roi-editor-modal');
        this.canvas = document.getElementById('roi-canvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.selector = document.getElementById('roi-selector');
        this.saveBtn = document.getElementById('save-roi-btn');
        this.coordsEl = document.getElementById('roi-coords');
        this.imageUpload = document.getElementById('roi-image-upload');
        
        this.roiConfig = {};
        this.roiImage = new Image();
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', () => this.initEditor());
        
        if (this.canvas) {
            this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
            this.canvas.addEventListener('mousemove', (e) => this.draw(e));
            this.canvas.addEventListener('mouseup', (e) => this.stopDrawing(e));
            this.canvas.addEventListener('mouseleave', (e) => this.stopDrawing(e));
        }
        
        if (this.selector) {
            this.selector.addEventListener('change', () => {
                this.drawRoiRects();
                this.updateCoordsDisplay();
            });
        }
        
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveRoiConfig());
        }
        
        if (this.imageUpload) {
            this.imageUpload.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.roiImage.src = URL.createObjectURL(file);
                }
            });
        }

        const addRoiBtn = document.getElementById('add-roi-btn');
        const newRoiNameInput = document.getElementById('new-roi-name');

        if (addRoiBtn && newRoiNameInput && this.selector) {
            addRoiBtn.addEventListener('click', () => {
                const newRoiName = newRoiNameInput.value.trim();
                if (newRoiName) {
                    const exists = Array.from(this.selector.options).some(option => option.value === newRoiName);
                    if (!exists) {
                        const newOption = new Option(newRoiName, newRoiName);
                        this.selector.add(newOption);
                        newRoiNameInput.value = '';
                        this.selector.value = newRoiName;
                        this.selector.dispatchEvent(new Event('change'));
                    } else {
                        alert('そのROI名はすでに存在します。');
                    }
                } else {
                    alert('新しいROIの名前を入力してください。');
                }
            });
        }
    }

    async initEditor() {
        try {
            const configResponse = await fetch('/api/roi/config');
            this.roiConfig = await configResponse.json();

            // roiConfigのキーを元にドロップダウンを動的に生成
            this.selector.innerHTML = ''; // 既存のオプションをクリア
            for (const key in this.roiConfig) {
                if (key === 'reference_resolution') continue;
                const option = new Option(key, key);
                this.selector.add(option);
            }

            this.roiImage.onload = () => {
                this.canvas.width = 1920;
                this.canvas.height = 1080;
                this.drawRoiRects();
                this.updateCoordsDisplay();
            };
            
            const currentSrc = document.getElementById('capture-image').src;
            if (currentSrc && !currentSrc.includes('placehold.co')) {
                this.roiImage.src = currentSrc;
            } else {
                try {
                    const imgPathResponse = await fetch('/api/roi/image_path');
                    const imgPathData = await imgPathResponse.json();
                    this.roiImage.src = imgPathData.image_path + '?t=' + new Date().getTime();
                } catch (e) {
                    console.warn("Could not load default ROI image. Using placeholder.");
                    this.roiImage.src = 'https://placehold.co/1920x1080/0c0a24/e5bfff?text=No+Preview+Available';
                }
            }

        } catch (error) {
            console.error("Error initializing ROI editor:", error);
        }
    }

    drawRoiRects() {
        if (!this.roiImage.src || this.roiImage.naturalWidth === 0) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.roiImage, 0, 0, this.canvas.width, this.canvas.height);
        this.ctx.lineWidth = 2;
        
        for (const key in this.roiConfig) {
            if (key === 'reference_resolution') continue;
            const [x, y, w, h] = this.roiConfig[key];
            if (key === this.selector.value) {
                this.ctx.strokeStyle = '#00ff00'; // Green
            } else {
                this.ctx.strokeStyle = '#ff0000'; // Red
            }
            this.ctx.strokeRect(x, y, w, h);
        }
    }

    startDrawing(e) {
        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        this.startX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        this.startY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
    }

    draw(e) {
        if (!this.isDrawing) return;
        const rect = this.canvas.getBoundingClientRect();
        const currentX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        const currentY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        this.drawRoiRects();
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.strokeRect(this.startX, this.startY, currentX - this.startX, currentY - this.startY);
    }

    stopDrawing(e) {
        if (!this.isDrawing) return;
        this.isDrawing = false;
        const selectedRoi = this.selector.value;
        const rect = this.canvas.getBoundingClientRect();
        const endX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        const endY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        const x = Math.min(this.startX, endX);
        const y = Math.min(this.startY, endY);
        const w = Math.abs(this.startX - endX);
        const h = Math.abs(this.startY - endY);
        
        if (w > 0 && h > 0) {
            this.roiConfig[selectedRoi] = [Math.round(x), Math.round(y), Math.round(w), Math.round(h)];
        }
        this.drawRoiRects();
        this.updateCoordsDisplay();
    }

    updateCoordsDisplay() {
        const selectedRoi = this.selector.value;
        if (this.roiConfig[selectedRoi]) {
            const [x, y, w, h] = this.roiConfig[selectedRoi];
            this.coordsEl.textContent = `[${x}, ${y}, ${w}, ${h}]`;
        }
    }

    async saveRoiConfig() {
        this.roiConfig.reference_resolution = {
            width: 1920,
            height: 1080
        };
        
        try {
            const response = await fetch('/api/roi/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.roiConfig)
            });
            const data = await response.json();
            
            if (response.ok) {
                alert('ROI設定を保存しました。');
            } else {
                alert(`保存に失敗しました: ${data.error}`);
            }
        } catch (error) {
            console.error("Error saving ROI config:", error);
            alert('保存中にエラーが発生しました。');
        }
    }
}
