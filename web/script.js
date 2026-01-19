async function generateContent() {
    const titleInput = document.getElementById('article-title');
    const urlInput = document.getElementById('article-url');
    const contentTextarea = document.getElementById('article-content');
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    const generateBtn = document.getElementById('generate-btn');

    const title = titleInput.value.trim();
    const url = urlInput.value.trim();
    const content = contentTextarea.value.trim();

    if (!content) {
        statusDiv.className = 'status error';
        statusDiv.textContent = 'Please enter the article content.';
        return;
    }

    // Disable button and show loading status
    generateBtn.disabled = true;
    statusDiv.className = 'status loading';
    statusDiv.textContent = 'Generating content... Please wait.';
    resultDiv.textContent = '';

    try {
        const result = await eel.generate_content(title, url, content)();

        if (result.success) {
            statusDiv.className = 'status success';
            statusDiv.textContent = 'Content generated successfully!';
            resultDiv.innerHTML = `
                <p>Title: <strong>${result.title}</strong></p>
                ${result.url ? `<p>URL: <a href="${result.url}" target="_blank">${result.url}</a></p>` : ''}
                <p>File saved: <strong>${result.filename}</strong></p>
                <p>Path: <code>${result.filepath}</code></p>
                ${result.s3_url ? `<p>S3 URL: <a href="${result.s3_url}" target="_blank">${result.s3_url}</a></p>` : ''}
                ${result.s3_warning ? `<p style="color: orange;">S3 Warning: ${result.s3_warning}</p>` : ''}
            `;
        } else {
            statusDiv.className = 'status error';
            statusDiv.textContent = 'Error occurred';
            resultDiv.textContent = result.error;
        }
    } catch (error) {
        statusDiv.className = 'status error';
        statusDiv.textContent = 'Error occurred';
        resultDiv.textContent = error.message || 'An unexpected error occurred.';
    } finally {
        generateBtn.disabled = false;
    }
}
