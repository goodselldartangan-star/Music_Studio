#!/usr/bin/env bash
# P9: append missing release files, never replace a historical artifact.
# Requires gh to be authenticated by caller; no credentials are stored here.
set -euo pipefail
if (($# < 2)); then
  echo "Usage: $0 <release-tag> <file> [file...]" >&2
  exit 2
fi
tag="$1"
shift
if [[ -z "$tag" ]]; then
  echo "Missing release tag" >&2
  exit 2
fi
existing="$(gh release view "$tag" --json assets --jq '.assets[].name')"
for file in "$@"; do
  if [[ ! -f "$file" ]]; then
    echo "Cannot publish missing file: $file" >&2
    exit 3
  fi
  filename="$(basename "$file")"
  if printf '%s\n' "$existing" | grep -Fqx -- "$filename"; then
    echo "Preserving existing release asset: $filename"
  else
    # Intentionally NEVER pass --clobber. A concurrent asset upload may cause
    # gh to fail; that is safer than overwriting an immutable preview.
    gh release upload "$tag" "$file"
    echo "Published previously absent asset: $filename"
    existing="$(printf '%s\n%s\n' "$existing" "$filename")"
  fi
done
