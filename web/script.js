async function generateContent() {
    const textArea = document.getElementById('english-text');
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    const generateBtn = document.getElementById('generate-btn');

    const text = textArea.value.trim();

    if (!text) {
        statusDiv.className = 'status error';
        statusDiv.textContent = 'Please enter some English text.';
        return;
    }

    // Disable button and show loading status
    generateBtn.disabled = true;
    statusDiv.className = 'status loading';
    statusDiv.textContent = 'Generating content... Please wait.';
    resultDiv.textContent = '';

    try {
        const result = await eel.generate_content(text)();

        if (result.success) {
            statusDiv.className = 'status success';
            statusDiv.textContent = 'Content generated successfully!';
            resultDiv.innerHTML = `
                <p>File saved: <strong>${result.filename}</strong></p>
                <p>Path: <code>${result.filepath}</code></p>
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
