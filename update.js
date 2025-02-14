async function fetchData() {
    try {
        // Cache-busted request for current solution
        const cacheBuster = `?rand=${Math.random().toString(36).substr(2, 9)}`;
        const response = await fetch(`data.json${cacheBuster}`);
        const data = await response.json();
        
        // Update main display
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        // Build puzzle tiles
        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = '';
        
        const words = data.solution.split(/\s+/);
        
        words.forEach((word, index) => {
            const wordContainer = document.createElement('div');
            wordContainer.className = 'word-container';
            
            word.split('').forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordContainer.appendChild(tile);
            });
            
            puzzleDisplay.appendChild(wordContainer);
            
            if(index < words.length - 1) {
                const space = document.createElement('div');
                space.className = 'word-space';
                puzzleDisplay.appendChild(space);
            }
        });

    } catch (error) {
        console.error('Error loading current puzzle:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('past-solutions.json');
        const pastSolutions = await response.json();
        const container = document.getElementById('solution-list');
        
        // Clear existing items
        container.innerHTML = '';
        
        // Create solution items matching current puzzle style
        pastSolutions.reverse().forEach(item => {
            const solutionItem = document.createElement('div');
            solutionItem.className = 'history-item';
            solutionItem.innerHTML = `
                <div class="info-box">
                    <span class="history-date">${item.date}</span>
                    <span class="history-solution">${item.solution}</span>
                </div>
            `;
            container.appendChild(solutionItem);
        });

    } catch (error) {
        console.error('Error loading history:', error);
        const container = document.getElementById('solution-list');
        container.innerHTML = '<div class="info-box">Error loading past solutions</div>';
    }
}

function toggleHistory() {
    const content = document.getElementById('history-content');
    const header = document.querySelector('.history-header');
    const arrow = document.querySelector('.dropdown-arrow');
    
    // Toggle visibility
    header.classList.toggle('active');
    content.classList.toggle('hidden');
    arrow.style.transform = content.classList.contains('hidden') 
        ? 'rotate(45deg)'
        : 'rotate(225deg)';
    
    // Load history only once when first opened
    if (!content.classList.contains('hidden') && document.getElementById('solution-list').children.length === 0) {
        loadHistory();
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', fetchData);
