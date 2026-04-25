"""
Project Code Export Script
Scans the project directory structure, extracts valid code files,
and exports them to a well-organized TXT file.
"""

import os
import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = Path(__file__).resolve().parent / "project_export.txt"

EXCLUDED_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "ENV",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "htmlcov",
    "build",
    "dist",
    ".eggs",
    ".runtime_data",
    "pip-wheel-metadata",
    "test",
    "tests",
}

EXCLUDED_FILE_PATTERNS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".egg-info",
    ".tmp",
    ".log",
    ".dat",
    ".DS_Store",
    "Thumbs.db",
    ".env",
    ".gitignore",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".db", ".sqlite", ".sqlite3",
    ".pyc", ".pyo",
    ".whl", ".egg",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".ttf", ".otf", ".woff", ".woff2",
    ".eot",
}

CODE_EXTENSIONS = {
    ".py",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".txt",
    ".cfg",
    ".ini",
    ".sh",
    ".bat",
    ".css",
    ".js",
    ".ts",
    ".html",
    ".xml",
    ".csv",
    ".rst",
}

INCLUDE_NO_EXTENSION = {
    "Makefile",
    "Dockerfile",
    "LICENSE",
    "MANIFEST.in",
}

GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"


# ============================================================
# .gitignore Parsing
# ============================================================

def parse_gitignore(gitignore_path):
    """Parse .gitignore file and return a set of directory/file names to exclude."""
    ignored = set()
    if not gitignore_path.exists():
        return ignored

    with open(gitignore_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("*."):
                ignored.add(line)
                continue

            if "*" in line or "?" in line or "[" in line:
                continue

            clean = line.rstrip("/")

            if "/" in clean:
                first_component = clean.split("/")[0]
                if first_component in ("src", "lib", "app", "core"):
                    continue
                ignored.add(first_component)
            else:
                ignored.add(clean)

    return ignored


# ============================================================
# File Classification
# ============================================================

def get_file_category(filepath, project_root):
    """Classify a file into a category based on its path and extension."""
    rel_path = filepath.relative_to(project_root)
    parts = rel_path.parts

    if len(parts) >= 2:
        top_dir = parts[0]
        sub_dir = parts[1] if len(parts) >= 3 else ""

        if top_dir == "src":
            category_map = {
                "agent": "src.agent",
                "context": "src.context",
                "control": "src.control",
                "llm": "src.llm",
                "runtime": "src.runtime",
                "schemas": "src.schemas",
                "shared": "src.shared",
                "skill": "src.skill",
                "storage": "src.storage",
                "tool": "src.tool",
            }
            if sub_dir in category_map:
                return category_map[sub_dir]
            elif top_dir in category_map:
                return category_map[top_dir]

    return str(rel_path.parent) if len(parts) > 1 else "root"


def get_extension_group(ext):
    """Group file extensions into broader categories."""
    if ext == ".py":
        return "Python Source"
    elif ext in (".md", ".rst", ".txt"):
        return "Documentation"
    elif ext in (".toml", ".yaml", ".yml", ".json", ".cfg", ".ini"):
        return "Configuration"
    elif ext in (".sh", ".bat"):
        return "Scripts"
    elif ext in (".css", ".js", ".ts", ".html", ".xml"):
        return "Web Assets"
    elif ext == ".csv":
        return "Data"
    else:
        return "Other"


# ============================================================
# File Scanning
# ============================================================

def should_exclude_dir(dirname, gitignore_ignored):
    """Check if a directory should be excluded."""
    if dirname in EXCLUDED_DIRS:
        return True
    if dirname.lower() in {"test", "tests"}:
        return True
    if dirname in gitignore_ignored:
        return True
    return False


def should_exclude_file(filename, filepath, gitignore_ignored):
    """Check if a file should be excluded."""
    if filename in EXCLUDED_FILE_PATTERNS:
        return True
    if filename in gitignore_ignored:
        return True

    ext = Path(filename).suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return True
    if ext in EXCLUDED_FILE_PATTERNS:
        return True

    if ext not in CODE_EXTENSIONS and filename not in INCLUDE_NO_EXTENSION:
        return True

    return False


def is_text_file(filepath):
    """Check if a file is a text file by trying to read it."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(8192)
        return True
    except (UnicodeDecodeError, PermissionError, OSError):
        return False


def scan_project(project_root, gitignore_ignored):
    """Scan the project and return a list of valid code files organized by category."""
    files_by_category = {}

    for dirpath, dirnames, filenames in os.walk(project_root):
        current_dir = Path(dirpath)

        dirnames[:] = [
            d for d in dirnames
            if not should_exclude_dir(d, gitignore_ignored)
            and not (current_dir / d).is_symlink()
        ]

        for filename in sorted(filenames):
            filepath = current_dir / filename

            if should_exclude_file(filename, filepath, gitignore_ignored):
                continue

            if not is_text_file(filepath):
                continue

            category = get_file_category(filepath, project_root)
            if category not in files_by_category:
                files_by_category[category] = []

            files_by_category[category].append(filepath)

    return files_by_category


# ============================================================
# TXT Export
# ============================================================

def build_directory_tree(project_root, gitignore_ignored):
    """Build a text representation of the project directory tree."""
    lines = []

    def _build_tree(dirpath, prefix=""):
        current = Path(dirpath)
        try:
            entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        filtered = []
        for entry in entries:
            if entry.is_dir():
                if not should_exclude_dir(entry.name, gitignore_ignored):
                    filtered.append(entry)
            else:
                if not should_exclude_file(entry.name, entry, gitignore_ignored):
                    filtered.append(entry)

        for i, entry in enumerate(filtered):
            is_last = (i == len(filtered) - 1)
            connector = "`-- " if is_last else "|-- "
            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "|   "
                _build_tree(entry, prefix + extension)

    _build_tree(project_root)
    return lines


def read_file_content(filepath):
    """Read file content safely."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, PermissionError, OSError):
        return "[Error: Unable to read file content]"


def export_to_txt(files_by_category, project_root, output_file):
    """Export all collected files to a single TXT file."""
    gitignore_ignored = parse_gitignore(GITIGNORE_PATH)
    dir_tree = build_directory_tree(project_root, gitignore_ignored)

    separator = "=" * 80
    thin_sep = "-" * 80

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"{separator}\n")
        out.write(f"  PROJECT CODE EXPORT\n")
        out.write(f"  Project: {project_root.name}\n")
        out.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"  Root Path: {project_root}\n")
        out.write(f"{separator}\n\n")

        out.write(f"{separator}\n")
        out.write(f"  TABLE OF CONTENTS\n")
        out.write(f"{separator}\n\n")

        total_files = 0
        for category in sorted(files_by_category.keys()):
            file_list = files_by_category[category]
            total_files += len(file_list)
            out.write(f"  [{category}]\n")
            out.write(f"    Files: {len(file_list)}\n")
            for fp in file_list:
                rel = fp.relative_to(project_root)
                out.write(f"      - {rel}\n")
            out.write("\n")

        out.write(f"  Total files: {total_files}\n\n")

        out.write(f"{separator}\n")
        out.write(f"  DIRECTORY STRUCTURE\n")
        out.write(f"{separator}\n\n")
        out.write(f"  {project_root.name}/\n")
        for line in dir_tree:
            out.write(f"  {line}\n")
        out.write(f"\n")

        out.write(f"{separator}\n")
        out.write(f"  CODE CONTENT\n")
        out.write(f"{separator}\n\n")

        for category in sorted(files_by_category.keys()):
            file_list = files_by_category[category]
            ext_group = get_extension_group(Path(file_list[0]).suffix)

            out.write(f"{thin_sep}\n")
            out.write(f"  MODULE: {category}\n")
            out.write(f"  TYPE: {ext_group}\n")
            out.write(f"  FILES: {len(file_list)}\n")
            out.write(f"{thin_sep}\n\n")

            for filepath in file_list:
                rel_path = filepath.relative_to(project_root)
                content = read_file_content(filepath)

                out.write(f"  {'#' * 60}\n")
                out.write(f"  # FILE: {rel_path}\n")
                out.write(f"  {'#' * 60}\n\n")

                out.write(content)

                if content and not content.endswith("\n"):
                    out.write("\n")

                out.write(f"\n\n")

        out.write(f"{separator}\n")
        out.write(f"  END OF EXPORT\n")
        out.write(f"  Total files included: {total_files}\n")
        out.write(f"{separator}\n")

    return total_files


# ============================================================
# Main
# ============================================================

def main():
    """Main entry point."""
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Output File: {OUTPUT_FILE}")
    print()

    if not PROJECT_ROOT.exists():
        print(f"ERROR: Project root does not exist: {PROJECT_ROOT}")
        sys.exit(1)

    gitignore_ignored = parse_gitignore(GITIGNORE_PATH)
    print(f"Parsed .gitignore: {len(gitignore_ignored)} patterns loaded")

    print("Scanning project files...")
    files_by_category = scan_project(PROJECT_ROOT, gitignore_ignored)

    total = sum(len(v) for v in files_by_category.values())
    print(f"Found {total} valid code files in {len(files_by_category)} categories")

    for category in sorted(files_by_category.keys()):
        print(f"  {category}: {len(files_by_category[category])} files")

    print(f"\nExporting to: {OUTPUT_FILE}")
    total_exported = export_to_txt(files_by_category, PROJECT_ROOT, OUTPUT_FILE)
    print(f"Export complete! {total_exported} files written to TXT.")
    print(f"Output size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
