# Speechmatics TTS Integration Feedback
## AI Podcast Generator Project

**Date:** October 20, 2025
**Contact:** [Your Name/Team]
**Purpose:** Technical feedback and optimization requests for Speechmatics TTS API

---

## Executive Summary

We're building an AI Podcast Generator that converts articles into conversational podcasts using Speechmatics TTS (Sarah and Theo voices). The service works well but we're experiencing rate limiting that extends generation time to 2-3 minutes per podcast. We'd like to discuss optimization options to achieve 30-60 second generation times while continuing to use Speechmatics TTS.

---

## Project Overview

### What We're Building

**AI Podcast Generator** - A web application that converts articles into 2-minute conversational podcasts featuring two AI hosts discussing key points.

**Architecture:**
- Frontend: JavaScript web app with adaptive polling
- Backend: Python Flask API
- Pipeline: Article scraping → OpenAI GPT-4 script generation → Speechmatics TTS → Audio processing
- Typical Output: 11 dialogue segments, ~2-minute final podcast

### Current Implementation

**API Endpoint:** `https://preview.tts.speechmatics.com/generate/{voice}`
**Voices Used:** Sarah (female) and Theo (male)
**Volume:** ~11 API calls per podcast generation
**Pattern:** Sequential requests with delays between each

**Request Pattern:**
```
Segment 1 (Sarah) → Wait 8s → Segment 2 (Theo) → Wait 8s → Segment 3 (Sarah) → ...
```

**Current Settings:**
- Delay between requests: 8 seconds
- Retry attempts: 4
- Exponential backoff: 2s, 4s, 8s, 16s
- Total generation time: 2-3 minutes for 11 segments

---

## Issues Encountered

### 1. Frequent Rate Limiting (HTTP 429)

**Symptoms:**
- Receiving 429 responses even with 8-second delays between requests
- 20-30% of segments require 1-3 retry attempts
- Unpredictable - some segments succeed immediately, others need multiple retries

**Impact:**
- Adds 2-30 seconds of retry delays per affected segment
- Inconsistent generation times
- Variable user experience

### 2. Service Unavailable Errors (HTTP 503)

**Symptoms:**
- Random 503 errors indicating API overload
- More frequent during apparent peak usage times
- Requires same retry logic as rate limiting

**Impact:**
- Additional unpredictable delays
- Occasional complete failures requiring manual restart

### 3. Speed Constraints

**Current Reality:**
- **Minimum time:** 80 seconds (10 × 8s delays between 11 segments)
- **Typical time:** 90-120 seconds (including some retries)
- **Worst case:** 180+ seconds (frequent retries)

**Competitor Comparison:**
- OpenAI TTS: 30-45 seconds for equivalent podcast
- Google Cloud TTS: 20-30 seconds (with parallel requests)
- ElevenLabs: 45-60 seconds

**Note:** We prefer Speechmatics voice quality but speed is becoming a critical factor for user experience.

---

## Our Optimizations & Workarounds

### Implemented Solutions

1. **Variable Delay Testing**
   - Tested 8s, 10s, and 12s delays
   - 12s was more reliable but too slow for good UX
   - Settled on 8s with increased retry attempts

2. **Increased Retry Attempts** (3 → 4)
   - Improved success rate
   - But adds latency when retries are needed

3. **Adaptive Frontend Polling**
   - Reduced status check frequency to minimize server load
   - Starts at 5s, adjusts to 3s or 10s based on progress
   - Reduces unnecessary API calls by ~40-60%

4. **Exponential Backoff**
   - Implemented 2s, 4s, 8s, 16s retry delays
   - Helps recover from transient issues
   - Works but adds significant time on failures

### Not Implemented (Concerns)

5. **Parallel Requests**
   - Haven't attempted due to rate limiting concerns
   - Would ideally like to process 2-3 segments simultaneously
   - Need guidance on whether this is supported

---

## Requests for Optimization

### High Priority

#### 1. Higher Rate Limits for Preview TTS

**Current Apparent Limit:** ~1 request per 8 seconds
**Requested:** ~1 request per 3-5 seconds, or support for 2-3 concurrent requests

**Impact:** Would reduce generation time from 2-3 minutes to 30-60 seconds

#### 2. Clearer Rate Limit Documentation

**What We Need:**
- Exact rate limits for preview TTS endpoint
- Is it requests/second? requests/minute? concurrent connections?
- Different limits for different API keys/tiers?
- Burst capacity vs sustained rate?

**Why:** Optimize delays based on actual limits instead of trial and error

#### 3. Rate Limit Response Headers

**Current:** Getting 429/503 with no context
**Would Help:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1634567890
Retry-After: 8
```

**Benefit:** Smart backoff implementation based on actual API state

#### 4. Batch/Bulk Endpoint

**Ideal Solution:** Submit all segments at once

**Example Request:**
```json
POST /generate/batch
{
  "segments": [
    {"voice": "sarah", "text": "Welcome to today's podcast..."},
    {"voice": "theo", "text": "Thanks Sarah, let's dive in..."},
    ...
  ]
}
```

**Response:** Job ID with status polling or webhook notification

**Benefit:**
- Server-side rate limiting and optimization
- Faster overall processing
- Better resource utilization

#### 5. WebSocket/Streaming Support

**Use Case:** Real-time streaming TTS for progressive playback
**Benefit:** Start playing audio while rest generates
**Impact:** Perceived speed improvement even if actual generation time similar

---

### Medium Priority

#### 6. Production Tier Access

**Question:** Is there a production endpoint with higher limits?
**Status:** Currently using preview endpoint
**Willingness:** Ready to pay for production-tier access with better performance

#### 7. Regional Endpoints

**Question:** Are there regional endpoints (US, EU, APAC)?
**Benefit:** Lower latency if we can route to geographically closest region
**Current:** Assuming single global endpoint

#### 8. API Key Tiers

**Question:** Can we obtain a higher-tier API key?
**Context:** Building demo now but planning production deployment
**Need:** Better limits for consistent performance

---

## Technical Questions

### Rate Limiting Architecture
1. What is the exact rate limit for the preview TTS endpoint?
2. Is rate limiting per API key, per IP address, or per voice?
3. Can we use multiple API keys to distribute load?
4. What's the difference between 429 (rate limit) and 503 (service unavailable) responses?
5. Is there a burst allowance for short-term higher request rates?

### Performance Optimization
6. Is parallel processing supported? How many concurrent requests are safe?
7. What's the recommended request pattern for podcast/dialogue generation?
8. Are there best practices for sequential dialogue generation with alternating speakers?
9. Is there any caching for identical text inputs?
10. What causes 503 errors - scaling issues, maintenance, or capacity limits?

### Service Tiers
11. Is there a paid tier with higher rate limits?
12. Are there SLAs or guaranteed response times available?
13. Can we get priority access or dedicated capacity for production use?
14. What's the process for upgrading from preview to production?

---

## What We Love About Speechmatics TTS

Before focusing only on issues, here's what's working excellently:

✅ **Voice Quality:** Sarah and Theo sound natural and conversational - better than most competitors
✅ **Consistency:** Voices remain consistent across all segments
✅ **Reliability:** When respecting rate limits, system works predictably
✅ **API Design:** Simple, clean REST API that's easy to integrate
✅ **Documentation:** Clear getting-started documentation
✅ **Audio Format:** Clean WAV output that's easy to process
✅ **Voice Selection:** Sarah and Theo are perfect for conversational podcast format

---

## Ideal Scenario

**If Speechmatics could offer:**
1. Support for 2-3 concurrent requests per API key, OR
2. Batch processing endpoint for dialogue generation, OR
3. Clear rate limit guidance allowing 3-5 second delays

**We could achieve:**
- 30-45 second generation times (competitive with alternatives)
- Reliable, consistent performance
- Excellent user experience
- Strong commitment to Speechmatics for production deployment

---

## Current Situation

We're evaluating alternatives (OpenAI TTS, ElevenLabs, Google Cloud TTS) primarily due to speed requirements, not quality concerns. **Speechmatics voices are excellent** - we simply need faster throughput for an acceptable user experience.

**We strongly prefer to continue with Speechmatics** if we can achieve faster generation times through:
- Higher rate limits
- Batch processing capabilities
- Better optimization guidance
- Production-tier access

---

## Performance Statistics

### Current Performance Metrics

| Metric | Value |
|--------|-------|
| Total Generation Time | 2-3 minutes |
| Segments Requiring Retries | 20-30% |
| Typical Retries Per Segment | 1-3 attempts |
| Success Rate | ~100% (with retry logic) |
| User Experience | Variable/Unpredictable |

### Desired Performance Metrics

| Metric | Target |
|--------|--------|
| Total Generation Time | 30-60 seconds |
| Segments Requiring Retries | <5% |
| Typical Retries Per Segment | Rare |
| Success Rate | ~100% |
| User Experience | Fast/Consistent |

---

## Code Implementation Example

### Current TTS Request Pattern

```python
def generate_dialogue_audio(self, dialogue: List[Dict], output_dir: str):
    """Generate audio for dialogue segments sequentially"""
    for segment in dialogue:
        # Generate audio for this segment
        audio_data = self.generate_speech(segment['text'], segment['speaker'])

        # Save audio file
        save_audio(audio_data, output_dir)

        # Wait 8 seconds before next request to avoid rate limiting
        time.sleep(8)
```

### Retry Logic with Exponential Backoff

```python
def generate_speech(self, text: str, voice: str, max_retries: int = 4):
    """Generate speech with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(voice_url, headers=headers, json=data)
            response.raise_for_status()
            return response.content

        except requests.RequestException as e:
            if e.response.status_code in [503, 429]:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2, 4, 8, 16 seconds
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
                    continue
            raise
```

---

## Next Steps

We'd appreciate the opportunity to discuss:

1. **Immediate:** Understanding actual rate limits and recommended usage patterns
2. **Short-term:** Accessing higher-tier API keys or production endpoints
3. **Long-term:** Batch processing or streaming capabilities for dialogue generation

We're excited about using Speechmatics TTS for production and would value guidance on optimizing our implementation for the best performance possible.

---

## Contact Information

**Project Repository:** [Add if applicable]
**Technical Contact:** [Your email/contact]
**Preferred Communication:** [Email/Slack/Meeting]

Thank you for considering this feedback. We're looking forward to working together to optimize our Speechmatics TTS integration!
