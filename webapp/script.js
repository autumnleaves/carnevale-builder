// Global variables
let factionIndex = null;
let currentFactionData = null;
let selectedCrew = {
    leaders: [],
    heroes: [],
    henchmen: []
};
let ducatsLimit = 150;
let currentSavedCrewId = null; // Track the currently loaded/saved crew
let crewHasUnsavedChanges = false; // Track if crew has been modified

// Load the faction index when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadFactionIndex();
    setupEventListeners();
    initializeCollapseStates();
});

// Load faction index from JSON file
async function loadFactionIndex() {
    try {
        const response = await fetch('cards/index.json');
        factionIndex = await response.json();
        populateFactionDropdown();
    } catch (error) {
        console.error('Error loading faction index:', error);
        showError('Error loading card data. Make sure you are running this from a web server (not file://). Try running: python -m http.server 8000');
    }
}

// Populate the faction dropdown
function populateFactionDropdown() {
    const select = document.getElementById('factionSelect');
    
    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Sort factions by name for consistent display
    const sortedFactions = factionIndex.factions.sort((a, b) => 
        a.faction.localeCompare(b.faction)
    );
    
    sortedFactions.forEach(faction => {
        const option = document.createElement('option');
        option.value = faction.file;
        option.textContent = faction.faction;
        select.appendChild(option);
    });
}

// Load specific faction card data
async function loadFactionData(factionFile) {
    try {
        // Handle legacy guild_cards.json or cards in the cards directory
        const url = factionFile === 'guild_cards.json' ? factionFile : `cards/${factionFile}`;
        const response = await fetch(url);
        currentFactionData = await response.json();
        
        // Reset collapse states to expanded when loading a new faction
        ['leader', 'hero', 'henchman'].forEach(rankId => {
            localStorage.setItem(`rank-${rankId}-collapsed`, 'false');
        });
        
        // Reset crew when faction changes
        resetCrew();
        displayAvailableCards();
        updateCrewDisplay();
        
    } catch (error) {
        console.error('Error loading faction data:', error);
        showError('Error loading faction card data.');
    }
}

// Setup event listeners
function setupEventListeners() {
    const factionSelect = document.getElementById('factionSelect');
    const ducatsSelect = document.getElementById('ducatsLimit');
    const rankFilters = ['showLeaders', 'showHeroes', 'showHenchmen'];
    
    factionSelect.addEventListener('change', function() {
        if (this.value) {
            // Show main content
            document.getElementById('mainContent').style.display = 'grid';
            loadFactionData(this.value);
        } else {
            // Hide main content
            document.getElementById('mainContent').style.display = 'none';
            currentFactionData = null;
            resetCrew();
            document.getElementById('availableCardsList').innerHTML = '<p>Select a faction to see available cards.</p>';
        }
    });
    
    ducatsSelect.addEventListener('change', handleDucatsChange);
    ducatsSelect.addEventListener('input', handleDucatsChange);
    
    // Add event listener for crew name changes
    const crewNameHeader = document.getElementById('crewNameHeader');
    crewNameHeader.addEventListener('input', function() {
        markCrewAsChanged();
    });
    
    function handleDucatsChange() {
        let value = parseInt(this.value) || 0;
        // Ensure non-negative values
        if (value < 0) {
            value = 0;
            this.value = 0;
        }
        ducatsLimit = value;
        updateBudgetDisplay();
        validateCrew();
        markCrewAsChanged();
    }
    
    // Prevent negative input in real-time
    window.preventNegative = function(input) {
        if (input.value < 0) {
            input.value = 0;
        }
    };
    
    // Rank filter checkboxes
    rankFilters.forEach(filterId => {
        document.getElementById(filterId).addEventListener('change', displayAvailableCards);
    });
    
    // Modal close functionality
    setupModal();
    
    // Initialize UI state
    initializeUI();
}

// Initialize the UI state on page load
function initializeUI() {
    const factionSelect = document.getElementById('factionSelect');
    if (!factionSelect.value) {
        // Ensure main content is hidden when no faction selected
        document.getElementById('mainContent').style.display = 'none';
    } else {
        // If a faction is already selected (shouldn't happen on first load), show main content
        document.getElementById('mainContent').style.display = 'grid';
    }
}

// Setup modal functionality
function setupModal() {
    const modal = document.getElementById('cardModal');
    const closeBtn = modal.querySelector('.close');
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (event) => {
        const cardModal = document.getElementById('cardModal');
        const savedCrewsModal = document.getElementById('savedCrewsModal');
        
        if (event.target === cardModal) {
            cardModal.style.display = 'none';
        }
        
        if (event.target === savedCrewsModal) {
            savedCrewsModal.style.display = 'none';
        }
    });
}

// Display available cards based on current filters
function displayAvailableCards() {
    const container = document.getElementById('availableCardsList');
    
    if (!currentFactionData || !currentFactionData.cards) {
        container.innerHTML = '<p>Select a faction to see available cards.</p>';
        return;
    }
    
    // Get filter states
    const showLeaders = document.getElementById('showLeaders').checked;
    const showHeroes = document.getElementById('showHeroes').checked;
    const showHenchmen = document.getElementById('showHenchmen').checked;
    const searchTerm = document.getElementById('cardSearch')?.value.toLowerCase().trim() || '';
    
    // Filter cards by rank and search term
    let filteredCards = currentFactionData.cards.filter(card => {
        const rank = card.rank?.toLowerCase();
        if (rank === 'leader' && !showLeaders) return false;
        if (rank === 'hero' && !showHeroes) return false;
        if (rank === 'henchman' && !showHenchmen) return false;
        
        // Apply search filter
        if (searchTerm && !card.name.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        return true;
    });
    
    if (filteredCards.length === 0) {
        container.innerHTML = '<p>No cards match the current filters.</p>';
        return;
    }
    
    // Group by rank and display
    const cardsByRank = groupCardsByRank(filteredCards);
    let html = '';
    
    ['Leader', 'Hero', 'Henchman'].forEach(rank => {
        if (cardsByRank[rank] && cardsByRank[rank].length > 0) {
            const rankId = rank.toLowerCase();
            const isCollapsed = localStorage.getItem(`rank-${rankId}-collapsed`) === 'true';
            
            html += `<div class="rank-group">
                <h3 class="rank-header" onclick="toggleRankSection('${rankId}')">
                    <span class="collapse-icon ${isCollapsed ? 'collapsed' : ''}">${isCollapsed ? '▶' : '▼'}</span>
                    ${rank}s (${cardsByRank[rank].length})
                </h3>
                <div class="cards-grid rank-content" id="rank-${rankId}" ${isCollapsed ? 'style="display: none;"' : ''}>`;
                
            cardsByRank[rank].forEach(card => {
                const isInCrew = isCardInCrew(card);
                const canAdd = canAddCardToCrew(card);
                const isUnique = card.keywords && card.keywords.some(k => k.toLowerCase() === 'unique');
                const crewCount = getCardCountInCrew(card);
                
                let buttonText = 'Add';
                if (isUnique && isInCrew) {
                    buttonText = 'In Crew';
                } else if (!isUnique && crewCount > 0) {
                    buttonText = `Add (${crewCount} in crew)`;
                }
                
                html += `
                    <div class="available-card ${!canAdd ? 'disabled' : ''}" 
                         data-card-name="${card.name}">
                        <div class="card-header">
                            <span class="card-name">${card.name}</span>
                            <span class="card-cost">${card.ducats}</span>
                        </div>
                        <div class="card-actions">
                            <button onclick="showCardDetails('${card.name}')" class="btn-details">Details</button>
                            <button onclick="addCardToCrew('${card.name}')" 
                                    class="btn-add ${!canAdd ? 'disabled' : ''}"
                                    ${!canAdd ? 'disabled' : ''}>
                                ${buttonText}
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        }
    });
    
    container.innerHTML = html;
}

// Group cards by rank for better organization
function groupCardsByRank(cards) {
    const groups = {
        'Leader': [],
        'Hero': [],
        'Henchman': []
    };
    
    cards.forEach(card => {
        const rank = card.rank || 'No Rank';
        if (!groups[rank]) {
            groups[rank] = [];
        }
        groups[rank].push(card);
    });
    
    // Sort each group by name
    Object.keys(groups).forEach(rank => {
        groups[rank].sort((a, b) => a.name.localeCompare(b.name));
    });
    
    return groups;
}

// Group cards by rank for better organization
function groupCardsByRank(cards) {
    const groups = {
        'Leader': [],
        'Hero': [],
        'Henchman': []
    };
    
    cards.forEach(card => {
        const rank = card.rank || 'Henchman'; // Default to Henchman if no rank
        if (!groups[rank]) {
            groups[rank] = [];
        }
        groups[rank].push(card);
    });
    
    // Sort each group by name
    Object.keys(groups).forEach(rank => {
        groups[rank].sort((a, b) => a.name.localeCompare(b.name));
    });
    
    return groups;
}

// Check if a card is already in the crew
function isCardInCrew(card) {
    return selectedCrew.leaders.some(c => c.name === card.name) ||
           selectedCrew.heroes.some(c => c.name === card.name) ||
           selectedCrew.henchmen.some(c => c.name === card.name);
}

// Get the count of a specific card in the crew
function getCardCountInCrew(card) {
    const leaderCount = selectedCrew.leaders.filter(c => c.name === card.name).length;
    const heroCount = selectedCrew.heroes.filter(c => c.name === card.name).length;
    const henchmanCount = selectedCrew.henchmen.filter(c => c.name === card.name).length;
    return leaderCount + heroCount + henchmanCount;
}

// Check if a card can be added to the crew
function canAddCardToCrew(card) {
    const rank = card.rank?.toLowerCase();
    
    // Leaders: only one allowed
    if (rank === 'leader' && selectedCrew.leaders.length >= 1) return false;
    
    // Unique models: check for duplicates (only unique models can't be duplicated)
    if (card.keywords && card.keywords.some(k => k.toLowerCase() === 'unique')) {
        return !isCardInCrew(card);
    }
    
    // Non-unique models can always be added (multiple copies allowed)
    return true;
}

// Add a card to the crew
function addCardToCrew(cardName) {
    const card = currentFactionData.cards.find(c => c.name === cardName);
    if (!card || !canAddCardToCrew(card)) return;
    
    const rank = card.rank?.toLowerCase();
    
    switch (rank) {
        case 'leader':
            selectedCrew.leaders.push(card);
            // Auto-collapse leaders section after selecting one
            const leaderContent = document.getElementById('rank-leader');
            const leaderIcon = document.querySelector(`[onclick="toggleRankSection('leader')"] .collapse-icon`);
            if (leaderContent && leaderIcon && leaderContent.style.display !== 'none') {
                leaderContent.style.display = 'none';
                leaderIcon.textContent = '▶';
                leaderIcon.classList.add('collapsed');
                localStorage.setItem('rank-leader-collapsed', 'true');
            }
            break;
        case 'hero':
            selectedCrew.heroes.push(card);
            break;
        case 'henchman':
        default:
            selectedCrew.henchmen.push(card);
            break;
    }
    
    updateCrewDisplay();
    displayAvailableCards(); // Refresh to update button states
    validateCrew();
    markCrewAsChanged();
}

// Remove a card from the crew (only one instance)
function removeCardFromCrew(cardName) {
    // Remove only the first occurrence of the card
    let removed = false;
    let removedFromLeaders = false;
    
    if (!removed && selectedCrew.leaders.some(c => c.name === cardName)) {
        const index = selectedCrew.leaders.findIndex(c => c.name === cardName);
        selectedCrew.leaders.splice(index, 1);
        removed = true;
        removedFromLeaders = true;
    }
    
    if (!removed && selectedCrew.heroes.some(c => c.name === cardName)) {
        const index = selectedCrew.heroes.findIndex(c => c.name === cardName);
        selectedCrew.heroes.splice(index, 1);
        removed = true;
    }
    
    if (!removed && selectedCrew.henchmen.some(c => c.name === cardName)) {
        const index = selectedCrew.henchmen.findIndex(c => c.name === cardName);
        selectedCrew.henchmen.splice(index, 1);
        removed = true;
    }
    
    // Auto-expand leaders section if we removed a leader (so user can select a new one)
    if (removedFromLeaders && selectedCrew.leaders.length === 0) {
        const leaderContent = document.getElementById('rank-leader');
        const leaderIcon = document.querySelector(`[onclick="toggleRankSection('leader')"] .collapse-icon`);
        if (leaderContent && leaderIcon && leaderContent.style.display === 'none') {
            leaderContent.style.display = 'grid';
            leaderIcon.textContent = '▼';
            leaderIcon.classList.remove('collapsed');
            localStorage.setItem('rank-leader-collapsed', 'false');
        }
    }
    
    updateCrewDisplay();
    displayAvailableCards(); // Refresh to update button states
    validateCrew();
    markCrewAsChanged();
}

// Remove all instances of a card from the crew
function removeAllCardsFromCrew(cardName) {
    selectedCrew.leaders = selectedCrew.leaders.filter(c => c.name !== cardName);
    selectedCrew.heroes = selectedCrew.heroes.filter(c => c.name !== cardName);
    selectedCrew.henchmen = selectedCrew.henchmen.filter(c => c.name !== cardName);
    
    updateCrewDisplay();
    displayAvailableCards(); // Refresh to update button states
    validateCrew();
}

// Reset the crew
function resetCrew() {
    selectedCrew = {
        leaders: [],
        heroes: [],
        henchmen: []
    };
    // Reset crew name to default
    document.getElementById('crewNameHeader').value = 'Your Crew';
    
    // Clear tracking state
    currentSavedCrewId = null;
    crewHasUnsavedChanges = false;
    updateSaveButtonState();
    
    updateCrewDisplay();
    validateCrew();
}

// Update the crew display
function updateCrewDisplay() {
    updateCrewSection('crewLeaders', selectedCrew.leaders, 'No leader selected');
    updateCrewSection('crewHeroes', selectedCrew.heroes, 'No heroes selected');
    updateCrewSection('crewHenchmen', selectedCrew.henchmen, 'No henchmen selected');
    
    // Update counts
    document.getElementById('heroCount').textContent = `(${selectedCrew.heroes.length})`;
    document.getElementById('henchmanCount').textContent = `(${selectedCrew.henchmen.length})`;
    
    updateBudgetDisplay();
}

// Update a specific crew section
function updateCrewSection(containerId, cards, emptyMessage) {
    const container = document.getElementById(containerId);
    
    if (cards.length === 0) {
        container.innerHTML = `<p class="empty-slot">${emptyMessage}</p>`;
        return;
    }
    
    // Group cards by name to handle duplicates
    const cardGroups = cards.reduce((groups, card) => {
        if (!groups[card.name]) {
            groups[card.name] = {
                card: card,
                count: 0
            };
        }
        groups[card.name].count++;
        return groups;
    }, {});
    
    const html = Object.values(cardGroups).map(group => {
        const card = group.card;
        const count = group.count;
        const totalCost = card.ducats * count;
        
        return `
            <div class="crew-card">
                <div class="card-header">
                    <span class="card-name">
                        ${card.name}
                        ${count > 1 ? `<span class="card-count">x${count}</span>` : ''}
                    </span>
                    <span class="card-cost">
                        ${count > 1 ? `${totalCost} (${card.ducats} each)` : card.ducats}
                    </span>
                </div>
                <div class="card-actions">
                    <button onclick="showCardDetails('${card.name}')" class="btn-details">Details</button>
                    <button onclick="removeCardFromCrew('${card.name}')" class="btn-remove">Remove${count > 1 ? ' One' : ''}</button>
                    ${count > 1 ? `<button onclick="removeAllCardsFromCrew('${card.name}')" class="btn-remove-all">Remove All</button>` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// Update budget display
function updateBudgetDisplay() {
    const totalCost = calculateTotalCost();
    const remaining = ducatsLimit - totalCost;
    
    document.getElementById('totalCost').textContent = totalCost;
    document.getElementById('budgetDisplay').textContent = ducatsLimit;
    document.getElementById('remainingBudget').textContent = remaining;
    
    // Color code the remaining budget
    const remainingEl = document.getElementById('remainingBudget');
    remainingEl.className = 'cost-display';
    if (remaining < 0) {
        if (totalCost <= ducatsLimit + 5) {
            remainingEl.classList.add('over-budget-warning'); // Within 5 ducats over
        } else {
            remainingEl.classList.add('over-budget-error'); // More than 5 ducats over
        }
    } else if (remaining <= 10) {
        remainingEl.classList.add('low-budget');
    }
}

// Calculate total cost of crew
function calculateTotalCost() {
    const allCards = [...selectedCrew.leaders, ...selectedCrew.heroes, ...selectedCrew.henchmen];
    return allCards.reduce((total, card) => total + (card.ducats || 0), 0);
}

// Validate crew composition and show warnings
function validateCrew() {
    const warnings = [];
    const totalCost = calculateTotalCost();
    
    // Check for leader requirement
    if (selectedCrew.leaders.length === 0) {
        warnings.push('⚠️ You must select exactly one leader');
    } else if (selectedCrew.leaders.length > 1) {
        warnings.push('❌ You can only have one leader');
    }
    
    // Check hero/henchman ratio
    if (selectedCrew.heroes.length > selectedCrew.henchmen.length) {
        warnings.push('❌ You must have at least as many henchmen as heroes');
    }
    
    // Check budget
    if (totalCost > ducatsLimit) {
        const overage = totalCost - ducatsLimit;
        if (overage <= 5) {
            warnings.push(`⚠️ Over budget by ${overage} ducats (allowed up to 5)`);
        } else {
            warnings.push(`❌ Over budget by ${overage} ducats (maximum 5 allowed)`);
        }
    }
    
    // Display warnings
    const warningsContainer = document.getElementById('crewWarnings');
    if (warnings.length === 0) {
        warningsContainer.innerHTML = '<div class="crew-valid">✅ Crew is valid!</div>';
    } else {
        warningsContainer.innerHTML = warnings.map(warning => 
            `<div class="crew-warning">${warning}</div>`
        ).join('');
    }
}

// Show card details in modal
function showCardDetails(cardName) {
    const card = currentFactionData.cards.find(c => c.name === cardName);
    if (!card) return;
    
    const modal = document.getElementById('cardModal');
    const modalContent = document.getElementById('modalCardDetails');
    
    modalContent.innerHTML = generateCardHTML(card);
    modal.style.display = 'block';
}

// Generate HTML for a card (detailed view)
function generateCardHTML(card) {
    return `
        <div class="card-header">
            <div class="card-name">${card.name}</div>
            <div class="card-meta">
                <span>Page: ${card.page}</span>
                <span>Version: ${card.version}</span>
                <span>Rank: ${card.rank || 'N/A'}</span>
                <span>Cost: ${card.ducats} ducats</span>
            </div>
        </div>
        
        ${generateKeywords(card.keywords)}
        
        <div class="card-stats">
            ${generateBasicStats(card)}
            ${generateStatBlock(card.stat_block)}
        </div>
        
        ${generateWeapons(card.weapons)}
        ${generateAbilities(card.abilities)}
    `;
}

// Generate keywords display
function generateKeywords(keywords) {
    if (!keywords || keywords.length === 0) {
        return '';
    }
    
    const keywordTags = keywords.map(keyword => 
        `<span class="keyword ${keyword.toLowerCase() === 'unique' ? 'unique-keyword' : ''}">${keyword}</span>`
    ).join('');
    
    return `<div class="keywords">${keywordTags}</div>`;
}

// Generate basic stats section
function generateBasicStats(card) {
    const stats = [
        { label: 'Actions', value: card.actions },
        { label: 'Command', value: card.command },
        { label: 'Will', value: card.will },
        { label: 'Life', value: card.life },
        { label: 'Base Size', value: card.base_size ? `${card.base_size}mm` : 'N/A' }
    ];
    
    const statsHTML = stats.map(stat => 
        `<div class="stat-item">
            <span class="stat-label">${stat.label}:</span>
            <span>${stat.value || 'N/A'}</span>
        </div>`
    ).join('');
    
    return `
        <div class="stats-section">
            <h3>Basic Stats</h3>
            <div class="stat-grid">${statsHTML}</div>
        </div>
    `;
}

// Generate stat block section
function generateStatBlock(statBlock) {
    if (!statBlock) {
        return '<div class="stats-section"><h3>Combat Stats</h3><p>No combat stats available</p></div>';
    }
    
    const stats = [
        { label: 'Movement', value: statBlock.movement },
        { label: 'Dexterity', value: statBlock.dexterity },
        { label: 'Attack', value: statBlock.attack },
        { label: 'Protection', value: statBlock.protection },
        { label: 'Mind', value: statBlock.mind }
    ];
    
    const statsHTML = stats.map(stat => 
        `<div class="stat-item">
            <span class="stat-label">${stat.label}:</span>
            <span>${stat.value || 'N/A'}</span>
        </div>`
    ).join('');
    
    return `
        <div class="stats-section">
            <h3>Combat Stats</h3>
            <div class="stat-grid">${statsHTML}</div>
        </div>
    `;
}

// Generate weapons section
function generateWeapons(weapons) {
    if (!weapons || weapons.length === 0) {
        return '<div class="weapons-section"><h3>Weapons</h3><p>No weapons</p></div>';
    }
    
    const weaponsHTML = weapons.map(weapon => `
        <div class="weapon">
            <div class="weapon-name">${weapon.name}</div>
            <div class="weapon-stats">
                <div class="weapon-stat">
                    <span>Range:</span>
                    <span>${weapon.range || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Evasion:</span>
                    <span>${weapon.evasion || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Damage:</span>
                    <span>${weapon.damage || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Penetration:</span>
                    <span>${weapon.penetration || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Abilities:</span>
                    <span>${weapon.abilities || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    return `
        <div class="weapons-section">
            <h3>Weapons</h3>
            ${weaponsHTML}
        </div>
    `;
}

// Generate abilities section
function generateAbilities(abilities) {
    if (!abilities) {
        return '<div class="abilities-section"><h3>Abilities</h3><p>No abilities</p></div>';
    }
    
    let abilitiesHTML = '';
    
    // Common abilities
    if (abilities.common && abilities.common.length > 0) {
        const commonHTML = abilities.common.map(ability => {
            if (typeof ability === 'string') {
                return `<div class="ability"><div class="ability-name">${ability}</div></div>`;
            } else {
                return `
                    <div class="ability">
                        <div class="ability-name">${ability.name}</div>
                        <div class="ability-description">${ability.description}</div>
                    </div>
                `;
            }
        }).join('');
        
        abilitiesHTML += `
            <div class="abilities-group">
                <h4>Common Abilities</h4>
                ${commonHTML}
            </div>
        `;
    }
    
    // Unique abilities
    if (abilities.unique && abilities.unique.length > 0) {
        const uniqueHTML = abilities.unique.map(ability => `
            <div class="ability">
                <div class="ability-name">${ability.name}</div>
                <div class="ability-description">${ability.description}</div>
            </div>
        `).join('');
        
        abilitiesHTML += `
            <div class="abilities-group">
                <h4>Unique Abilities</h4>
                ${uniqueHTML}
            </div>
        `;
    }
    
    // Command abilities
    if (abilities.command && abilities.command.length > 0) {
        const commandHTML = abilities.command.map(ability => `
            <div class="ability">
                <div class="ability-name">${ability.name}</div>
                ${ability.type ? `<div class="ability-type">${ability.type}</div>` : ''}
                <div class="ability-description">${ability.description}</div>
            </div>
        `).join('');
        
        abilitiesHTML += `
            <div class="abilities-group">
                <h4>Command Abilities</h4>
                ${commandHTML}
            </div>
        `;
    }
    
    return `
        <div class="abilities-section">
            <h3>Abilities</h3>
            ${abilitiesHTML || '<p>No abilities</p>'}
        </div>
    `;
}

// Show error message
function showError(message) {
    document.getElementById('availableCardsList').innerHTML = 
        `<p style="color: red;">${message}</p>`;
}

// Toggle rank section visibility
function toggleRankSection(rankId) {
    const content = document.getElementById(`rank-${rankId}`);
    const icon = document.querySelector(`[onclick="toggleRankSection('${rankId}')"] .collapse-icon`);
    
    if (!content || !icon) return;
    
    const isCollapsed = content.style.display === 'none';
    
    if (isCollapsed) {
        content.style.display = 'grid';
        icon.textContent = '▼';
        icon.classList.remove('collapsed');
        localStorage.setItem(`rank-${rankId}-collapsed`, 'false');
    } else {
        content.style.display = 'none';
        icon.textContent = '▶';
        icon.classList.add('collapsed');
        localStorage.setItem(`rank-${rankId}-collapsed`, 'true');
    }
}

// Initialize collapse states from localStorage
function initializeCollapseStates() {
    // Initialize crew sections
    ['leaders', 'heroes', 'henchmen'].forEach(sectionId => {
        const isCollapsed = localStorage.getItem(`crew-${sectionId}-collapsed`) === 'true';
        if (isCollapsed) {
            const content = document.querySelector(`[data-section="${sectionId}"]`);
            const icon = document.querySelector(`[onclick="toggleCrewSection('${sectionId}')"] .collapse-icon`);
            if (content && icon) {
                content.style.display = 'none';
                icon.textContent = '▶';
                icon.classList.add('collapsed');
            }
        }
    });
}

// Toggle crew section visibility
function toggleCrewSection(sectionId) {
    const content = document.querySelector(`[data-section="${sectionId}"]`);
    const icon = document.querySelector(`[onclick="toggleCrewSection('${sectionId}')"] .collapse-icon`);
    
    if (!content || !icon) return;
    
    const isCollapsed = content.style.display === 'none';
    
    if (isCollapsed) {
        content.style.display = 'grid';
        icon.textContent = '▼';
        icon.classList.remove('collapsed');
        localStorage.setItem(`crew-${sectionId}-collapsed`, 'false');
    } else {
        content.style.display = 'none';
        icon.textContent = '▶';
        icon.classList.add('collapsed');
        localStorage.setItem(`crew-${sectionId}-collapsed`, 'true');
    }
}

// Expand all rank sections
function expandAllRanks() {
    ['leader', 'hero', 'henchman'].forEach(rankId => {
        const content = document.getElementById(`rank-${rankId}`);
        const icon = document.querySelector(`[onclick="toggleRankSection('${rankId}')"] .collapse-icon`);
        if (content && icon) {
            content.style.display = 'grid';
            icon.textContent = '▼';
            icon.classList.remove('collapsed');
            localStorage.setItem(`rank-${rankId}-collapsed`, 'false');
        }
    });
}

// Collapse all rank sections
function collapseAllRanks() {
    ['leader', 'hero', 'henchman'].forEach(rankId => {
        const content = document.getElementById(`rank-${rankId}`);
        const icon = document.querySelector(`[onclick="toggleRankSection('${rankId}')"] .collapse-icon`);
        if (content && icon) {
            content.style.display = 'none';
            icon.textContent = '▶';
            icon.classList.add('collapsed');
            localStorage.setItem(`rank-${rankId}-collapsed`, 'true');
        }
    });
}

// Filter cards by search term
function filterCardsBySearch() {
    const searchTerm = document.getElementById('cardSearch').value.toLowerCase().trim();
    displayAvailableCards(); // This will apply the search filter
}

// Clear search input and refresh display
function clearSearch() {
    document.getElementById('cardSearch').value = '';
    displayAvailableCards();
}

// Crew Save/Load Functionality
function saveCurrentCrew() {
    const crewName = document.getElementById('crewNameHeader').value.trim();
    if (!crewName) {
        showToast('Please enter a name for your crew', 'warning');
        document.getElementById('crewNameHeader').focus();
        return;
    }
    
    const factionSelect = document.getElementById('factionSelect');
    const ducatsSelect = document.getElementById('ducatsLimit');
    
    if (!currentFactionData || !factionSelect.value) {
        showToast('Please select a faction first', 'warning');
        return;
    }
    
    // Check if crew is invalid and warn user
    const warnings = validateCrewInternal();
    let saveConfirmed = true;
    
    // For now, just save without confirmation - could add a visual warning later
    if (warnings.length > 0) {
        saveConfirmed = true; // Auto-confirm for now
    }
    
    if (!saveConfirmed) return;
    
    // Generate GUID for unique identification (only for new crews)
    const guid = currentSavedCrewId || generateGUID();
    
    const crewData = {
        id: guid, // Unique identifier
        name: crewName,
        faction: factionSelect.value,
        factionName: factionSelect.options[factionSelect.selectedIndex].text,
        ducatsLimit: parseInt(ducatsSelect.value),
        crew: {
            leaders: [...selectedCrew.leaders],
            heroes: [...selectedCrew.heroes],
            henchmen: [...selectedCrew.henchmen]
        },
        totalCost: calculateTotalCost(),
        savedDate: new Date().toISOString(),
        isValid: warnings.length === 0
    };
    
    // Get existing saved crews
    const savedCrews = getSavedCrews();
    
    // Check if we're updating an existing crew or creating a new one
    let isUpdate = false;
    if (currentSavedCrewId) {
        // Update existing crew
        const existingIndex = savedCrews.findIndex(c => c.id === currentSavedCrewId);
        if (existingIndex !== -1) {
            savedCrews[existingIndex] = crewData;
            isUpdate = true;
        } else {
            // Fallback: if we can't find the existing crew by ID, add as new
            savedCrews.push(crewData);
        }
    } else {
        // Add as new crew
        savedCrews.push(crewData);
    }
    
    // Save to localStorage
    localStorage.setItem('carnevale-saved-crews', JSON.stringify(savedCrews));
    
    // Store the current crew's saved ID for tracking changes
    currentSavedCrewId = guid;
    crewHasUnsavedChanges = false;
    updateSaveButtonState();
    
    // Show success toast
    const action = isUpdate ? 'updated' : 'saved';
    showToast(`Crew "${crewName}" ${action} successfully!`, 'success');
    
    // Refresh saved crews display if modal is open
    const modal = document.getElementById('savedCrewsModal');
    if (modal.style.display === 'block') {
        displaySavedCrews();
    }
}

function saveAsNewCrew() {
    // Temporarily clear the current saved crew ID to force creation of a new crew
    const originalId = currentSavedCrewId;
    currentSavedCrewId = null;
    
    // Call the regular save function (which will now create a new crew)
    saveCurrentCrew();
    
    // Note: currentSavedCrewId will be set to the new GUID by saveCurrentCrew()
}

function getSavedCrews() {
    const saved = localStorage.getItem('carnevale-saved-crews');
    return saved ? JSON.parse(saved) : [];
}

// Generate a simple GUID
function generateGUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Update the save button state based on crew changes
function updateSaveButtonState() {
    const saveButton = document.querySelector('.btn-save-crew');
    const saveAsNewButton = document.querySelector('.btn-save-as-new');
    
    if (crewHasUnsavedChanges || currentSavedCrewId === null) {
        saveButton.textContent = 'Save Crew';
        saveButton.disabled = false;
        saveButton.classList.remove('btn-saved');
        
        // Hide "Save as New" button if we don't have a saved crew to base it on
        if (currentSavedCrewId === null) {
            saveAsNewButton.style.display = 'none';
        } else {
            saveAsNewButton.style.display = 'inline-block';
        }
    } else {
        saveButton.textContent = 'Saved ✓';
        saveButton.disabled = false; // Still allow saving (updates existing crew)
        saveButton.classList.add('btn-saved');
        
        // Show "Save as New" button when crew is saved
        saveAsNewButton.style.display = 'inline-block';
    }
}

// Mark crew as having unsaved changes
function markCrewAsChanged() {
    if (!crewHasUnsavedChanges) {
        crewHasUnsavedChanges = true;
        updateSaveButtonState();
    }
}

function toggleSavedCrews() {
    document.getElementById('savedCrewsModal').style.display = 'block';
    displaySavedCrews();
}

function closeSavedCrewsModal() {
    document.getElementById('savedCrewsModal').style.display = 'none';
}

function displaySavedCrews() {
    const savedCrews = getSavedCrews();
    const container = document.getElementById('savedCrewsList');
    
    if (savedCrews.length === 0) {
        container.innerHTML = '<div class="empty-crews-message">No saved crews found.<br>Build a crew and save it to get started!</div>';
        return;
    }
    
    container.innerHTML = savedCrews.map(crew => {
        const savedDate = new Date(crew.savedDate).toLocaleDateString();
        const validityIcon = crew.isValid ? '✅' : '⚠️';
        const totalCards = crew.crew.leaders.length + crew.crew.heroes.length + crew.crew.henchmen.length;
        
        return `
            <div class="saved-crew-item">
                <div class="saved-crew-info">
                    <h5>${validityIcon} ${crew.name}</h5>
                    <p class="saved-crew-details">
                        <strong>${crew.factionName}</strong> • ${crew.ducatsLimit} ducats • ${totalCards} cards • ${crew.totalCost} cost<br>
                        Saved: ${savedDate}
                    </p>
                </div>
                <div class="saved-crew-actions">
                    <button class="btn-load" onclick="loadSavedCrew('${crew.id}')">Load</button>
                    <button class="btn-delete-crew" onclick="deleteSavedCrew('${crew.id}')">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

function loadSavedCrew(crewId) {
    const savedCrews = getSavedCrews();
    const crew = savedCrews.find(c => c.id === crewId);
    
    if (!crew) {
        showToast('Crew not found', 'error');
        return;
    }
    
    // Set faction and ducats
    const factionSelect = document.getElementById('factionSelect');
    const ducatsSelect = document.getElementById('ducatsLimit');
    
    factionSelect.value = crew.faction;
    ducatsSelect.value = crew.ducatsLimit;
    
    // Load faction data and then set crew
    loadFactionData(crew.faction).then(() => {
        // Set the crew name in header
        document.getElementById('crewNameHeader').value = crew.name;
        
        // Set the crew
        selectedCrew = {
            leaders: [...crew.crew.leaders],
            heroes: [...crew.crew.heroes],
            henchmen: [...crew.crew.henchmen]
        };
        
        // Update displays
        updateCrewDisplay();
        displayAvailableCards();
        validateCrew();
        
        // Reset tracking variables for loaded crew
        currentSavedCrewId = crew.id;
        crewHasUnsavedChanges = false;
        updateSaveButtonState();
        
        showToast(`Crew "${crew.name}" loaded successfully!`, 'success');
        
        // Close the modal
        closeSavedCrewsModal();
    }).catch(error => {
        console.error('Error loading crew:', error);
        showToast('Error loading crew. The faction data might not be available.', 'error');
    });
}

function deleteSavedCrew(crewId) {
    const savedCrews = getSavedCrews();
    const crew = savedCrews.find(c => c.id === crewId);
    
    if (!crew) {
        showToast('Crew not found', 'error');
        return;
    }
    
    // Delete directly without confirmation
    const filteredCrews = savedCrews.filter(c => c.id !== crewId);
    
    localStorage.setItem('carnevale-saved-crews', JSON.stringify(filteredCrews));
    displaySavedCrews();
    
    showToast(`Crew "${crew.name}" deleted`, 'success');
}

// Helper function to get validation warnings without displaying them
function validateCrewInternal() {
    const warnings = [];
    const totalCost = calculateTotalCost();
    const currentBudget = parseInt(document.getElementById('ducatsLimit').value) || 150;
    
    // Check budget
    if (totalCost > currentBudget) {
        warnings.push(`Over budget by ${totalCost - currentBudget} ducats`);
    }
    
    // Check leader requirement
    if (selectedCrew.leaders.length === 0) {
        warnings.push('No leader selected');
    } else if (selectedCrew.leaders.length > 1) {
        warnings.push('Too many leaders selected');
    }
    
    // Check for duplicates of unique cards
    const allCards = [...selectedCrew.leaders, ...selectedCrew.heroes, ...selectedCrew.henchmen];
    const uniqueCards = allCards.filter(card => card.unique);
    const uniqueNames = uniqueCards.map(card => card.name);
    const duplicateUnique = uniqueNames.filter((name, index) => uniqueNames.indexOf(name) !== index);
    
    if (duplicateUnique.length > 0) {
        warnings.push(`Duplicate unique cards: ${[...new Set(duplicateUnique)].join(', ')}`);
    }
    
    return warnings;
}

// Toast notification system
function showToast(message, type = 'success', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Remove toast after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (container.contains(toast)) {
                container.removeChild(toast);
            }
        }, 300);
    }, duration);
}
