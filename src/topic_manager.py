import os
import json
from pathlib import Path


class TopicManager:
    def __init__(self, progress_file="data/topics_progress.json", index_file="data/topics_index.json"):
        self.progress_file = Path(progress_file)
        self.index_file = Path(index_file)
        self.index = []
        self.progress = {
            "current_idx": 0,
            "completed_ids": [],
            "total_completed": 0,
            "last_updated": None
        }
        self._load()

    def _load(self):
        # Load progress
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    self.progress = json.load(f)
            except Exception:
                pass

        # Load index
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.index = data.get('topics', [])
            except Exception:
                pass

    def _save_progress(self):
        self.progress['last_updated'] = str(Path(__file__).stat().st_mtime if Path(__file__).exists() else "now")
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def load_index(self, all_content):
        """Rebuild index from extracted content."""
        index = []
        chapter_id = 0

        for book in sorted(all_content, key=lambda x: x['class']):
            class_num = book['class']
            medium = book['medium']
            chapters = book['chapters']

            for chapter in chapters:
                chapter_id += 1
                chapter_name = chapter['chapter']
                topics = chapter['topics']

                for topic_idx, topic_text in enumerate(topics):
                    index.append({
                        'id': chapter_id * 1000 + topic_idx,
                        'class': class_num,
                        'medium': medium,
                        'chapter': chapter_name,
                        'topic_idx': topic_idx,
                        'topic': topic_text,
                        'source': book['source']
                    })

        self.index = index
        return index

    def get_current_topic(self):
        """Get the next topic to be taught (skips already completed)."""
        if not self.index:
            return None

        completed = set(self.progress.get('completed_ids', []))
        idx = self.progress.get('current_idx', 0)

        # Skip forward past any already-completed topics (prevents repeats)
        while idx < len(self.index) and self.index[idx].get('id') in completed:
            idx += 1

        if idx >= len(self.index):
            return None

        # Update idx if we skipped ahead
        if idx != self.progress.get('current_idx', 0):
            self.progress['current_idx'] = idx
            self._save_progress()

        return self.index[idx]

    def mark_completed(self, topic_id):
        """Mark a topic as completed and move to next."""
        if topic_id not in self.progress.get('completed_ids', []):
            self.progress['completed_ids'].append(topic_id)

        self.progress['current_idx'] += 1
        self.progress['total_completed'] = len(self.progress['completed_ids'])
        self._save_progress()

        print(f"Topic {topic_id} completed. Progress: {self.progress['current_idx']}/{len(self.index)}")

    def get_progress_stats(self):
        """Return progress statistics."""
        return {
            'total_topics': len(self.index),
            'completed': self.progress.get('current_idx', 0),
            'remaining': len(self.index) - self.progress.get('current_idx', 0),
            'percentage': round((self.progress.get('current_idx', 0) / max(len(self.index), 1)) * 100, 1)
        }

    def reset(self):
        """Reset progress to start from beginning."""
        self.progress = {
            "current_idx": 0,
            "completed_ids": [],
            "total_completed": 0,
            "last_updated": None
        }
        self._save_progress()
        print("Progress reset!")

    def skip_topic(self, count=1):
        """Skip N topics."""
        self.progress['current_idx'] = min(
            self.progress.get('current_idx', 0) + count,
            len(self.index) - 1
        )
        self._save_progress()


if __name__ == "__main__":
    manager = TopicManager()
    stats = manager.get_progress_stats()
    print(f"Progress: {stats['completed']}/{stats['total_topics']} ({stats['percentage']}%)")

    topic = manager.get_current_topic()
    if topic:
        print(f"Current topic: Class {topic['class']} | {topic['chapter']} | {topic['topic'][:50]}...")
    else:
        print("No more topics! All completed.")