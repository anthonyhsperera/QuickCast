// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost'
    ? `http://localhost:${window.location.port}/api`
    : '/api';

// State
let audioElement = null;
let shareId = null;

// DOM Elements
const loadingSection = document.getElementById('loadingSection');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const podcastInfo = document.getElementById('podcastInfo');
const podcastTitle = document.getElementById('podcastTitle');
const podcastSource = document.getElementById('podcastSource');
const podcastDuration = document.getElementById('podcastDuration');
const playerSection = document.getElementById('playerSection');
const ctaSection = document.getElementById('ctaSection');
const playBtn = document.getElementById('playBtn');
const playIcon = document.getElementById('playIcon');
const pauseIcon = document.getElementById('pauseIcon');
const timelineSlider = document.getElementById('timelineSlider');
const timelineProgress = document.getElementById('timelineProgress');
const currentTime = document.getElementById('currentTime');
const totalTime = document.getElementById('totalTime');
const volumeSlider = document.getElementById('volumeSlider');
const volumeBtn = document.getElementById('volumeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const shareBtn = document.getElementById('shareBtn');
const shareModal = document.getElementById('shareModal');
const shareModalClose = document.getElementById('shareModalClose');
const shareModalOverlay = document.getElementById('shareModalOverlay');
const shareLinkInput = document.getElementById('shareLinkInput');
const copyLinkBtn = document.getElementById('copyLinkBtn');
const copyBtnText = document.getElementById('copyBtnText');
const copyIcon = document.getElementById('copyIcon');
const checkIcon = document.getElementById('checkIcon');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    audioElement = document.getElementById('audioElement');
    extractShareId();
    loadSharedPodcast();
    setupEventListeners();
});

// Extract share ID from URL
function extractShareId() {
    const path = window.location.pathname;
    const match = path.match(/\/s\/([a-zA-Z0-9]+)/);
    if (match) {
        shareId = match[1];
    }
}

// Clean source URL to display-friendly format
function cleanSourceUrl(url) {
    if (!url) return '';

    try {
        const urlObj = new URL(url);
        let domain = urlObj.hostname;

        // Remove www. prefix
        domain = domain.replace(/^www\./, '');

        // Extract pathname for context (e.g., /bbcnews)
        const path = urlObj.pathname.split('/').filter(p => p);

        // Common domain to name mappings
        const domainNames = {
            'facebook.com': 'Facebook',
            'twitter.com': 'Twitter',
            'x.com': 'X',
            'linkedin.com': 'LinkedIn',
            'medium.com': 'Medium',
            'substack.com': 'Substack',
            'nytimes.com': 'The New York Times',
            'wsj.com': 'The Wall Street Journal',
            'theguardian.com': 'The Guardian',
            'bbc.com': 'BBC',
            'bbc.co.uk': 'BBC',
            'cnn.com': 'CNN',
            'reuters.com': 'Reuters',
            'bloomberg.com': 'Bloomberg',
            'techcrunch.com': 'TechCrunch',
            'theverge.com': 'The Verge',
            'wired.com': 'Wired'
        };

        // Check if we have a known domain
        if (domainNames[domain]) {
            // For Facebook pages, add the page name if available
            if (domain === 'facebook.com' && path.length > 0) {
                return `${domainNames[domain]} - ${path[0]}`;
            }
            return domainNames[domain];
        }

        // For unknown domains, capitalize first letter and remove TLD
        const baseDomain = domain.split('.')[0];
        return baseDomain.charAt(0).toUpperCase() + baseDomain.slice(1);

    } catch (e) {
        // If URL parsing fails, return the original
        return url;
    }
}

// Load shared podcast
async function loadSharedPodcast() {
    if (!shareId) {
        showError('Invalid share link');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/share/${shareId}`);

        if (!response.ok) {
            if (response.status === 404) {
                showError('This podcast is not available or has expired');
            } else {
                showError('Failed to load shared podcast');
            }
            return;
        }

        const data = await response.json();

        if (!data.exists) {
            showError('This podcast is not available or has expired');
            return;
        }

        // Display podcast info
        podcastTitle.textContent = data.title || 'QuickCast Podcast';

        // Display cleaned source URL
        if (data.source_url) {
            const cleanedSource = cleanSourceUrl(data.source_url);
            podcastSource.textContent = cleanedSource;
            podcastSource.classList.remove('hidden');
        } else if (data.author) {
            podcastSource.textContent = data.author;
            podcastSource.classList.remove('hidden');
        } else {
            podcastSource.classList.add('hidden');
        }

        if (data.duration) {
            podcastDuration.textContent = formatDuration(data.duration);
        }

        // Load audio
        audioElement.src = data.audio_url;
        audioElement.load();

        // Show content
        hideLoading();
        podcastInfo.classList.remove('hidden');
        playerSection.classList.remove('hidden');
        ctaSection.classList.remove('hidden');

        // Set up download
        downloadBtn.addEventListener('click', () => {
            window.open(data.audio_url, '_blank');
        });

    } catch (error) {
        console.error('Error loading shared podcast:', error);
        showError('Failed to load shared podcast');
    }
}

// Event Listeners
function setupEventListeners() {
    // Audio player controls
    playBtn.addEventListener('click', togglePlayPause);
    timelineSlider.addEventListener('input', handleSeek);
    volumeSlider.addEventListener('input', handleVolumeChange);
    volumeBtn.addEventListener('click', toggleMute);

    // Audio element events
    audioElement.addEventListener('loadedmetadata', handleAudioLoaded);
    audioElement.addEventListener('timeupdate', handleTimeUpdate);
    audioElement.addEventListener('ended', handleAudioEnded);

    // Share modal events
    if (shareBtn) {
        shareBtn.addEventListener('click', openShareModal);
    }
    if (shareModalClose) {
        shareModalClose.addEventListener('click', closeShareModal);
    }
    if (shareModalOverlay) {
        shareModalOverlay.addEventListener('click', closeShareModal);
    }
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', copyShareLink);
    }
}

// Audio Controls
function togglePlayPause() {
    if (audioElement.paused) {
        audioElement.play();
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
    } else {
        audioElement.pause();
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    }
}

function handleAudioLoaded() {
    totalTime.textContent = formatTime(audioElement.duration);
    timelineSlider.max = audioElement.duration;
}

function handleTimeUpdate() {
    const current = audioElement.currentTime;
    const duration = audioElement.duration;

    if (duration) {
        const percentage = (current / duration) * 100;
        timelineProgress.style.width = percentage + '%';
        timelineSlider.value = current;
        currentTime.textContent = formatTime(current);
    }
}

function handleSeek(e) {
    const time = parseFloat(e.target.value);
    audioElement.currentTime = time;
}

function handleVolumeChange(e) {
    const volume = parseFloat(e.target.value) / 100;
    audioElement.volume = volume;
}

function toggleMute() {
    audioElement.muted = !audioElement.muted;

    if (audioElement.muted) {
        volumeSlider.value = 0;
    } else {
        volumeSlider.value = audioElement.volume * 100;
    }
}

function handleAudioEnded() {
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
}

// UI Helper Functions
function hideLoading() {
    loadingSection.classList.add('hidden');
}

function showError(message) {
    loadingSection.classList.add('hidden');
    podcastInfo.classList.add('hidden');
    playerSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    errorMessage.textContent = message;
}

// Share Functions
function openShareModal() {
    // Use current page URL for sharing
    const shareUrl = window.location.href;
    shareLinkInput.value = shareUrl;
    shareModal.classList.remove('hidden');
    shareLinkInput.select();
}

function closeShareModal() {
    shareModal.classList.add('hidden');
    resetCopyButton();
}

async function copyShareLink() {
    try {
        await navigator.clipboard.writeText(shareLinkInput.value);

        // Update button to show success
        copyBtnText.textContent = 'Copied!';
        copyIcon.classList.add('hidden');
        checkIcon.classList.remove('hidden');
        copyLinkBtn.classList.add('copied');

        // Reset after 2 seconds
        setTimeout(resetCopyButton, 2000);
    } catch (error) {
        // Fallback for browsers that don't support clipboard API
        shareLinkInput.select();
        document.execCommand('copy');

        copyBtnText.textContent = 'Copied!';
        copyIcon.classList.add('hidden');
        checkIcon.classList.remove('hidden');
        copyLinkBtn.classList.add('copied');

        setTimeout(resetCopyButton, 2000);
    }
}

function resetCopyButton() {
    copyBtnText.textContent = 'Copy';
    copyIcon.classList.remove('hidden');
    checkIcon.classList.add('hidden');
    copyLinkBtn.classList.remove('copied');
}

// Utility Functions
function formatTime(seconds) {
    if (isNaN(seconds) || seconds === Infinity) {
        return '0:00';
    }

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);

    if (mins === 0) {
        return `${secs}s`;
    }

    return `${mins}m ${secs}s`;
}
