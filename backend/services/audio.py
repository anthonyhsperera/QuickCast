from pydub import AudioSegment
from typing import List, Dict
import os

class AudioProcessor:
    """Handles audio processing and combining"""

    def __init__(self, pause_duration: int = 500):
        """
        Initialize audio processor

        Args:
            pause_duration: Duration of pause between speakers in milliseconds (default: 500ms)
        """
        self.pause_duration = pause_duration

    def combine_segments(self, segments: List[Dict[str, any]], output_path: str) -> Dict[str, any]:
        """
        Combine audio segments into a single podcast file

        Args:
            segments: List of audio segments with filepath and metadata
            output_path: Path to save the combined audio file

        Returns:
            Dictionary with metadata about the combined audio
        """
        if not segments:
            raise ValueError("No audio segments to combine")

        try:
            # Create an empty audio segment
            combined_audio = AudioSegment.empty()

            # Create a silent pause segment
            pause = AudioSegment.silent(duration=self.pause_duration)

            total_duration = 0
            segment_timings = []

            # Combine all segments
            for segment in segments:
                # Load the audio file
                audio = AudioSegment.from_wav(segment['filepath'])

                # Record timing
                start_time = total_duration
                duration = len(audio) / 1000.0  # Convert to seconds

                segment_timings.append({
                    'speaker': segment['speaker'],
                    'text': segment['text'],
                    'start': start_time,
                    'duration': duration
                })

                # Add the audio segment
                combined_audio += audio

                # Add pause (except after the last segment)
                if segment != segments[-1]:
                    combined_audio += pause
                    total_duration += duration + (self.pause_duration / 1000.0)
                else:
                    total_duration += duration

            # Export the combined audio
            combined_audio.export(output_path, format="wav")

            # Get file size
            file_size = os.path.getsize(output_path)

            return {
                'filepath': output_path,
                'duration': total_duration,
                'file_size': file_size,
                'segment_count': len(segments),
                'timings': segment_timings
            }

        except Exception as e:
            raise Exception(f"Failed to combine audio segments: {str(e)}")

    def normalize_audio(self, audio_path: str) -> None:
        """
        Normalize audio levels for consistent volume

        Args:
            audio_path: Path to the audio file to normalize
        """
        try:
            audio = AudioSegment.from_wav(audio_path)

            # Normalize to -20 dBFS
            normalized_audio = audio.normalize()

            # Save back to the same file
            normalized_audio.export(audio_path, format="wav")

        except Exception as e:
            raise Exception(f"Failed to normalize audio: {str(e)}")

    def add_intro_outro(self, main_audio_path: str, intro_path: str = None, outro_path: str = None, output_path: str = None) -> str:
        """
        Add intro and/or outro music to the podcast

        Args:
            main_audio_path: Path to the main podcast audio
            intro_path: Path to intro music (optional)
            outro_path: Path to outro music (optional)
            output_path: Path to save the final audio (default: overwrites main_audio_path)

        Returns:
            Path to the final audio file
        """
        try:
            audio = AudioSegment.from_wav(main_audio_path)

            if intro_path and os.path.exists(intro_path):
                intro = AudioSegment.from_file(intro_path)
                audio = intro + audio

            if outro_path and os.path.exists(outro_path):
                outro = AudioSegment.from_file(outro_path)
                audio = audio + outro

            final_path = output_path or main_audio_path
            audio.export(final_path, format="wav")

            return final_path

        except Exception as e:
            raise Exception(f"Failed to add intro/outro: {str(e)}")

    def combine_from_directory(self, output_dir: str, output_path: str, max_segments: int = None) -> bool:
        """
        Combine audio segment files from a directory (for progressive combining)

        Args:
            output_dir: Directory containing segment_XXX_*.wav files
            output_path: Path to save the combined audio
            max_segments: Maximum number of segments to combine (None = all)

        Returns:
            True if successful, False if no segments found
        """
        try:
            # Find all segment files
            import glob
            segment_files = sorted(glob.glob(os.path.join(output_dir, "segment_*.wav")))

            if not segment_files:
                return False

            # Limit to max_segments if specified
            if max_segments:
                segment_files = segment_files[:max_segments]

            # Create combined audio
            combined_audio = AudioSegment.empty()
            pause = AudioSegment.silent(duration=self.pause_duration)

            for i, filepath in enumerate(segment_files):
                audio = AudioSegment.from_wav(filepath)
                combined_audio += audio

                # Add pause except after last segment
                if i < len(segment_files) - 1:
                    combined_audio += pause

            # Export
            combined_audio.export(output_path, format="wav")
            return True

        except Exception as e:
            print(f"Error combining from directory: {e}")
            return False

    def get_audio_info(self, audio_path: str) -> Dict[str, any]:
        """
        Get information about an audio file

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary with audio metadata
        """
        try:
            audio = AudioSegment.from_wav(audio_path)

            return {
                'duration': len(audio) / 1000.0,  # in seconds
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'file_size': os.path.getsize(audio_path)
            }

        except Exception as e:
            raise Exception(f"Failed to get audio info: {str(e)}")
