/**
 * Document Parser - Upload PDFs, get Markdown with LaTeX equations
 */
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const clearFile = document.getElementById('clearFile');
    const parseBtn = document.getElementById('parseBtn');
    const statusBar = document.getElementById('statusBar');
    const statusText = document.getElementById('statusText');
    const errorBar = document.getElementById('errorBar');
    const errorText = document.getElementById('errorText');
    const resultArea = document.getElementById('resultArea');
    const renderedView = document.getElementById('renderedView');
    const sourceView = document.getElementById('sourceView');
    const sourceCode = document.getElementById('sourceCode');
    const viewRendered = document.getElementById('viewRendered');
    const viewSource = document.getElementById('viewSource');
    const copyMd = document.getElementById('copyMd');

    let selectedFile = null;
    let markdownResult = '';

    // Check service health on load
    checkHealth();

    // Drop zone events
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) selectFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', () => { if (fileInput.files.length) selectFile(fileInput.files[0]); });

    clearFile.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        dropZone.style.display = '';
        resultArea.style.display = 'none';
        errorBar.style.display = 'none';
    });

    parseBtn.addEventListener('click', parseDocument);

    // View toggle
    viewRendered.addEventListener('click', () => {
        viewRendered.classList.add('active');
        viewSource.classList.remove('active');
        renderedView.style.display = '';
        sourceView.style.display = 'none';
    });
    viewSource.addEventListener('click', () => {
        viewSource.classList.add('active');
        viewRendered.classList.remove('active');
        sourceView.style.display = '';
        renderedView.style.display = 'none';
    });

    copyMd.addEventListener('click', () => {
        navigator.clipboard.writeText(markdownResult);
        copyMd.textContent = 'Copied!';
        setTimeout(() => { copyMd.textContent = 'Copy Markdown'; }, 2000);
    });

    function selectFile(file) {
        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatSize(file.size);
        fileInfo.style.display = 'flex';
        dropZone.style.display = 'none';
        errorBar.style.display = 'none';
        resultArea.style.display = 'none';
    }

    async function parseDocument() {
        if (!selectedFile) return;
        statusBar.style.display = 'flex';
        statusText.textContent = `Parsing ${selectedFile.name}...`;
        errorBar.style.display = 'none';
        resultArea.style.display = 'none';
        parseBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const resp = await fetch('/tvbo/api/parse', { method: 'POST', body: formData });
            const data = await resp.json();

            if (!data.success) {
                showError(data.error || 'Parsing failed');
                return;
            }

            // MinerU returns result in various formats — extract markdown
            markdownResult = extractMarkdown(data.data);
            sourceCode.textContent = markdownResult;

            // Render markdown
            renderedView.innerHTML = marked.parse(markdownResult);

            // Render LaTeX equations
            if (window.renderMathInElement) {
                renderMathInElement(renderedView, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '$', right: '$', display: false },
                        { left: '\\[', right: '\\]', display: true },
                        { left: '\\(', right: '\\)', display: false },
                    ],
                    throwOnError: false,
                });
            }

            resultArea.style.display = '';
            viewRendered.click();
        } catch (e) {
            showError('Request failed: ' + e.message);
        } finally {
            statusBar.style.display = 'none';
            parseBtn.disabled = false;
        }
    }

    function extractMarkdown(data) {
        // MinerU /file_parse returns various structures; handle common shapes
        if (typeof data === 'string') return data;
        if (data.md) return data.md;
        if (data.markdown) return data.markdown;
        if (Array.isArray(data)) {
            // Multiple files/pages — join their markdown
            return data.map(d => d.md || d.markdown || JSON.stringify(d, null, 2)).join('\n\n---\n\n');
        }
        return JSON.stringify(data, null, 2);
    }

    function showError(msg) {
        errorText.textContent = msg;
        errorBar.style.display = '';
    }

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    async function checkHealth() {
        const dot = document.getElementById('statusDot');
        const label = document.getElementById('serviceLabel');
        try {
            const resp = await fetch('/tvbo/api/parse/health');
            const data = await resp.json();
            if (data.success) {
                dot.classList.add('online');
                label.textContent = 'MinerU service online';
            } else {
                dot.classList.add('offline');
                label.textContent = 'MinerU service offline';
            }
        } catch {
            dot.classList.add('offline');
            label.textContent = 'MinerU service unavailable';
        }
    }
});
