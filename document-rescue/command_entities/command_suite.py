#!/usr/bin/env python3
"""
Command Entity Suite - DOS + Unix commands as autonomous nani entities
Each command knows what it can do solo and with the system
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'nani_engine'))
from decision_engine import NaniCommandEntity, quick_execute


# ======================
# FILE SYSTEM ENTITIES
# ======================

class CdEntity(NaniCommandEntity):
    """cd - Change directory"""

    def __init__(self):
        super().__init__("cd")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path', '~')
        try:
            os.chdir(os.path.expanduser(path))
            return {
                "status": "success",
                "command": "cd",
                "new_directory": os.getcwd()
            }
        except Exception as e:
            return {"status": "error", "command": "cd", "error": str(e)}

    def solo_capabilities(self):
        return ["change_directory", "navigate_filesystem"]

    def system_capabilities(self):
        return ["set_context_for_pwd", "prepare_for_ls", "position_for_operations"]


class MkdirEntity(NaniCommandEntity):
    """mkdir - Make directory"""

    def __init__(self):
        super().__init__("mkdir")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path')
        parents = self.context.get('inputs', {}).get('parents', False)

        try:
            if parents:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)

            return {"status": "success", "command": "mkdir", "path": path}
        except Exception as e:
            return {"status": "error", "command": "mkdir", "error": str(e)}

    def solo_capabilities(self):
        return ["create_directory", "create_directory_tree"]

    def system_capabilities(self):
        return ["prepare_structure_for_cp", "organize_for_find", "scaffold_projects"]


class CpEntity(NaniCommandEntity):
    """cp - Copy files/directories"""

    def __init__(self):
        super().__init__("cp")

    def _execute(self):
        src = self.context.get('inputs', {}).get('src')
        dst = self.context.get('inputs', {}).get('dst')
        recursive = self.context.get('inputs', {}).get('recursive', False)

        try:
            if recursive and os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

            return {"status": "success", "command": "cp", "src": src, "dst": dst}
        except Exception as e:
            return {"status": "error", "command": "cp", "error": str(e)}

    def solo_capabilities(self):
        return ["copy_file", "copy_directory", "preserve_metadata"]

    def system_capabilities(self):
        return ["rescue_to_legacy", "backup_for_mv", "duplicate_for_versioning", "stage_for_processing"]


class MvEntity(NaniCommandEntity):
    """mv - Move/rename files"""

    def __init__(self):
        super().__init__("mv")

    def _execute(self):
        src = self.context.get('inputs', {}).get('src')
        dst = self.context.get('inputs', {}).get('dst')

        try:
            shutil.move(src, dst)
            return {"status": "success", "command": "mv", "src": src, "dst": dst}
        except Exception as e:
            return {"status": "error", "command": "mv", "error": str(e)}

    def solo_capabilities(self):
        return ["move_file", "rename_file", "relocate_directory"]

    def system_capabilities(self):
        return ["transfer_ownership", "organize_for_recycle", "stage_for_archive", "queue_for_processing"]


class RmEntity(NaniCommandEntity):
    """rm - Remove files (DANGER: Use with caution)"""

    def __init__(self):
        super().__init__("rm")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path')
        recursive = self.context.get('inputs', {}).get('recursive', False)
        force = self.context.get('inputs', {}).get('force', False)

        # Safety check - never force delete without explicit confirmation
        if not self.context.get('inputs', {}).get('confirmed', False):
            return {
                "status": "declined",
                "command": "rm",
                "reason": "requires_confirmation",
                "path": path
            }

        try:
            if recursive and os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

            return {"status": "success", "command": "rm", "path": path}
        except Exception as e:
            return {"status": "error", "command": "rm", "error": str(e)}

    def solo_capabilities(self):
        return ["remove_file", "remove_directory_tree"]

    def system_capabilities(self):
        return ["cleanup_after_mv", "purge_temp_files", "finalize_recycle"]


# ======================
# INSPECTION ENTITIES
# ======================

class CatEntity(NaniCommandEntity):
    """cat - Concatenate and display files"""

    def __init__(self):
        super().__init__("cat")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path')
        limit = self.context.get('inputs', {}).get('limit', None)

        try:
            with open(path, 'r') as f:
                content = f.read(limit) if limit else f.read()

            return {
                "status": "success",
                "command": "cat",
                "path": path,
                "content": content,
                "truncated": limit is not None
            }
        except Exception as e:
            return {"status": "error", "command": "cat", "error": str(e)}

    def solo_capabilities(self):
        return ["display_content", "read_file", "stream_data"]

    def system_capabilities(self):
        return ["feed_grep", "provide_to_diff", "extract_for_analysis", "preview_for_rescue"]


class GrepEntity(NaniCommandEntity):
    """grep - Search file contents"""

    def __init__(self):
        super().__init__("grep")

    def _execute(self):
        pattern = self.context.get('inputs', {}).get('pattern')
        path = self.context.get('inputs', {}).get('path')
        recursive = self.context.get('inputs', {}).get('recursive', False)

        try:
            if recursive:
                # Use ripgrep if available, else grep
                result = subprocess.run(
                    ['rg', pattern, path] if shutil.which('rg') else ['grep', '-r', pattern, path],
                    capture_output=True, text=True
                )
            else:
                result = subprocess.run(
                    ['grep', pattern, path],
                    capture_output=True, text=True
                )

            matches = result.stdout.strip().split('\n') if result.stdout else []

            return {
                "status": "success",
                "command": "grep",
                "pattern": pattern,
                "path": path,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"status": "error", "command": "grep", "error": str(e)}

    def solo_capabilities(self):
        return ["search_content", "filter_lines", "pattern_match"]

    def system_capabilities(self):
        return ["filter_for_find", "scan_for_rescue", "validate_for_cp", "identify_for_legacy"]


class FindEntity(NaniCommandEntity):
    """find - Search for files"""

    def __init__(self):
        super().__init__("find")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path', '.')
        pattern = self.context.get('inputs', {}).get('pattern', '*')
        file_type = self.context.get('inputs', {}).get('type', None)  # 'f' or 'd'

        try:
            cmd = ['find', path, '-name', pattern]
            if file_type:
                cmd.extend(['-type', file_type])

            result = subprocess.run(cmd, capture_output=True, text=True)
            items = result.stdout.strip().split('\n') if result.stdout else []

            return {
                "status": "success",
                "command": "find",
                "path": path,
                "pattern": pattern,
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"status": "error", "command": "find", "error": str(e)}

    def solo_capabilities(self):
        return ["locate_files", "search_directory_tree", "filter_by_type"]

    def system_capabilities(self):
        return ["feed_ls_results", "provide_to_grep", "scan_for_rescue", "inventory_for_recycle"]


class WcEntity(NaniCommandEntity):
    """wc - Word count (lines, words, chars)"""

    def __init__(self):
        super().__init__("wc")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path')

        try:
            with open(path, 'r') as f:
                content = f.read()

            lines = len(content.split('\n'))
            words = len(content.split())
            chars = len(content)

            return {
                "status": "success",
                "command": "wc",
                "path": path,
                "lines": lines,
                "words": words,
                "chars": chars
            }
        except Exception as e:
            return {"status": "error", "command": "wc", "error": str(e)}

    def solo_capabilities(self):
        return ["count_lines", "count_words", "measure_size"]

    def system_capabilities(self):
        return ["size_for_cp", "metrics_for_rescue", "validate_for_processing"]


class StatEntity(NaniCommandEntity):
    """stat - Get file metadata"""

    def __init__(self):
        super().__init__("stat")

    def _execute(self):
        path = self.context.get('inputs', {}).get('path')

        try:
            stat_info = os.stat(path)

            return {
                "status": "success",
                "command": "stat",
                "path": path,
                "size": stat_info.st_size,
                "modified": stat_info.st_mtime,
                "accessed": stat_info.st_atime,
                "created": stat_info.st_ctime,
                "mode": oct(stat_info.st_mode)
            }
        except Exception as e:
            return {"status": "error", "command": "stat", "error": str(e)}

    def solo_capabilities(self):
        return ["get_metadata", "check_timestamps", "measure_size"]

    def system_capabilities(self):
        return ["validate_for_rescue", "track_for_versioning", "audit_for_legacy"]


# ======================
# UTILITY REGISTRY
# ======================

COMMAND_REGISTRY = {
    # File operations
    'cd': CdEntity,
    'mkdir': MkdirEntity,
    'cp': CpEntity,
    'mv': MvEntity,
    'rm': RmEntity,
    'ls': None,  # Defined in decision_engine.py
    'pwd': None,  # Defined in decision_engine.py

    # Inspection
    'cat': CatEntity,
    'grep': GrepEntity,
    'find': FindEntity,
    'wc': WcEntity,
    'stat': StatEntity,
}


def get_entity(command_name: str):
    """Get entity class for command"""
    entity_class = COMMAND_REGISTRY.get(command_name)
    if entity_class is None:
        raise ValueError(f"Unknown command: {command_name}")
    return entity_class


if __name__ == "__main__":
    print("∰◊€π¿🌌∞ Command Entity Suite Test ∰◊€π¿🌌∞\n")

    # Test various entities
    tests = [
        ('pwd', {}),
        ('ls', {'inputs': {'path': '.'}}),
        ('cat', {'inputs': {'path': __file__, 'limit': 100}}),
        ('wc', {'inputs': {'path': __file__}}),
        ('stat', {'inputs': {'path': __file__}}),
    ]

    for cmd, ctx in tests:
        print(f"Testing {cmd.upper()}...")
        try:
            if cmd == 'pwd':
                from decision_engine import PwdEntity
                result = quick_execute(PwdEntity, ctx)
            elif cmd == 'ls':
                from decision_engine import LsEntity
                result = quick_execute(LsEntity, ctx)
            else:
                result = quick_execute(get_entity(cmd), ctx)

            print(f"  ✓ {result.get('status', 'unknown')}")
            if 'result' in result:
                print(f"    {result['result']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

    print("🤖 Command entity suite ready!")
