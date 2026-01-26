#!/usr/bin/env python3
"""
Copy1 Entity - First-pass duplicate manager with shadow token conversion
Converts duplicate files to shadow tokens attached to origin document
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent))
from decision_engine import NaniCommandEntity, DecisionContext, DecisionState, quick_execute


@dataclass
class ShadowToken:
    """Shadow token representing a duplicate file"""
    original_path: str
    shadow_id: str
    created: str
    file_hash: str
    size: int
    gravity_well: str  # work, play, or create
    rubric_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkPlayCreateRubric:
    """
    Rubric for assigning shadows to gravity wells based on content analysis
    Scores: work (productive), play (exploratory), create (generative)
    """

    def __init__(self):
        # Keywords/patterns for each category
        self.work_indicators = [
            'project', 'plan', 'todo', 'task', 'meeting', 'report', 'analysis',
            'budget', 'schedule', 'deadline', 'milestone', 'requirements',
            'specification', 'documentation', 'proposal', 'review'
        ]

        self.play_indicators = [
            'experiment', 'test', 'prototype', 'explore', 'try', 'idea',
            'brainstorm', 'draft', 'sketch', 'playground', 'sandbox',
            'discovery', 'research', 'investigate', 'curiosity'
        ]

        self.create_indicators = [
            'design', 'build', 'create', 'generate', 'compose', 'write',
            'develop', 'craft', 'construct', 'make', 'produce', 'author',
            'art', 'story', 'narrative', 'vision', 'imagine', 'invent'
        ]

    def score_content(self, file_path: str, content: Optional[str] = None) -> Dict[str, float]:
        """
        Score file content on work/play/create dimensions
        Returns dict with scores 0.0-1.0 for each
        """
        if content is None:
            try:
                # Try to read if text-based
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10000)  # First 10KB
            except:
                # Can't read, use filename only
                content = str(file_path).lower()

        content_lower = content.lower()

        # Count indicators
        work_count = sum(1 for word in self.work_indicators if word in content_lower)
        play_count = sum(1 for word in self.play_indicators if word in content_lower)
        create_count = sum(1 for word in self.create_indicators if word in content_lower)

        total = work_count + play_count + create_count

        if total == 0:
            # No clear indicators, use defaults based on file type
            return self._score_by_filetype(file_path)

        # Normalize to 0-1
        scores = {
            'work': work_count / total,
            'play': play_count / total,
            'create': create_count / total
        }

        return scores

    def _score_by_filetype(self, file_path: str) -> Dict[str, float]:
        """Fallback scoring based on file extension"""
        ext = Path(file_path).suffix.lower()

        # Document types
        if ext in ['.docx', '.pdf', '.txt', '.md', '.odt']:
            return {'work': 0.5, 'play': 0.2, 'create': 0.3}

        # Code types
        elif ext in ['.py', '.js', '.sh', '.json', '.yaml']:
            return {'work': 0.4, 'play': 0.3, 'create': 0.3}

        # Media types
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3']:
            return {'work': 0.2, 'play': 0.2, 'create': 0.6}

        # Data types
        elif ext in ['.csv', '.xlsx', '.db', '.sql']:
            return {'work': 0.7, 'play': 0.2, 'create': 0.1}

        # Default
        else:
            return {'work': 0.33, 'play': 0.33, 'create': 0.34}

    def assign_gravity_well(self, scores: Dict[str, float]) -> str:
        """Assign to gravity well based on highest score"""
        max_category = max(scores.items(), key=lambda x: x[1])
        return max_category[0]  # work, play, or create


class Copy1Entity(NaniCommandEntity):
    """
    Copy1 Entity - First-pass duplicate manager

    Workflow:
    1. Scan source (trash/today folder)
    2. Compute file hashes
    3. Identify first instance (origin) vs duplicates (shadows)
    4. Move origin to active_content
    5. Convert duplicates to shadow tokens
    6. Assign shadows to gravity wells (work/play/create)
    7. Attach shadow tokens to origin metadata
    """

    def __init__(self, active_content_dir: str = "/home/sauron/Q/active_content",
                 shadow_registry: str = "/home/sauron/Q/shadow_registry.json"):
        super().__init__("copy1")
        self.active_content = Path(active_content_dir)
        self.active_content.mkdir(parents=True, exist_ok=True)

        self.shadow_registry_path = Path(shadow_registry)
        self.shadow_registry = self._load_shadow_registry()

        self.rubric = WorkPlayCreateRubric()

        # Hash cache for performance
        self.hash_cache = {}

    def _load_shadow_registry(self) -> Dict:
        """Load shadow token registry"""
        if self.shadow_registry_path.exists():
            with open(self.shadow_registry_path, 'r') as f:
                return json.load(f)
        return {"origins": {}, "shadows": {}}

    def _save_shadow_registry(self):
        """Save shadow token registry"""
        with open(self.shadow_registry_path, 'w') as f:
            json.dump(self.shadow_registry, f, indent=2)

    def compute_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file"""
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]

        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    sha256.update(chunk)
            file_hash = sha256.hexdigest()
            self.hash_cache[file_path] = file_hash
            return file_hash
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
            return None

    def _execute(self) -> Dict[str, Any]:
        """Execute copy1 rescue operation"""
        source_dir = self.context.get('inputs', {}).get('source_dir')
        visionary_mode = self.context.get('inputs', {}).get('visionary_mode', False)

        if not source_dir or not os.path.exists(source_dir):
            return {"status": "error", "reason": "source_dir not found", "path": source_dir}

        # Scan all files
        all_files = []
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                all_files.append(os.path.join(root, file))

        # Group by hash
        hash_groups = {}
        for file_path in all_files:
            file_hash = self.compute_hash(file_path)
            if file_hash:
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_path)

        # Process each group
        results = {
            'origins_moved': 0,
            'shadows_created': 0,
            'duplicates_found': 0,
            'gravity_wells': {'work': 0, 'play': 0, 'create': 0}
        }

        for file_hash, paths in hash_groups.items():
            if len(paths) == 1:
                # Unique file, just move to active
                self._move_to_active(paths[0], file_hash, visionary_mode)
                results['origins_moved'] += 1
            else:
                # Duplicates found!
                origin = paths[0]  # First instance is origin
                shadows = paths[1:]  # Rest are shadows

                results['duplicates_found'] += len(shadows)

                # Move origin to active
                origin_path = self._move_to_active(origin, file_hash, visionary_mode)
                results['origins_moved'] += 1

                # Create shadow tokens for duplicates
                for shadow_path in shadows:
                    shadow_token = self._create_shadow_token(
                        origin_path, shadow_path, file_hash, visionary_mode
                    )
                    results['shadows_created'] += 1
                    results['gravity_wells'][shadow_token.gravity_well] += 1

        self._save_shadow_registry()

        return {
            "status": "success",
            "command": "copy1",
            "results": results
        }

    def _move_to_active(self, file_path: str, file_hash: str, visionary_mode: bool) -> str:
        """Move file to active content directory"""
        filename = Path(file_path).name
        dest_path = self.active_content / filename

        # Handle name collisions
        counter = 1
        while dest_path.exists():
            stem = Path(file_path).stem
            ext = Path(file_path).suffix
            dest_path = self.active_content / f"{stem}_{counter}{ext}"
            counter += 1

        # Move or copy based on mode
        import shutil
        if visionary_mode:
            # Visionary mode: copy (preserve original)
            shutil.copy2(file_path, dest_path)
        else:
            # Normal mode: move (remove original)
            shutil.move(file_path, dest_path)

        # Register as origin
        self.shadow_registry["origins"][file_hash] = {
            "path": str(dest_path),
            "original_path": file_path,
            "created": datetime.now().isoformat(),
            "shadows": []
        }

        return str(dest_path)

    def _create_shadow_token(self, origin_path: str, shadow_path: str,
                            file_hash: str, visionary_mode: bool) -> ShadowToken:
        """Create shadow token for duplicate file"""
        # Score content
        scores = self.rubric.score_content(shadow_path)
        gravity_well = self.rubric.assign_gravity_well(scores)

        # Create shadow token
        shadow_id = f"shadow_{file_hash}_{len(self.shadow_registry['origins'][file_hash]['shadows'])}"

        shadow = ShadowToken(
            original_path=shadow_path,
            shadow_id=shadow_id,
            created=datetime.now().isoformat(),
            file_hash=file_hash,
            size=os.path.getsize(shadow_path),
            gravity_well=gravity_well,
            rubric_scores=scores,
            metadata={
                'origin': origin_path,
                'visionary_mode': visionary_mode
            }
        )

        # Add to registry
        self.shadow_registry["origins"][file_hash]["shadows"].append({
            "id": shadow.shadow_id,
            "path": shadow.original_path,
            "gravity_well": shadow.gravity_well,
            "scores": shadow.rubric_scores,
            "created": shadow.created,
            "size": shadow.size
        })

        self.shadow_registry["shadows"][shadow_id] = {
            "origin_hash": file_hash,
            "origin_path": origin_path,
            "shadow_path": shadow_path,
            "gravity_well": gravity_well,
            "scores": scores,
            "created": shadow.created
        }

        # Delete duplicate file (shadow is now token only)
        if not visionary_mode:
            os.remove(shadow_path)

        return shadow

    def solo_capabilities(self) -> list:
        return ["identify_duplicates", "create_shadows", "move_origins", "score_content"]

    def system_capabilities(self) -> list:
        return [
            "coordinate_with_copy2",
            "feed_gravity_wells",
            "track_economies",
            "maintain_shadow_registry"
        ]


# Visionary Mode Functions
class VisionaryMode:
    """
    Visionary/Sysop mode for rescue system
    Like BBS sysop - full access, override capabilities
    """

    def __init__(self, user: str = "suxen"):
        self.user = user
        self.is_active = False
        self.command_history = []

    def activate(self, passphrase: str) -> bool:
        """Activate visionary mode (requires passphrase)"""
        # In production, use proper auth
        if passphrase == "enjoy_the_journey":
            self.is_active = True
            print(f"🔮 VISIONARY MODE ACTIVATED for {self.user} 🔮")
            return True
        return False

    def deactivate(self):
        """Deactivate visionary mode"""
        self.is_active = False
        print(f"🔮 Visionary mode deactivated")

    def execute_with_authority(self, command: str, *args, **kwargs):
        """Execute command with sysop authority"""
        if not self.is_active:
            raise PermissionError("Visionary mode not active")

        self.command_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'args': args,
            'kwargs': kwargs
        })

        # Execute with full permissions
        print(f"🔮 VISIONARY: {command}")
        # Command execution here
        return {"status": "executed", "authority": "visionary"}


# CLI Interface
if __name__ == "__main__":
    print("∰◊€π¿🌌∞ Copy1 Entity - Duplicate Manager with Shadow Tokens ∰◊€π¿🌌∞\n")

    # Test rubric
    print("Testing Work/Play/Create Rubric...")
    rubric = WorkPlayCreateRubric()

    test_files = {
        "project_plan.docx": "This is a project plan with tasks and deadlines",
        "experiment_notes.txt": "Experimental ideas to explore and test",
        "story_draft.md": "Creative writing and narrative design"
    }

    for filename, content in test_files.items():
        scores = rubric.score_content(filename, content)
        well = rubric.assign_gravity_well(scores)
        print(f"\n{filename}:")
        print(f"  Scores: work={scores['work']:.2f}, play={scores['play']:.2f}, create={scores['create']:.2f}")
        print(f"  → Gravity Well: {well}")

    # Test visionary mode
    print("\n\nTesting Visionary Mode...")
    vm = VisionaryMode()
    vm.activate("enjoy_the_journey")
    vm.execute_with_authority("rescue_all", source="/test")
    vm.deactivate()

    print("\n\n🤖 Copy1 Entity ready!")
    print("   Shadow tokens: Convert duplicates to lightweight references")
    print("   Gravity wells: work/play/create assignment")
    print("   Visionary mode: Sysop authority for rescue operations")
    print("   ∰◊€π¿🌌∞")
