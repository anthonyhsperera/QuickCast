import requests
from typing import Dict, List, Callable
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class SpeechmaticsTTS:
    """Handles text-to-speech conversion using Speechmatics API"""

    def __init__(self, api_key: str, base_url: str = "https://preview.tts.speechmatics.com/generate"):
        self.api_key = api_key
        self.base_url = base_url
        self.sample_rate = 16000

    def generate_speech(self, text: str, voice: str, max_retries: int = 4) -> bytes:
        """
        Generate speech audio from text using specified voice

        Args:
            text: The text to convert to speech
            voice: The voice to use ('sarah' or 'theo')
            max_retries: Maximum number of retry attempts (default: 4)

        Returns:
            WAV audio data as bytes
        """
        voice_url = f"{self.base_url}/{voice.lower()}"

        data = {
            "text": text
        }

        last_error = None

        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                response = requests.post(voice_url, headers=headers, json=data, timeout=30)

                # Log any non-200 status codes
                if response.status_code != 200:
                    print(f"⚠️  Non-200 response: {response.status_code} for voice '{voice}' (attempt {attempt + 1}/{max_retries})")
                    try:
                        error_body = response.text[:200]  # First 200 chars of response
                        print(f"   Response body: {error_body}")
                    except:
                        pass

                response.raise_for_status()

                wav_data = response.content

                if not wav_data or len(wav_data) < 44:
                    raise ValueError(f"Invalid audio data received for voice {voice}")

                return wav_data

            except requests.RequestException as e:
                last_error = e

                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    print(f"HTTP {status_code} error for voice '{voice}' (attempt {attempt + 1}/{max_retries})")

                    if status_code in [503, 429]:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** (attempt + 1)
                            print(f"   Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"   Max retries reached")
                    else:
                        print(f"   Non-retryable error: {status_code}")

                raise Exception(f"Failed to generate speech for {voice}: {str(e)}")

        # If we exhausted all retries
        raise Exception(f"Failed to generate speech for {voice} after {max_retries} attempts: {str(last_error)}")

    def generate_dialogue_audio(self, dialogue: List[Dict[str, str]], output_dir: str,
                                 progress_callback: Callable[[int, int], None] = None) -> List[Dict[str, any]]:
        """
        Generate audio for dialogue segments

        Args:
            dialogue: List of dialogue segments with speaker and text
            output_dir: Directory to save audio files
            progress_callback: Optional callback function(completed, total) for progress updates

        Returns:
            List of audio segments with metadata
        """
        os.makedirs(output_dir, exist_ok=True)

        audio_segments = []
        total_segments = len(dialogue)
        batch_size = 2

        print(f"Processing {total_segments} segments in batches of {batch_size}...")

        # Process segments in batches
        for batch_start in range(0, total_segments, batch_size):
            batch_end = min(batch_start + batch_size, total_segments)
            batch = dialogue[batch_start:batch_end]

            # Process this batch in parallel
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit tasks for this batch
                future_to_idx = {}
                for i, segment in enumerate(batch):
                    actual_idx = batch_start + i
                    future = executor.submit(
                        self._generate_segment,
                        segment,
                        actual_idx,
                        output_dir
                    )
                    future_to_idx[future] = actual_idx

                # Wait for all tasks in this batch to complete
                batch_results = {}
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result = future.result()
                        batch_results[idx] = result
                    except Exception as e:
                        raise Exception(f"Failed to generate audio for segment {idx}: {str(e)}")

            # Add completed segments in order
            for idx in sorted(batch_results.keys()):
                audio_segments.append(batch_results[idx])

            # Update progress
            completed = len(audio_segments)
            if progress_callback:
                progress_callback(completed, total_segments)

            print(f"Completed: {completed}/{total_segments} segments")

        print(f"All {total_segments} segments generated successfully")
        return audio_segments

    def _generate_segment(self, segment: Dict[str, str], idx: int, output_dir: str) -> Dict[str, any]:
        """Generate audio for a single dialogue segment"""
        speaker = segment['speaker']
        text = segment['text']

        # Generate audio
        audio_data = self.generate_speech(text, speaker)

        # Save to file
        filename = f"segment_{idx:03d}_{speaker}.wav"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(audio_data)

        # Calculate duration
        audio_bytes = len(audio_data) - 44  # Remove WAV header
        samples = audio_bytes // 2  # 16-bit = 2 bytes per sample
        duration = samples / self.sample_rate

        return {
            'index': idx,
            'speaker': speaker,
            'text': text,
            'filepath': filepath,
            'duration': duration,
            'audio_data': audio_data
        }

    def calculate_audio_duration(self, wav_data: bytes) -> float:
        """Calculate the duration of WAV audio data in seconds"""
        if len(wav_data) < 44:
            return 0.0

        audio_bytes = len(wav_data) - 44  # Remove WAV header
        samples = audio_bytes // 2  # 16-bit = 2 bytes per sample
        duration = samples / self.sample_rate

        return duration
