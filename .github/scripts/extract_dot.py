#!/usr/bin/env python3
"""Extract DOT code blocks from a markdown file and render them as SVGs."""

import re
import subprocess
import sys
from pathlib import Path

def extract_dot_blocks(md_text):
    """Yield (name, dot_source) for every fenced block containing a digraph."""
    # Match fenced code blocks (``` ... ```) with optional language tag
    fence_re = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
    name_re = re.compile(r"digraph\s+(\w+)\s*\{")
    seen = {}
    for match in fence_re.finditer(md_text):
        block = match.group(1)
        m = name_re.search(block)
        if not m:
            continue
        name = m.group(1)
        # Deduplicate: if same name appears multiple times, suffix with counter
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        yield name, block.strip()


def render(name, dot_source, output_dir):
    dot_path = output_dir / f"{name}.dot"
    svg_path = output_dir / f"{name}.svg"
    dot_path.write_text(dot_source)
    result = subprocess.run(
        ["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR rendering {name}:\n{result.stderr}", file=sys.stderr)
        return False
    dot_path.unlink()
    print(f"  rendered {svg_path}")
    return True


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <markdown_file> <output_dir>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    md_text = md_path.read_text()
    blocks = list(extract_dot_blocks(md_text))
    if not blocks:
        print("No DOT diagrams found.")
        sys.exit(0)

    errors = 0
    for name, dot_source in blocks:
        print(f"Rendering digraph '{name}'...")
        if not render(name, dot_source, output_dir):
            errors += 1

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
