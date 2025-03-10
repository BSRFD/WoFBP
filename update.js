let historyLoaded = false;

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

        // Add click-to-copy functionality
        solutionElement.style.cursor = 'pointer';
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
        
        const words = data.solution.split(/\s+/);
        const allTiles = [];
        
        // Create main container
        const wordContainer = document.createElement('div');
        wordContainer.className = 'word-container';

        // Create rows for each word
        words.forEach(word => {
            const wordRow = document.createElement('div');
            wordRow.className = 'word-row';
            
            // Create letter tiles
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

        // Shuffle and reveal tiles randomly
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
    feedback.textContent = message;
    
    document.body.appendChild(feedback);
    
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => feedback.remove(), 300);
    }, 1000);
}

async function loadHistory() {
    try {
        const response = await fetch('past-solutions.json');
        const pastSolutions = await response.json();
        const list = document.getElementById('solution-list');
        
        list.innerHTML = pastSolutions
            .reverse()
            .map(item => `
                <div class="history-solution-item">
                    <div class="history-date">${item.date}</div>
                    <div class="history-solution">${item.solution}</div>
                </div>
            `).join('');

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

// Initial load
document.addEventListener('DOMContentLoaded', fetchData);
