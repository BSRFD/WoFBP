let historyLoaded = false;
let lastUpdateCheck = Date.now();

// Fisher-Yates shuffle algorithm
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

async function fetchData() {
    try {
        const response = await fetch(`data.json?rand=${Date.now()}`);
        const data = await response.json();
        
        const dateElement = document.getElementById('date');
        const solutionElement = document.getElementById('solution');
        
        dateElement.textContent = data.date;
        solutionElement.textContent = data.solution;

        // Auto-refresh check
        if (Date.now() - lastUpdateCheck > 300000) {
            const freshCheck = await fetch(`data.json?rand=${Date.now()}`);
            const freshData = await freshCheck.json();
            if (freshData.date !== data.date) {
                window.location.reload(true);
            }
            lastUpdateCheck = Date.now();
        }

        // Click-to-copy functionality
        solutionElement.style.cursor = 'pointer';
        solutionElement.setAttribute('title', 'Click to copy');
        solutionElement.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(data.solution);
                showCopyFeedback('Copied to clipboard!');
            } catch (err) {
                console.error('Failed to copy:', err);
                showCopyFeedback('Failed to copy!');
            }
        });

        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = '';
        
        // Add timestamp to puzzle board
        const addedDate = data.added_utc ? new Date(data.added_utc) : null;
        if (addedDate) {
            const timeContainer = document.createElement('div');
            timeContainer.className = 'puzzle-timestamp';
            timeContainer.textContent = `Added: ${addedDate.toLocaleTimeString([], { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            })}`;
            puzzleDisplay.appendChild(timeContainer);
        }

        const words = data.solution.split(/\s+/);
        const allTiles = [];
        
        const wordContainer = document.createElement('div');
        wordContainer.className = 'word-container';

        words.forEach(word => {
            const wordRow = document.createElement('div');
            wordRow.className = 'word-row';
            
            [...word.toUpperCase()].forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordRow.appendChild(tile);
                allTiles.push(tile);
            });
            
            wordContainer.appendChild(wordRow);
        });

        puzzleDisplay.appendChild(wordContainer);

        shuffleArray(allTiles);
        allTiles.forEach((tile, index) => {
            setTimeout(() => {
                tile.classList.add('revealed');
            }, index * 50);
        });

    } catch (error) {
        console.error('Error:', error);
    }
}

function showCopyFeedback(message) {
    const feedback = document.createElement('div');
    feedback.className = 'copy-feedback';
    feedback.setAttribute('role', 'alert');
    feedback.setAttribute('aria-live', 'polite');
    feedback.textContent = message;
    
    // Clear existing feedback
    const existing = document.querySelector('.copy-feedback');
    if (existing) existing.remove();
    
    document.body.appendChild(feedback);
    
    // Force reflow to enable animation
    void feedback.offsetWidth;
    
    feedback.style.opacity = '1';
    
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => feedback.remove(), 500);
    }, 1500);
}

async function loadHistory() {
        try {
        const response = await fetch(`past-solutions.json?rand=${Date.now()}`); // ← Add cache bust
        const pastSolutions = await response.json();
        const list = document.getElementById('solution-list');
        
        list.innerHTML = pastSolutions
            .map(item => {
                const addedDate = item.added_utc ? new Date(item.added_utc) : null;
                const timeString = addedDate ? 
                    addedDate.toLocaleTimeString([], { 
                        hour: 'numeric', 
                        minute: '2-digit',
                        hour12: true 
                    }) : '';
                return `
                    <div class="history-solution-item">
                        <div class="history-date" ${timeString ? `title="Added at ${timeString}"` : ''}>
                            ${item.date}
                        </div>
                        <div class="history-solution">
                            ${item.solution}
                        </div>
                    </div>
                `;
            }).join('');

        historyLoaded = true;
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function toggleHistory() {
    const content = document.getElementById('history-content');
    const arrow = document.querySelector('.dropdown-arrow');
    
    content.classList.toggle('visible');
    arrow.style.transform = content.classList.contains('visible') 
        ? 'rotate(225deg)' 
        : 'rotate(45deg)';
    
    if (!historyLoaded && content.classList.contains('visible')) {
        loadHistory();
    }
}

document.addEventListener('DOMContentLoaded', fetchData);
