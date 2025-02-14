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
            
            // Create letter tiles
            word.split('').forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordContainer.appendChild(tile);
            });
            
            puzzleDisplay.appendChild(wordContainer);
            
            // Add word spacing
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
        const list = document.getElementById('solution-list');
        
        // Clear existing items
        list.innerHTML = '';
        
        // Create grid items
        pastSolutions.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `
                <strong>${item.date}:</strong>
                <span>${item.solution}</span>
            `;
            list.appendChild(li);
        });

    } catch (error) {
        console.error('Error loading history:', error);
        const list = document.getElementById('solution-list');
        list.innerHTML = '<li>Error loading past solutions</li>';
    }
}

function toggleHistory() {
    const content = document.getElementById('history-content');
    const header = document.querySelector('.history-header');
    const list = document.getElementById('solution-list');
    
    // Toggle visibility
    header.classList.toggle('active');
    content.classList.toggle('hidden');
    
    // Animate dropdown arrow
    const arrow = document.querySelector('.dropdown-arrow');
    arrow.style.transform = content.classList.contains('hidden') 
        ? 'rotate(45deg)'
        : 'rotate(225deg)';
    
    // Load history only once
    if (!content.classList.contains('hidden') && list.children.length === 0) {
        loadHistory();
    }
}

// Initial page load
document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    
    // Preload history if user opens immediately
    const observer = new MutationObserver(mutations => {
        if (!document.getElementById('history-content').classList.contains('hidden')) {
            loadHistory();
        }
    });
    observer.observe(document.getElementById('history-content'), {
        attributes: true,
        attributeFilter: ['class']
    });
});
