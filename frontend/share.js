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
const podcastAuthor = document.getElementById('podcastAuthor');
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

        if (data.author) {
            podcastAuthor.textContent = data.author;
            podcastAuthor.classList.remove('hidden');
        } else {
            podcastAuthor.classList.add('hidden');
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
