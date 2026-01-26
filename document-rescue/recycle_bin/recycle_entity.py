#!/usr/bin/env python3
"""
Recycle Bin Meta-Entity - Document Rescue Coordinator
Orchestrates nani command entities for trash → recycle → legacy workflow
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'nani_engine'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'command_entities'))

from decision_engine import NaniDecisionEngine, DecisionContext, DecisionState, quick_execute
from command_suite import *


class RecycleEconomy:
    """
    Economy system for recycle deposits
    Entities earn credits for transferring ownership to consortium
    """

    def __init__(self, ledger_path: str = "recycle_ledger.json"):
        self.ledger_path = ledger_path
        self.ledger = self._load_ledger()

    def _load_ledger(self) -> Dict:
        if os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'r') as f:
                return json.load(f)
        return {"entities": {}, "transactions": []}

    def _save_ledger(self):
        with open(self.ledger_path, 'w') as f:
            json.dump(self.ledger, f, indent=2)

    def credit_depositor(self, entity_name: str, item_path: str, item_type: str) -> int:
        """
        Credit entity for deposit
        Returns credit amount
        """
        # Credit calculation based on item type and size
        credits = {
            "document": 10,
            "code": 15,
            "data": 5,
            "media": 20,
            "archive": 25
        }.get(item_type, 10)

        # Bonus for large items
        try:
            size = os.path.getsize(item_path)
            if size > 1_000_000:  # 1MB+
                credits += 5
            if size > 10_000_000:  # 10MB+
                credits += 10
        except:
            pass

        # Update ledger
        if entity_name not in self.ledger["entities"]:
            self.ledger["entities"][entity_name] = 0

        self.ledger["entities"][entity_name] += credits

        # Record transaction
        self.ledger["transactions"].append({
            "timestamp": datetime.now().isoformat(),
            "entity": entity_name,
            "item": item_path,
            "type": item_type,
            "credits": credits
        })

        self._save_ledger()
        return credits

    def get_balance(self, entity_name: str) -> int:
        return self.ledger["entities"].get(entity_name, 0)

    def get_top_contributors(self, limit: int = 10) -> List[tuple]:
        """Return top contributors by credits"""
        items = sorted(self.ledger["entities"].items(), key=lambda x: x[1], reverse=True)
        return items[:limit]


class LegacyManager:
    """
    Manages document versioning to Legacy folders
    Uses shortcuts (symlinks locally, shortcut files on Google Drive)
    """

    def __init__(self, legacy_root: str = "legacy"):
        self.legacy_root = Path(legacy_root)
        self.legacy_root.mkdir(parents=True, exist_ok=True)

    def create_legacy_entry(self, original_path: str, version: str = None) -> str:
        """
        Create legacy entry for document
        Returns path to legacy location
        """
        original = Path(original_path)

        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Legacy path structure: legacy/{category}/{basename}_{version}{ext}
        category = self._categorize(original)
        legacy_dir = self.legacy_root / category
        legacy_dir.mkdir(parents=True, exist_ok=True)

        # Build legacy filename
        stem = original.stem
        ext = original.suffix
        legacy_name = f"{stem}_{version}{ext}"
        legacy_path = legacy_dir / legacy_name

        # Copy to legacy
        import shutil
        shutil.copy2(str(original), str(legacy_path))

        return str(legacy_path)

    def create_shortcut(self, target_path: str, shortcut_location: str) -> str:
        """
        Create shortcut (symlink locally)
        For Google Drive, would create .gdshortcut file
        """
        shortcut_path = Path(shortcut_location)

        if os.name == 'nt':  # Windows
            # Create .lnk file
            # Would need pywin32
            pass
        else:  # Unix
            if not shortcut_path.exists():
                os.symlink(target_path, str(shortcut_path))

        return str(shortcut_path)

    def _categorize(self, path: Path) -> str:
        """Categorize file for legacy organization"""
        ext = path.suffix.lower()

        categories = {
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.md', '.odt'],
            'code': ['.py', '.js', '.sh', '.json', '.yaml', '.toml'],
            'data': ['.csv', '.xlsx', '.db', '.sql'],
            'media': ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3'],
            'archives': ['.zip', '.tar', '.gz', '.7z']
        }

        for category, extensions in categories.items():
            if ext in extensions:
                return category

        return 'other'


class RecycleBinEntity:
    """
    Recycle Bin Meta-Entity
    Coordinates nani command entities for document rescue
    """

    def __init__(self, recycle_dir: str = "recycle_bin", legacy_dir: str = "legacy"):
        self.recycle_dir = Path(recycle_dir)
        self.recycle_dir.mkdir(parents=True, exist_ok=True)

        self.engine = NaniDecisionEngine("recycle_bin", mode="pattern")
        self.economy = RecycleEconomy(str(self.recycle_dir / "ledger.json"))
        self.legacy = LegacyManager(legacy_dir)

        # Entity queue for processing
        self.queue = []

    def accept_deposit(self, item_path: str, depositor: str) -> Dict[str, Any]:
        """
        Accept item into recycle bin
        Returns deposit receipt
        """
        # Decision: Should we accept this deposit?
        ctx = DecisionContext(
            operation="accept_deposit",
            inputs={'path': item_path, 'depositor': depositor}
        )

        decision = self.engine.decide(ctx)

        if decision == DecisionState.NO:
            return {
                "status": "declined",
                "reason": "decision_engine_declined",
                "item": item_path
            }

        # Move to recycle bin
        item = Path(item_path)
        recycle_path = self.recycle_dir / item.name

        # Use mv entity
        result = quick_execute(MvEntity, {
            'inputs': {'src': str(item), 'dst': str(recycle_path)}
        })

        if result['status'] != 'success':
            return result

        # Credit depositor
        item_type = self.legacy._categorize(item)
        credits = self.economy.credit_depositor(depositor, str(recycle_path), item_type)

        # Add to processing queue
        self.queue.append({
            'path': str(recycle_path),
            'depositor': depositor,
            'type': item_type,
            'timestamp': datetime.now().isoformat()
        })

        return {
            "status": "accepted",
            "item": item_path,
            "recycle_location": str(recycle_path),
            "credits_earned": credits,
            "queue_position": len(self.queue)
        }

    def rescue_document(self, item_path: str) -> Dict[str, Any]:
        """
        Rescue document from recycle to legacy
        Full document rescue workflow
        """
        item = Path(item_path)

        if not item.exists():
            return {"status": "error", "reason": "item_not_found", "path": item_path}

        # 1. Inspect item with stat entity
        stat_result = quick_execute(StatEntity, {'inputs': {'path': str(item)}})

        if stat_result['status'] != 'success':
            return stat_result

        # 2. Analyze content (if text-based)
        wc_result = None
        if item.suffix.lower() in ['.txt', '.md', '.py', '.sh', '.json']:
            wc_result = quick_execute(WcEntity, {'inputs': {'path': str(item)}})

        # 3. Create legacy entry
        legacy_path = self.legacy.create_legacy_entry(str(item))

        # 4. Transfer ownership (represented by move to legacy)
        # Item stays in recycle, legacy is the archive

        return {
            "status": "rescued",
            "item": item_path,
            "legacy_location": legacy_path,
            "metadata": {
                "size": stat_result.get('size'),
                "modified": stat_result.get('modified'),
                "lines": wc_result.get('lines') if wc_result else None
            }
        }

    def scan_for_rescue(self, pattern: str = "*") -> List[str]:
        """
        Scan recycle bin for items matching pattern
        Uses find entity
        """
        result = quick_execute(FindEntity, {
            'inputs': {'path': str(self.recycle_dir), 'pattern': pattern, 'type': 'f'}
        })

        if result['status'] == 'success':
            return result.get('items', [])

        return []

    def process_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Process items in queue
        Batch rescue operation
        """
        results = []

        for item_data in self.queue[:limit]:
            result = self.rescue_document(item_data['path'])
            result['depositor'] = item_data['depositor']
            results.append(result)

        # Clear processed items
        self.queue = self.queue[limit:]

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get recycle bin statistics"""
        # Count items in recycle
        items_result = quick_execute(FindEntity, {
            'inputs': {'path': str(self.recycle_dir), 'pattern': '*', 'type': 'f'}
        })

        item_count = items_result.get('count', 0) if items_result['status'] == 'success' else 0

        return {
            "recycle_items": item_count,
            "queue_length": len(self.queue),
            "total_credits_distributed": sum(self.economy.ledger["entities"].values()),
            "top_contributors": self.economy.get_top_contributors(5),
            "total_transactions": len(self.economy.ledger["transactions"])
        }


# ======================
# GOOGLE DRIVE TRASH CRAWLER
# ======================

class GDriveTrashCrawler:
    """
    Crawls Google Drive trash
    In-place processing using shortcuts
    """

    def __init__(self, recycle_bin: RecycleBinEntity):
        self.recycle_bin = recycle_bin
        self.processed = []

    def crawl_trash(self, trash_location: str) -> Dict[str, Any]:
        """
        Crawl Google Drive trash
        Returns list of items ready for rescue
        """
        # Would use rclone or google-api-python-client
        # For now, simulate with local find

        import subprocess
        try:
            result = subprocess.run(
                ['rclone', 'lsf', f'{trash_location}', '--recursive'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                items = result.stdout.strip().split('\n')
                return {
                    "status": "success",
                    "location": trash_location,
                    "items": items,
                    "count": len(items)
                }
        except Exception as e:
            pass

        return {"status": "error", "reason": "crawl_failed"}

    def deploy_rescue(self, trash_item: str, depositor: str = "gdrive_crawler") -> Dict[str, Any]:
        """
        Deploy rescue for trash item
        Move to recycle bin, create shortcut in original location
        """
        # This would:
        # 1. Copy from Google Drive trash to local recycle
        # 2. Create shortcut in entity queue on Google Drive
        # 3. Transfer ownership metadata

        return {
            "status": "rescue_deployed",
            "item": trash_item,
            "method": "shortcut_based",
            "ownership": "transferred_to_consortium"
        }


# ======================
# CLI Interface
# ======================

if __name__ == "__main__":
    print("∰◊€π¿🌌∞ Recycle Bin Entity - Document Rescue System ∰◊€π¿🌌∞\n")

    # Initialize recycle bin
    recycle = RecycleBinEntity(
        recycle_dir="/home/sauron/Q/recycle_bin",
        legacy_dir="/home/sauron/Q/legacy"
    )

    print("Recycle Bin Entity initialized")
    print(f"  Location: {recycle.recycle_dir}")
    print(f"  Legacy: {recycle.legacy.legacy_root}\n")

    # Show stats
    stats = recycle.get_stats()
    print("Current Stats:")
    print(f"  Items in recycle: {stats['recycle_items']}")
    print(f"  Queue length: {stats['queue_length']}")
    print(f"  Total credits: {stats['total_credits_distributed']}")
    print(f"  Transactions: {stats['total_transactions']}\n")

    if stats['top_contributors']:
        print("Top Contributors:")
        for entity, credits in stats['top_contributors']:
            print(f"  {entity}: {credits} credits")
        print()

    print("🤖 Recycle Bin Entity ready for document rescue!")
    print("   Load → Do → Unload. No bog down. ∰◊€π¿🌌∞")
