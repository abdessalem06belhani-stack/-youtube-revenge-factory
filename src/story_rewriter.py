"""
AI Story Rewriter — يعيد كتابة القصص المستخرجة من يوتيوب
بهيكل درامي 3 acts مع hook قوي + cliffhanger كل 10 دقائق + نهاية عاطفية.
Primary: NVIDIA NIM (Llama 3.1 70B) — مجاني غير محدود
Backup: Google Gemini (1M tokens/min) — مجاني
"""
from __future__ import annotations
import json, os, re, time, random
from typing import Dict, List, Optional
from datetime import datetime
import requests

class StoryRewriter:
    """
    Rewrites raw YouTube stories into dramatic 3-act narratives
    optimized for YouTube retention (hook, cliffhangers, CTA).
    """
    
    def __init__(self):
        self.nvidia_key = os.getenv("NVIDIA_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.nvidia_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        # Retention rules for the rewrite prompt
        self.retention_rules = """
CRITICAL RETENTION RULES (FOLLOW EXACTLY):
1. HOOK (first 5 seconds): Start with a shocking/emotional sentence that makes viewers stop scrolling
2. NARRATIVE STYLE: First person (I, my, me) - creates empathy
3. CLIFFHANGER: Every 10 minutes (600 seconds) add a cliffhanger sentence
4. MINI-CLIFFHANGER: Every 20 minutes add a smaller hook
5. ENDING: Unexpected twist + moral lesson + interactive question
6. CTA: "Drop a comment and be sure to subscribe" at the end
7. PACING: Fast during action, slow during emotional moments
8. LENGTH: Each scene 2-5 minutes, total 45-60 minutes of narration
9. BACKGROUND KEYWORDS: Include 3-5 keywords per scene for image search
10. MOOD: Tag each scene with one emotional mood
"""
        
        self.system_prompt = f"""You are a professional YouTube revenge-story writer. 
Your job is to transform raw stories into engaging 3-act dramatic narratives.
{self.retention_rules}

OUTPUT FORMAT (JSON ONLY):
{{
  "title": "Catchy YouTube Title with — Twist",
  "hook": "First shocking sentence (max 20 words)",
  "acts": [
    {{
      "act_number": 1,
      "title": "The Betrayal",
      "scenes": [
        {{
          "number": 1,
          "narration": "Full narration text for this scene...",
          "duration_sec": 120,
          "mood": "tense_family|sadness|anger|betrayal|justice|revenge|victory|reflection|confrontation|resolution|greed|love|loss|hope",
          "background_keywords": "4-5 comma-separated keywords for image search"
        }}
      ]
    }}
  ],
  "cliffhangers": [
    {{"at_sec": 600, "text": "Cliffhanger text for 10-minute mark..."}},
    {{"at_sec": 1200, "text": "Cliffhanger text for 20-minute mark..."}}
  ],
  "ending": "Emotional ending narration (2-3 sentences)",
  "moral": "Life lesson from the story (1 sentence)",
  "cta": "Subscribe call to action (1 sentence)"
}}

TOTAL NARRATION LENGTH: 45-60 minutes when read aloud
SCENE DURATION: Each scene 120-300 seconds
CLIFFHANGERS: Every 600 seconds (adjust count to video length)
"""
    
    def rewrite(self, raw_story: Dict, target_duration_min: int = 50) -> Optional[Dict]:
        """
        Rewrite a raw story into a dramatic 3-act structure.
        
        Args:
            raw_story: Dict with transcript/description from ContentFinder
            target_duration_min: Target video duration in minutes
            
        Returns: Dict with rewritten story (title, acts, cliffhangers, etc.)
        """
        # Get the source text
        source_text = raw_story.get("transcript") or raw_story.get("original_description", "")
        if not source_text or len(source_text) < 100:
            print(f"  ✗ Source text too short ({len(source_text)} chars)")
            return None
        
        title_hint = raw_story.get("original_title", "revenge story")
        hashtags = raw_story.get("hashtags", [])
        
        print(f"  Rewriting: '{title_hint}' ({len(source_text)} chars)")
        
        # Calculate approximate scenes needed
        scenes_needed = target_duration_min * 60 // 150  # ~150 seconds per scene average
        acts_needed = 3
        cliffhangers_count = target_duration_min // 10  # Every 10 minutes
        
        user_prompt = f"""Transform this true revenge/family-drama story into a dramatic {target_duration_min}-minute video script.

SOURCE TITLE: {title_hint}
SOURCE HASHTAGS: {', '.join(hashtags[:10])}

RAW STORY:
{source_text[:8000]}

REQUIREMENTS:
- {acts_needed} acts with {scenes_needed} total scenes
- {cliffhangers_count} cliffhangers at regular intervals
- Hook in first sentence
- Emotional ending with moral lesson
- Each scene has mood and background_keywords for video production
- Target narration time: {target_duration_min} minutes

OUTPUT AS JSON ONLY."""
        
        # Try NVIDIA NIM first
        result = self._call_nvidia(user_prompt)
        if not result:
            print("  Trying Gemini as fallback...")
            result = self._call_gemini(user_prompt)
        
        if result:
            # Add metadata
            result["source_title"] = title_hint
            result["source_video_id"] = raw_story.get("video_id", "")
            result["target_duration_min"] = target_duration_min
            result["total_scenes"] = sum(len(act["scenes"]) for act in result.get("acts", []))
            result["total_cliffhangers"] = len(result.get("cliffhangers", []))
            result["rewritten_at"] = datetime.now().isoformat()
            
            print(f"  ✓ Rewritten: {result.get('title', 'Untitled')}")
            print(f"    → {result['total_scenes']} scenes, {result['total_cliffhangers']} cliffhangers")
            return result
        
        print(f"  ✗ All AI APIs failed")
        return None
    
    def _call_nvidia(self, prompt: str) -> Optional[Dict]:
        """Call NVIDIA NIM API (free, Llama 3.1 70B)."""
        if not self.nvidia_key:
            print("  ⚠ No NVIDIA_API_KEY set")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.nvidia_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta/llama-3.1-70b-instruct",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 8192,
            "top_p": 0.95,
        }
        
        try:
            resp = requests.post(
                self.nvidia_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)
            
        except requests.exceptions.Timeout:
            print("  ⚠ NVIDIA NIM timeout (120s)")
        except Exception as e:
            print(f"  ⚠ NVIDIA NIM error: {e}")
        
        return None
    
    def _call_gemini(self, prompt: str) -> Optional[Dict]:
        """Call Google Gemini API (free, 1M tokens/min)."""
        if not self.gemini_key:
            print("  ⚠ No GEMINI_API_KEY set")
            return None
        
        url = f"{self.gemini_url}?key={self.gemini_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{self.system_prompt}\n\n{prompt}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,
                "topP": 0.95,
            }
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_response(text)
            
        except Exception as e:
            print(f"  ⚠ Gemini error: {e}")
        
        return None
    
    def _parse_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from AI response, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # Clean the content
        content = content.strip()
        
        # Try parsing JSON
        for attempt in range(3):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try fixing common issues
                if attempt == 0:
                    # Try finding JSON boundaries
                    start = content.find('{')
                    end = content.rfind('}')
                    if start >= 0 and end > start:
                        content = content[start:end+1]
                        continue
                elif attempt == 1:
                    # Try escaping quotes
                    content = content.replace("'", '"')
                    continue
                else:
                    print(f"  ✗ Failed to parse AI response as JSON")
                    # Save raw response for debugging
                    debug_path = f"data/rewritten/debug_{int(time.time())}.txt"
                    os.makedirs("data/rewritten", exist_ok=True)
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  Saved debug output: {debug_path}")
                    return None
        
        return None
    
    def batch_rewrite(self, stories: List[Dict], output_dir: str = "data/rewritten") -> List[Dict]:
        """Rewrite multiple stories."""
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, story in enumerate(stories):
            print(f"\n[{i+1}/{len(stories)}] Rewriting...")
            result = self.rewrite(story)
            if result:
                # Save individual result
                video_id = story.get("video_id", f"story_{i}")
                outfile = os.path.join(output_dir, f"{video_id}_rewritten.json")
                with open(outfile, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"  Saved: {outfile}")
                results.append(result)
        
        # Save batch summary
        summary = os.path.join(output_dir, "batch_summary.json")
        with open(summary, 'w', encoding='utf-8') as f:
            json.dump({
                "total": len(results),
                "rewritten_at": datetime.now().isoformat(),
                "stories": [{
                    "title": r.get("title"),
                    "scenes": r.get("total_scenes"),
                    "cliffhangers": r.get("total_cliffhangers"),
                } for r in results]
            }, f, indent=2)
        
        print(f"\n✓ Batch complete: {len(results)} stories rewritten")
        return results


def main():
    import argparse, json, glob
    
    parser = argparse.ArgumentParser(description="AI Story Rewriter")
    parser.add_argument("--input", help="Raw story JSON file from ContentFinder")
    parser.add_argument("--input-dir", help="Directory with multiple raw story JSON files")
    parser.add_argument("--duration", type=int, default=50, help="Target video duration (min)")
    parser.add_argument("--output", default="data/rewritten", help="Output directory")
    args = parser.parse_args()
    
    rewriter = StoryRewriter()
    
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            story = json.load(f)
        result = rewriter.rewrite(story, args.duration)
        if result:
            os.makedirs(args.output, exist_ok=True)
            outfile = os.path.join(args.output, f"{story.get('video_id', 'story')}_rewritten.json")
            with open(outfile, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n✓ Done! Saved: {outfile}")
    
    elif args.input_dir:
        stories = []
        for fpath in glob.glob(os.path.join(args.input_dir, "*_raw.json")):
            with open(fpath, 'r', encoding='utf-8') as f:
                stories.append(json.load(f))
        rewriter.batch_rewrite(stories, args.output)

if __name__ == "__main__":
    main()