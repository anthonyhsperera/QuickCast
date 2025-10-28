// API Configuration
// Use same port as frontend in development, relative URL in production
const API_BASE_URL = window.location.hostname === 'localhost'
    ? `http://localhost:${window.location.port}/api`
    : '/api';

// State
let currentJobId = null;
let pollInterval = null;
let audioElement = null;
let partialAudioLoaded = false;
let lastSegmentCount = 0;
let pollIntervalTime = 1000; // Start with 1 second polling
let lastProgress = 0;
let noProgressCount = 0;
let pendingSegmentCount = 0; // Track segments available but not yet loaded

// DOM Elements
const urlInput = document.getElementById('urlInput');
const generateBtn = document.getElementById('generateBtn');
const inputSection = document.getElementById('inputSection');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressMessage = document.getElementById('progressMessage');
const progressPercentage = document.getElementById('progressPercentage');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const podcastInfo = document.getElementById('podcastInfo');
const podcastTitle = document.getElementById('podcastTitle');
const podcastAuthor = document.getElementById('podcastAuthor');
const podcastDuration = document.getElementById('podcastDuration');
const playerSection = document.getElementById('playerSection');
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
const actionBar = document.getElementById('actionBar');
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
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Generate button
    generateBtn.addEventListener('click', handleGenerate);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleGenerate();
    });

    // Retry button
    retryBtn.addEventListener('click', resetUI);

    // Audio player controls
    playBtn.addEventListener('click', togglePlayPause);
    timelineSlider.addEventListener('input', handleSeek);
    volumeSlider.addEventListener('input', handleVolumeChange);
    volumeBtn.addEventListener('click', toggleMute);
    downloadBtn.addEventListener('click', handleDownload);

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

// Main Functions
async function handleGenerate() {
    const url = urlInput.value.trim();

    if (!url) {
        showError('Please enter a valid URL');
        return;
    }

    // Validate URL format
    try {
        new URL(url);
    } catch {
        showError('Please enter a valid URL');
        return;
    }

    // Start generation
    try {
        generateBtn.disabled = true;
        hideError();
        showProgress('Initializing...', 0);

        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start generation');
        }

        const data = await response.json();
        currentJobId = data.job_id;

        // Start polling for status
        startPolling();

    } catch (error) {
        showError(error.message);
        generateBtn.disabled = false;
    }
}

function startPolling() {
    // Use recursive setTimeout for adaptive polling
    async function poll() {
        try {
            const response = await fetch(`${API_BASE_URL}/status/${currentJobId}`);

            if (!response.ok) {
                throw new Error('Failed to get job status');
            }

            const data = await response.json();

            // Adaptive polling: adjust interval based on progress
            const currentProgress = data.progress || 0;
            const currentSegments = data.completed_segments || 0;

            if (currentProgress > lastProgress || currentSegments > lastSegmentCount) {
                // Progress detected - keep fast at 1 second
                pollIntervalTime = 1000;
                noProgressCount = 0;
            } else {
                // No progress - increment counter
                noProgressCount++;
                if (noProgressCount >= 3) {
                    // After 3 polls with no progress, slow down to 5 seconds
                    pollIntervalTime = 5000;
                }
            }

            lastProgress = currentProgress;

            // Update progress
            updateProgress(data);

            // Check if completed or failed
            if (data.status === 'completed') {
                stopPolling();
                handleCompletion(data);
            } else if (data.status === 'failed') {
                stopPolling();
                showError(data.error || 'Podcast generation failed');
                generateBtn.disabled = false;
            } else {
                // Schedule next poll with adaptive interval
                pollInterval = setTimeout(poll, pollIntervalTime);
            }

        } catch (error) {
            stopPolling();
            showError('Failed to check status: ' + error.message);
            generateBtn.disabled = false;
        }
    }

    // Start first poll immediately
    poll();
}

function stopPolling() {
    if (pollInterval) {
        clearTimeout(pollInterval);
        pollInterval = null;
    }
    // Reset polling state
    pollIntervalTime = 1000;
    lastProgress = 0;
    noProgressCount = 0;
}

function updateProgress(data) {
    const progress = data.progress || 0;
    const message = data.message || 'Processing...';

    showProgress(message, progress);

    // Check for partial audio availability (progressive playback)
    if (data.partial_audio_url && !partialAudioLoaded) {
        // First time partial audio is available - load it
        loadPartialAudio(data.partial_audio_url, data.completed_segments, data.total_segments);
        partialAudioLoaded = true;
        lastSegmentCount = data.completed_segments;
        pendingSegmentCount = data.completed_segments;
    } else if (data.partial_audio_url && data.completed_segments > lastSegmentCount) {
        // More segments completed - check if we should reload now
        pendingSegmentCount = data.completed_segments;

        const currentTime = audioElement.currentTime || 0;
        const duration = audioElement.duration || 0;
        const timeRemaining = duration - currentTime;

        // Only reload if: not playing, not started yet, or within 5 seconds of the end
        const shouldReloadNow = audioElement.paused || currentTime === 0 || timeRemaining < 5;

        if (shouldReloadNow) {
            reloadPartialAudio(data.partial_audio_url, data.completed_segments, data.total_segments);
            lastSegmentCount = data.completed_segments;
        }
        // Otherwise, let the timeupdate handler reload when appropriate
    }
}

function handleCompletion(data) {
    hideProgress();
    hideBufferingIndicator();  // Hide buffering when complete

    // Reset state for completed podcast
    pendingSegmentCount = 0;
    lastSegmentCount = data.metadata?.dialogue_segments || 0;

    // Display podcast info
    const metadata = data.metadata || {};
    const article = metadata.article || {};
    const audio = metadata.audio || {};

    // Make title clickable if article URL available
    const title = article.title || 'Your Podcast';
    if (article.url) {
        podcastTitle.innerHTML = `<a href="${article.url}" target="_blank" rel="noopener noreferrer" class="podcast-title-link">${title}</a>`;
    } else {
        podcastTitle.textContent = title;
    }

    // Clean author URL for display
    if (article.author) {
        const cleanedAuthor = cleanSourceUrl(article.author);
        podcastAuthor.textContent = cleanedAuthor;
        podcastAuthor.classList.remove('hidden');
    } else {
        podcastAuthor.classList.add('hidden');
    }

    if (audio.duration) {
        podcastDuration.textContent = formatDuration(audio.duration);
    }

    podcastInfo.classList.remove('hidden');

    // Load audio
    const audioUrl = `${API_BASE_URL}/audio/${currentJobId}`;
    loadAudio(audioUrl);

    // Show action bar with download and share if share URL is available
    if (metadata.share_url && actionBar) {
        actionBar.classList.remove('hidden');
    }
}

function loadAudio(url) {
    // Store current playback position if playing (in case we're upgrading from partial to final)
    const currentTime = audioElement.currentTime || 0;
    const wasPlaying = !audioElement.paused;

    // Mark that we're no longer in partial mode
    partialAudioLoaded = false;

    audioElement.src = url;
    audioElement.load();
    playerSection.classList.remove('hidden');

    // Resume playback from previous position if it was playing
    if (wasPlaying && currentTime > 0) {
        audioElement.addEventListener('loadeddata', function onLoaded() {
            audioElement.currentTime = currentTime;
            audioElement.play().catch(() => {
                // Auto-play might be blocked, ignore error
            });
            audioElement.removeEventListener('loadeddata', onLoaded);
        });
    }
}

function loadPartialAudio(url, completed, total) {
    // Store current playback position if playing
    const currentTime = audioElement.currentTime || 0;
    const wasPlaying = !audioElement.paused;

    // Load partial audio
    audioElement.src = url;
    audioElement.load();

    // Show player and buffering indicator
    playerSection.classList.remove('hidden');
    showBufferingIndicator(completed, total);

    // Resume playback from previous position when loaded
    audioElement.addEventListener('loadeddata', function onLoaded() {
        audioElement.currentTime = currentTime;
        if (wasPlaying) {
            audioElement.play().catch(() => {
                // Auto-play might be blocked, ignore error
            });
        }
        audioElement.removeEventListener('loadeddata', onLoaded);
    });
}

function reloadPartialAudio(url, completed, total) {
    // Store current playback position
    const currentTime = audioElement.currentTime || 0;
    const wasPlaying = !audioElement.paused;

    // Update buffering indicator
    showBufferingIndicator(completed, total);

    // Reload audio with new segments
    audioElement.src = url + '&t=' + Date.now(); // Cache busting
    audioElement.load();

    // Resume playback from previous position
    audioElement.addEventListener('loadeddata', function onLoaded() {
        audioElement.currentTime = currentTime;
        if (wasPlaying) {
            audioElement.play().catch(() => {
                // Auto-play might be blocked, ignore error
            });
        }
        audioElement.removeEventListener('loadeddata', onLoaded);
    });
}

function handleAudioLoaded() {
    totalTime.textContent = formatTime(audioElement.duration);
    timelineSlider.max = audioElement.duration;
}

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

function handleTimeUpdate() {
    const current = audioElement.currentTime;
    const duration = audioElement.duration;

    if (duration) {
        const percentage = (current / duration) * 100;
        timelineProgress.style.width = percentage + '%';
        timelineSlider.value = current;
        currentTime.textContent = formatTime(current);

        // Check if we need to load pending segments (when within 5 seconds of end)
        // Only do this if we're still in processing mode (partialAudioLoaded is true)
        const timeRemaining = duration - current;
        if (timeRemaining < 5 && pendingSegmentCount > lastSegmentCount && partialAudioLoaded) {
            // Load the pending segments now
            const partialUrl = `${API_BASE_URL}/audio/${currentJobId}?partial=true`;
            reloadPartialAudio(partialUrl, pendingSegmentCount, 0); // We don't have total here, but it's okay
            lastSegmentCount = pendingSegmentCount;
        }
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

function handleDownload() {
    if (currentJobId) {
        const url = `${API_BASE_URL}/audio/${currentJobId}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `podcast_${currentJobId}.wav`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// UI Helper Functions
function showProgress(message, progress) {
    inputSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    progressSection.classList.remove('hidden');

    progressMessage.textContent = message;
    progressPercentage.textContent = `${Math.round(progress)}%`;
    progressBar.style.width = `${progress}%`;
}

function hideProgress() {
    progressSection.classList.add('hidden');
}

function showError(message) {
    inputSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    errorMessage.textContent = message;
}

function hideError() {
    errorSection.classList.add('hidden');
}

function resetUI() {
    // Stop any ongoing operations
    stopPolling();
    currentJobId = null;

    // Reset audio
    if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
    }

    // Reset progressive playback state
    partialAudioLoaded = false;
    lastSegmentCount = 0;
    pendingSegmentCount = 0;

    // Reset UI elements
    urlInput.value = '';
    generateBtn.disabled = false;

    hideError();
    hideProgress();
    hideBufferingIndicator();
    podcastInfo.classList.add('hidden');
    playerSection.classList.add('hidden');
    inputSection.classList.remove('hidden');

    // Hide action bar and modal
    if (actionBar) {
        actionBar.classList.add('hidden');
    }
    if (shareModal) {
        shareModal.classList.add('hidden');
    }

    // Reset player state
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
    timelineProgress.style.width = '0%';
    timelineSlider.value = 0;
    currentTime.textContent = '0:00';
    totalTime.textContent = '0:00';
}

function showBufferingIndicator(completed, total) {
    // Update progress message to show buffering
    const bufferingMsg = `Playing ${completed}/${total} segments (loading more...)`;
    progressMessage.textContent = bufferingMsg;

    // Show a subtle buffering indicator in the player section only if we have pending content
    if (pendingSegmentCount > lastSegmentCount) {
        let bufferingEl = document.getElementById('bufferingIndicator');
        if (!bufferingEl) {
            bufferingEl = document.createElement('div');
            bufferingEl.id = 'bufferingIndicator';
            bufferingEl.className = 'buffering-indicator';
            bufferingEl.innerHTML = `
                <div class="buffering-spinner"></div>
                <span class="buffering-text">More content available - will load automatically near end</span>
            `;
            playerSection.appendChild(bufferingEl);
        }
        bufferingEl.classList.remove('hidden');
    }
}

function hideBufferingIndicator() {
    const bufferingEl = document.getElementById('bufferingIndicator');
    if (bufferingEl) {
        bufferingEl.classList.add('hidden');
    }
}

// Share Functions
function openShareModal() {
    const shareUrl = `${window.location.origin}/s/${currentJobId.split('-')[0]}`;

    // Try to get actual share URL from job metadata
    fetch(`${API_BASE_URL}/status/${currentJobId}`)
        .then(response => response.json())
        .then(data => {
            if (data.metadata && data.metadata.share_id) {
                const actualShareUrl = `${window.location.origin}/s/${data.metadata.share_id}`;
                shareLinkInput.value = actualShareUrl;
            } else {
                shareLinkInput.value = shareUrl;
            }
        })
        .catch(() => {
            shareLinkInput.value = shareUrl;
        });

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
