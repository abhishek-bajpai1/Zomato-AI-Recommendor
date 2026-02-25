/**
 * Zomato Recommender - Main Application Logic
 */

const API_BASE = ""; // Backend and frontend are on same origin

const state = {
    token: sessionStorage.getItem('zomato_token'),
    locations: [],
    cuisines: [],
    selectedCuisines: [],
    rating: 0,
    budget: null
};

// ── DOM Elements ─────────────────────────────────────────────────────────────

const screens = {
    loader: document.getElementById('loader'),
    login: document.getElementById('login-screen'),
    reco: document.getElementById('reco-screen')
};

const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const getRecosBtn = document.getElementById('get-recos-btn');

const filterLoc = document.getElementById('filter-location');
const filterCuisine = document.getElementById('filter-cuisine');
const selectedCuisinesContainer = document.getElementById('selected-cuisines');
const filterRating = document.getElementById('filter-rating');
const ratingVal = document.getElementById('rating-val');
const filterBudget = document.getElementById('filter-budget');

const resultsGrid = document.getElementById('results-grid');
const resultsBanners = document.getElementById('results-imagery');
const resultsPlaceholder = document.getElementById('results-placeholder');
const resultsLoading = document.getElementById('results-loading');
const resultsCount = document.getElementById('results-count');
const toastContainer = document.getElementById('toast-container');

// ── Navigation & Initialization ──────────────────────────────────────────────

function showScreen(screenId) {
    Object.keys(screens).forEach(key => {
        screens[key].classList.add('hidden');
    });
    screens[screenId].classList.remove('hidden');
}

async function init() {
    if (state.token) {
        try {
            await verifyAuth();
            showScreen('reco');
            await loadCatalogData();
            renderBanners();
        } catch (err) {
            logout();
        }
    } else {
        showScreen('login');
    }
}

async function verifyAuth() {
    const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) throw new Error('Unauthorized');
}

// ── Auth Handlers ────────────────────────────────────────────────────────────

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.textContent = "";

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (res.ok) {
            state.token = data.access_token;
            sessionStorage.setItem('zomato_token', state.token);
            init();
        } else {
            loginError.textContent = data.detail || "Login failed";
        }
    } catch (err) {
        loginError.textContent = "Network error connection failed";
    }
});

function logout() {
    state.token = null;
    sessionStorage.removeItem('zomato_token');
    showScreen('login');
}

logoutBtn.addEventListener('click', logout);

// ── Filter Handlers ──────────────────────────────────────────────────────────

async function loadCatalogData() {
    try {
        const [locsRes, cuisinesRes] = await Promise.all([
            fetch(`${API_BASE}/restaurants/locations`, { headers: { 'Authorization': `Bearer ${state.token}` } }),
            fetch(`${API_BASE}/restaurants/cuisines`, { headers: { 'Authorization': `Bearer ${state.token}` } })
        ]);

        state.locations = await locsRes.json();
        state.cuisines = await cuisinesRes.json();

        populateDropdown(filterLoc, state.locations, "Any Location");
        populateDropdown(filterCuisine, state.cuisines, "Any Cuisine");
    } catch (err) {
        console.error("Failed to load catalog filters", err);
    }
}

function populateDropdown(select, items, defaultText) {
    select.innerHTML = `<option value="">${defaultText}</option>`;
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item.charAt(0).toUpperCase() + item.slice(1);
        select.appendChild(opt);
    });
}

filterRating.addEventListener('input', (e) => {
    state.rating = parseFloat(e.target.value);
    ratingVal.textContent = state.rating.toFixed(1);
});

filterBudget.addEventListener('input', (e) => {
    state.budget = e.target.value ? parseInt(e.target.value) : null;
});

filterCuisine.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val && !state.selectedCuisines.includes(val)) {
        if (state.selectedCuisines.length >= 4) {
            showToast("Maximum 4 cuisines allowed");
            e.target.value = "";
            return;
        }
        state.selectedCuisines.push(val);
        renderCuisineTags();
        e.target.value = "";
    }
});

function renderCuisineTags() {
    selectedCuisinesContainer.innerHTML = state.selectedCuisines.map(c => `
        <div class="cuisine-tag">
            <span>${c.charAt(0).toUpperCase() + c.slice(1)}</span>
            <button class="deselect-cuisine" onclick="removeCuisineTag('${c}')" aria-label="Remove ${c}">
                <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" class="deselect-svg">
                    <path d="M30 30 L70 70 M70 30 L30 70" stroke="currentColor" stroke-width="15" stroke-linecap="round" />
                </svg>
            </button>
        </div>
    `).join('');
}

window.removeCuisineTag = (cuisine) => {
    state.selectedCuisines = state.selectedCuisines.filter(c => c !== cuisine);
    renderCuisineTags();
};

function showToast(message) {
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;

    toastContainer.appendChild(toast);

    // Fade out after 3.6s, remove after 4s
    setTimeout(() => {
        toast.classList.add('fade-out');
    }, 3600);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ── Voice Transcription ──────────────────────────────────────────────────────

const voiceTrigger = document.getElementById('feature-voice-trigger');
const inlineVoiceContainer = document.getElementById('inline-voice-search');
const voiceTranscriptDisplay = document.getElementById('voice-transcript-display');
const clearVoiceCmdBtn = document.getElementById('clear-voice-cmd-btn');
const voiceHeroText = document.getElementById('voice-hero-text');

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;

    voiceTrigger.addEventListener('click', () => {
        if (inlineVoiceContainer.classList.contains('hidden')) {
            inlineVoiceContainer.classList.remove('hidden');
            voiceHeroText.classList.add('hidden');
            voiceTranscriptDisplay.textContent = "Listening...";
            clearVoiceCmdBtn.classList.add('hidden');
            recognition.start();
            voiceTrigger.classList.add('listening');
        } else {
            recognition.stop();
        }
    });

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');
        voiceTranscriptDisplay.textContent = transcript;

        if (transcript.length > 0) {
            clearVoiceCmdBtn.classList.remove('hidden');
        }
    };

    recognition.onend = () => {
        voiceTrigger.classList.remove('listening');
        const transcript = voiceTranscriptDisplay.textContent;

        if (!transcript || transcript === "Listening...") {
            inlineVoiceContainer.classList.add('hidden');
            voiceHeroText.classList.remove('hidden');
        } else {
            // Automatically process after a short delay for UX
            setTimeout(() => {
                // Double check it hasn't been cleared/canceled
                if (!inlineVoiceContainer.classList.contains('hidden') && voiceTranscriptDisplay.textContent !== "Listening...") {
                    inlineVoiceContainer.classList.add('hidden');
                    voiceHeroText.classList.remove('hidden');
                    processVoiceCommand(transcript);
                }
            }, 1000);
        }
    };

    clearVoiceCmdBtn.addEventListener('click', () => {
        voiceTranscriptDisplay.textContent = "Listening...";
        clearVoiceCmdBtn.classList.add('hidden');
    });

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        voiceTranscriptDisplay.textContent = "Error: " + event.error;
        setTimeout(() => {
            inlineVoiceContainer.classList.add('hidden');
            voiceHeroText.classList.remove('hidden');
        }, 2000);
    };
}

function processVoiceCommand(cmd) {
    if (!cmd || cmd.toLowerCase() === "listening..." || cmd.length < 3) return;

    // Simple heuristic-based command parsing
    const lowerCmd = cmd.toLowerCase();

    // Check for locations
    state.locations.forEach(loc => {
        if (lowerCmd.includes(loc.toLowerCase())) {
            filterLoc.value = loc;
        }
    });

    // Check for cuisines (limit to first matching one if found)
    state.cuisines.forEach(c => {
        if (lowerCmd.includes(c.toLowerCase()) && !state.selectedCuisines.includes(c)) {
            if (state.selectedCuisines.length < 4) {
                state.selectedCuisines.push(c);
            }
        }
    });

    renderCuisineTags();
    getRecommendations();
}

// ── Recommendation Logic ─────────────────────────────────────────────────────

async function getRecommendations() {
    resultsPlaceholder.classList.add('hidden');
    resultsLoading.classList.remove('hidden');
    resultsGrid.innerHTML = "";
    resultsCount.textContent = "";

    const payload = {
        location: filterLoc.value,
        cuisines: state.selectedCuisines,
        min_rating: state.rating,
        max_price: state.budget
    };

    try {
        const res = await fetch(`${API_BASE}/recommendations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        resultsLoading.classList.add('hidden');

        if (data.length === 0) {
            resultsPlaceholder.classList.remove('hidden');
            resultsPlaceholder.innerHTML = `<div class="placeholder-icon">🔍</div><p>No restaurants found matching your criteria</p>`;
        } else {
            renderResults(data);
            resultsCount.textContent = `Showing top ${data.length} recommendations`;
        }
    } catch (err) {
        resultsLoading.classList.add('hidden');
        resultsPlaceholder.classList.remove('hidden');
        resultsPlaceholder.textContent = "Error loading recommendations. Please try again.";
    }
}

getRecosBtn.addEventListener('click', getRecommendations);

function renderResults(restaurants) {
    resultsGrid.innerHTML = restaurants.map(r => {
        const fullStars = Math.floor(r.rating);
        const hasHalf = r.rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

        let starsHtml = '<span class="star-filled">' + '★'.repeat(fullStars) + '</span>';
        if (hasHalf) starsHtml += '<span class="star-filled">★</span>'; // Simplified for now
        starsHtml += '<span class="star-empty">' + '★'.repeat(emptyStars) + '</span>';

        return `
            <div class="restaurant-card">
                <h3 class="resto-name">${r.name}</h3>
                <p class="resto-meta">${r.location.charAt(0).toUpperCase() + r.location.slice(1)}</p>
                <div class="resto-tags">
                    <span class="resto-cuisine">${r.cuisine.charAt(0).toUpperCase() + r.cuisine.slice(1)}</span>
                    <div class="resto-rating">
                        <div class="stars">${starsHtml}</div>
                        <span>${r.rating.toFixed(1)}</span>
                    </div>
                </div>
                ${r.review_summary ? `
                <div class="ai-summary">
                    <span class="ai-badge">AI Summary</span>
                    <p>${r.review_summary}</p>
                </div>` : ''}
                <div style="margin-top: 12px; font-size: 0.875rem; color: #FFFFFF; opacity: 0.9; font-weight: 600;">
                    Min. Price for Two: ₹${r.min_price_for_two || r.cost_for_two}
                </div>
            </div>
        `;
    }).join('');
}

function renderBanners() {
    const banners = [
        { name: "Traditional", img: "/assets/indian.png" },
        { name: "Fast Food", img: "/assets/burger.png" },
        { name: "Nightlife", img: "/assets/cocktails.png" }
    ];

    resultsBanners.innerHTML = banners.map(b => `
        <div class="banner" style="background-image: url('${b.img}')" onclick="quickFilterCuisine('${b.name}')">
            <span>${b.name}</span>
        </div>
    `).join('');
}

window.quickFilterCuisine = (name) => {
    filterCuisine.value = name.toLowerCase();
    getRecommendations();
};

init();
