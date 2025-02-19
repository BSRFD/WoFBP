let historyLoaded = false;

async function fetchData() {
    try {
        const response = await fetch(`data.json?rand=${Date.now()}`);
        const data = await response.json();
        
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = '';
        
        const words = data.solution.split(/\s+/);
        let letterCount = 0;

        // Create all tiles first (hidden)
        for (const word of words) {
            const wordContainer = document.createElement('div');
            wordContainer.className = 'word-container';
            
            for (const letter of word.toUpperCase()) {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordContainer.appendChild(tile);
                letterCount++;
            }
            
            puzzleDisplay.appendChild(wordContainer);
            
            if (words.indexOf(word) < words.length - 1) {
                const space = document.createElement('div');
                space.className = 'word-space';
                puzzleDisplay.appendChild(space);
            }
        }

        // Reveal tiles sequentially
        const tiles = document.querySelectorAll('.letter-tile');
        tiles.forEach((tile, index) => {
            setTimeout(() => {
                tile.classList.add('revealed');
            }, index * 100); // 100ms between letters
        });

    } catch (error) {
        console.error('Error:', error);
    }
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