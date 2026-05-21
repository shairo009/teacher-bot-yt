import os
import json
from pathlib import Path


class TopicManager:
    def __init__(self, progress_file="data/topics_progress.json", index_file="data/topics_index.json", curriculum_file="curriculum_master.json"):
        self.progress_file = Path(progress_file)
        self.index_file = Path(index_file)
        self.curriculum_file = Path(curriculum_file)
        self.index = []
        self.progress = {
            "current_idx": 0,
            "completed_ids": [],
            "total_completed": 0,
            "last_updated": None,
            "current_class": 1
        }
        self._load()

    def _load_curriculum(self):
        """Load the master curriculum."""
        if self.curriculum_file.exists():
            with open(self.curriculum_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        fallback_file = Path("curriculum.json")
        if fallback_file.exists():
            with open(fallback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def build_from_curriculum(self):
        """Build index based on the master curriculum (Class 1 to 15)."""
        curr = self._load_curriculum()
        if not curr: return []
        
        index = []
        topic_id = 0
        
        def get_level_str(class_num):
            if class_num == 11:
                return "Class 11"
            elif class_num == 12:
                return "Class 12"
            elif class_num == 13:
                return "Undergraduate"
            elif class_num == 14:
                return "Masters Level"
            elif class_num == 15:
                return "PhD Level"
            else:
                return f"Class {class_num}"
        
        # Check if it has the flat 'curriculum' key structure or the nested 'classes' structure
        if 'curriculum' in curr:
            # Flat list of chapter entries
            for entry in sorted(curr['curriculum'], key=lambda x: (x.get('class', 1), x.get('chapter', 1))):
                class_num = entry.get('class', 1)
                chapter_num = entry.get('chapter', 1)
                chapter_name = entry.get('topic', '')
                subtopics = entry.get('subtopics', [])
                for sub in subtopics:
                    topic_id += 1
                    index.append({
                        'id': topic_id,
                        'class': class_num,
                        'chapter': f"Chapter {chapter_num}: {chapter_name}",
                        'topic': sub,
                        'level': get_level_str(class_num),
                        'source': 'curriculum'
                    })
        elif 'classes' in curr:
            # Nested structure
            for class_data in sorted(curr['classes'], key=lambda x: x['class']):
                class_num = class_data['class']
                for chapter_data in sorted(class_data['chapters'], key=lambda x: x['chapter']):
                    chapter_num = chapter_data['chapter']
                    topic_name = chapter_data['topic']
                    for sub in chapter_data['subtopics']:
                        topic_id += 1
                        index.append({
                            'id': topic_id,
                            'class': class_num,
                            'chapter': f"Chapter {chapter_num}: {topic_name}",
                            'topic': sub,
                            'level': get_level_str(class_num),
                            'source': 'curriculum'
                        })
        self.index = index
        return index

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
        """Get the next topic to be taught. Loops infinitely."""
        if not self.index:
            return None

        idx = self.progress.get('current_idx', 0)
        if idx >= len(self.index):
            # All topics completed - RESET for infinite lifetime loop!
            print("🔄 Reached end of book! Restarting from Chapter 1 for infinite loop...")
            self.reset()
            idx = 0

        return self.index[idx]

    def mark_completed(self, topic_id):
        """Mark a topic as completed and move to next."""
        if topic_id not in self.progress.get('completed_ids', []):
            self.progress['completed_ids'].append(topic_id)

        # Move to next index
        self.progress['current_idx'] += 1
        
        # Check if we reached the end
        if self.progress['current_idx'] >= len(self.index):
            print("🔄 Reached end of book! Resetting index for next run...")
            self.progress['current_idx'] = 0

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