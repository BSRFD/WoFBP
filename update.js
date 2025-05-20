let historyLoaded = false;
let lastUpdateCheck = Date.now();

// Fisher-Yates shuffle algorithm
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

// --- FUNCTION to display any puzzle on the board ---
function displayPuzzleOnBoard(dateStr, solutionStr, addedUtcStr) {
    const dateElement = document.getElementById('date');
    const solutionElementOriginal = document.getElementById('solution'); // Get the original element
    
    if (dateElement) dateElement.textContent = dateStr;
    
    // Recreate or update solutionElement to handle event listeners correctly
    if (solutionElementOriginal) {
        const newSolutionElement = solutionElementOriginal.cloneNode(false); // Clone structure, not deep children
        newSolutionElement.textContent = solutionStr; // Set the text content
        newSolutionElement.id = 'solution'; // Ensure ID is maintained
        newSolutionElement.className = 'info-value'; // Ensure class is maintained
        newSolutionElement.style.cursor = 'pointer';
        newSolutionElement.setAttribute('title', 'Click to copy');
        
        solutionElementOriginal.parentNode.replaceChild(newSolutionElement, solutionElementOriginal); // Replace old with new
    
        newSolutionElement.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(solutionStr);
                showCopyFeedback('Copied to clipboard!');
            } catch (err) {
                console.error('Failed to copy:', err);
                showCopyFeedback('Failed to copy!');
            }
        });
    }


    const puzzleDisplay = document.getElementById('puzzle-display');
    if (!puzzleDisplay) return; 

    puzzleDisplay.innerHTML = ''; 
    
    const addedDate = addedUtcStr && addedUtcStr !== 'null' && addedUtcStr !== 'undefined' ? new Date(addedUtcStr) : null;
    let timeContainer = null;
    if (addedDate && !isNaN(addedDate)) { // Check if date is valid
        timeContainer = document.createElement('div');
        timeContainer.className = 'puzzle-timestamp';
        timeContainer.textContent = `Added: ${addedDate.toLocaleTimeString([], { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        })}`;
    }

    const wordContainer = document.createElement('div');
    wordContainer.className = 'word-container';
    puzzleDisplay.appendChild(wordContainer);

    const allTiles = [];
    const words = solutionStr.split(/\s+/);
    
    const MAX_CHARS_PER_LINE = 14; 
    let currentLineElement = null;
    let currentLineCharCount = 0;

    words.forEach((word) => {
        const wordLength = word.length;
        const spaceNeededForThisWord = currentLineCharCount > 0 ? 1 + wordLength : wordLength;

        if (currentLineElement === null || (currentLineCharCount + spaceNeededForThisWord > MAX_CHARS_PER_LINE && currentLineCharCount > 0)) {
            currentLineElement = document.createElement('div');
            currentLineElement.className = 'word-row';
            wordContainer.appendChild(currentLineElement);
            currentLineCharCount = 0;
        }

        if (currentLineCharCount > 0) {
            const spaceTile = document.createElement('div');
            spaceTile.className = 'letter-tile space-tile';
            spaceTile.innerHTML = ' ';
            currentLineElement.appendChild(spaceTile);
            currentLineCharCount += 1;
        }

        [...word.toUpperCase()].forEach(letter => {
            const tile = document.createElement('div');
            tile.className = 'letter-tile';
            tile.textContent = letter;
            currentLineElement.appendChild(tile);
            allTiles.push(tile);
        });
        currentLineCharCount += wordLength;
    });

    if (timeContainer) { 
         puzzleDisplay.appendChild(timeContainer);
    }

    shuffleArray(allTiles); 
    allTiles.forEach((tile, index) => {
        setTimeout(() => {
            tile.classList.add('revealed');
        }, index * 50); 
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
}
// --- END NEW FUNCTION ---


async function fetchData() {
    try {
        const response = await fetch(`data.json?rand=${Date.now()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        displayPuzzleOnBoard(data.date, data.solution, data.added_utc);

        if (Date.now() - lastUpdateCheck > 300000) { 
            const freshCheck = await fetch(`data.json?rand=${Date.now()}`);
            if (!freshCheck.ok) { 
                console.warn(`Auto-refresh check failed: ${freshCheck.status}`);
                lastUpdateCheck = Date.now(); 
                return;
            }
            const freshData = await freshCheck.json();
            if (freshData.date !== data.date || freshData.solution !== data.solution) { 
                window.location.reload(true);
            }
            lastUpdateCheck = Date.now();
        }

    } catch (error) {
        console.error('Error fetching or displaying current data:', error);
        const puzzleDisplay = document.getElementById('puzzle-display');
        if(puzzleDisplay) puzzleDisplay.innerHTML = "<p style='text-align:center; color: var(--gold); padding-top: 20px;'>Could not load current puzzle. Please try again later.</p>";
        const dateElement = document.getElementById('date');
        const solutionElement = document.getElementById('solution');
        if(dateElement) dateElement.textContent = "Error";
        if(solutionElement) solutionElement.textContent = "Error loading";
    }
}

function showCopyFeedback(message) {
    const feedback = document.createElement('div');
    feedback.className = 'copy-feedback';
    feedback.setAttribute('role', 'alert');
    feedback.setAttribute('aria-live', 'polite');
    feedback.textContent = message;
    
    const existing = document.querySelector('.copy-feedback');
    if (existing) existing.remove();
    
    document.body.appendChild(feedback);
    void feedback.offsetWidth; 
    feedback.style.opacity = '1';
    
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => feedback.remove(), 500);
    }, 1500);
}

async function loadHistory() {
    try {
        const response = await fetch(`past-solutions.json?rand=${Date.now()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const pastSolutions = await response.json();
        const list = document.getElementById('solution-list');
        if (!list) return;
        
        const escapeForAttribute = (str) => {
            if (typeof str !== 'string') return ''; // Ensure it's a string
            return str.replace(/'/g, "\\'")    // Escape single quotes for JS string literal in attribute
                      .replace(/"/g, """)  // Escape double quotes for HTML attribute value
                      .replace(/\n/g, "\\n")   // Escape newlines for JS string literal
                      .replace(/\r/g, "\\r");   // Escape carriage returns for JS string literal
        };

        list.innerHTML = pastSolutions
            .map(item => {
                const addedDate = item.added_utc && item.added_utc !== 'null' && item.added_utc !== 'undefined' ? new Date(item.added_utc) : null;
                let timeString = '';
                if (addedDate && !isNaN(addedDate)) { // Check if date is valid
                     timeString = addedDate.toLocaleTimeString([], { 
                        hour: 'numeric', 
                        minute: '2-digit',
                        hour12: true 
                    });
                }
                
                const safeDate = escapeForAttribute(item.date);
                const safeSolution = escapeForAttribute(item.solution);
                const safeAddedUtc = escapeForAttribute(item.added_utc || '');


                return `
                    <div class="history-solution-item" 
                         onclick="displayPuzzleOnBoard('${safeDate}', '${safeSolution}', '${safeAddedUtc}')"
                         title="Click to view this puzzle on the board"
                         role="button" 
                         tabindex="0" 
                         onkeypress="if(event.key==='Enter' || event.key===' ') { displayPuzzleOnBoard('${safeDate}', '${safeSolution}', '${safeAddedUtc}'); event.preventDefault(); }">
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
        const list = document.getElementById('solution-list');
        if(list) list.innerHTML = "<p style='text-align:center; color: var(--gold);'>Could not load history.</p>";
    }
}

function toggleHistory() {
    const content = document.getElementById('history-content');
    const arrow = document.querySelector('.dropdown-arrow');
    if (!content || !arrow) return;
    
    content.classList.toggle('visible');
    arrow.style.transform = content.classList.contains('visible') 
        ? 'rotate(225deg)' 
        : 'rotate(45deg)';
    
    if (!historyLoaded && content.classList.contains('visible')) {
        loadHistory();
    }
}

document.addEventListener('DOMContentLoaded', fetchData);
