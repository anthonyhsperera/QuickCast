from openai import OpenAI
from typing import List, Dict
import json
import re

class PodcastScriptGenerator:
    """Generates podcast dialogue from article content using OpenAI"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def generate_podcast_script(self, article: Dict[str, str], target_duration: float = 2.5) -> List[Dict[str, str]]:
        """
        Generate a conversational podcast script from an article

        Args:
            article: Dictionary containing title, author, content, and url
            target_duration: Target duration in minutes (default: 2.0)

        Returns:
            List of dialogue segments with speaker and text
        """
        # Prepare the prompt
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(article, target_duration)

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=1600
            )

            # Parse the response
            script_text = response.choices[0].message.content
            dialogue = self._parse_dialogue(script_text)

            return dialogue

        except Exception as e:
            raise Exception(f"Failed to generate podcast script: {str(e)}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are a podcast script writer who creates SHORT, engaging conversational dialogues between two hosts: Sarah and Theo.

Sarah is enthusiastic, curious, and asks insightful questions. She often brings up interesting angles.
Theo is knowledgeable, analytical, and great at explaining complex topics simply. He's warm and engaging.

Your task is to transform articles into BRIEF, natural podcast conversations that:
- Sound like real people talking (use contractions, natural speech patterns)
- Make complex topics accessible and interesting
- Include back-and-forth dialogue with questions, reactions, and insights
- Are CONCISE and focused on the main points only
- Keep each speaker turn relatively short (1-3 sentences max)

Format your output EXACTLY as:
SARAH: [dialogue text]
THEO: [dialogue text]
SARAH: [dialogue text]
...and so on.

Each line should start with either "SARAH:" or "THEO:" followed by their dialogue."""

    def _get_user_prompt(self, article: Dict[str, str], target_duration: float) -> str:
        """Generate the user prompt with article content"""
        word_count = int(target_duration * 150)  # Approximate words for target duration

        return f"""Transform the following article into a {target_duration}-minute podcast conversation between Sarah and Theo.

Article Title: {article['title']}

Article Content:
{article['content'][:4000]}  # Limit content

Instructions:
- Keep each line concise (1-2 sentences)
- ~{word_count} words total
- Structure:
  * Sarah introduces topic
  * Discuss 2-3 key points with natural back-and-forth
  * Theo wraps up with insights
  * Sarah thanks listeners

Format each line as:
SARAH: [text]
THEO: [text]

Begin the podcast script:"""

    def _parse_dialogue(self, script_text: str) -> List[Dict[str, str]]:
        """Parse the LLM output into structured dialogue segments"""
        dialogue = []

        # Split by lines and process
        lines = script_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match pattern: "SPEAKER: dialogue"
            match = re.match(r'^(SARAH|THEO):\s*(.+)$', line, re.IGNORECASE)

            if match:
                speaker = match.group(1).upper()
                text = match.group(2).strip()

                # Map to voice names
                voice = "sarah" if speaker == "SARAH" else "theo"

                dialogue.append({
                    "speaker": voice,
                    "text": text
                })

        if not dialogue:
            raise ValueError("Failed to parse dialogue from LLM response")

        return dialogue

    def estimate_duration(self, dialogue: List[Dict[str, str]]) -> float:
        """Estimate the duration of the podcast in minutes"""
        total_words = sum(len(segment['text'].split()) for segment in dialogue)
        # Average speaking rate is ~150 words per minute
        estimated_minutes = total_words / 150
        return round(estimated_minutes, 1)
