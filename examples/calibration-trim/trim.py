"""Local UTF-8 text cleanup; preserve line endings and the input file."""
import argparse
from pathlib import Path
import re
import sys


def trim(source, destination):
    data = Path(source).read_bytes()
    data.decode('utf-8')  # Reject unsupported encodings before creating output.
    parts = re.split(rb'(\r\n|\r|\n)', data)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].rstrip(b' \t')
    cleaned = b''.join(parts)
    with Path(destination).open('xb') as f:
        f.write(cleaned)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source')
    p.add_argument('destination')
    a = p.parse_args()
    try:
        trim(a.source, a.destination)
    except (OSError, UnicodeError) as e:
        print(f'conversion failed: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
