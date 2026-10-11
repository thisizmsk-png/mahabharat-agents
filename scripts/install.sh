#!/usr/bin/env bash
# scripts/install.sh — install mahabharat-agents from a git ref into a Claude Code scope.
#
# Usage: scripts/install.sh --target user|<project-dir> [--from <git-ref>] [--dry-run]
#                           [--skip-skill <name>]... [--force-replace]
#
#   --from <git-ref>   tag, branch or commit to install (default: HEAD). Files come from
#                      `git archive <ref>`, never from the working tree, so unreviewed
#                      edits in the checkout don't go live.
#   --target user      ${CLAUDE_CONFIG_DIR:-$HOME/.claude} (required: there is no default)
#   --target <dir>     <dir>/.claude (project scope; use this to iterate on unreleased work)
#   --dry-run          print what would happen; write nothing
#   --skip-skill <n>   leave skills/<n>/ alone (repeatable), e.g. another package's skill
#   --force-replace    replace files this installer does not own (still backed up)
#
# What it installs, flat (Claude Code scans agents/ recursively, so nothing nests):
#   agents/<name>.md          every agent in agents/roster.yaml (templates are never installed)
#   workflows/<file>.js       repo workflows/*.js, if the ref has a workflows/ directory
#   skills/<name>/...         skills/shared/* and skills/role-specific/* (except zero-bias)
#
# Safety:
#   - refuses if any destination path, or any of its parents inside the target, is a symlink
#   - only replaces what it owns: a path listed in the target's previous install manifest,
#     or a file whose content matches a committed version of the same file in this repo's
#     history, or (agents only) a file that defines the same agent name. Anything else, such
#     as another package's skill that shares a name, is refused unless --skip-skill or
#     --force-replace is given, so the installer never builds a half-foreign skill
#   - refuses a ref with any symlink under agents/, skills/ or workflows/ (files or
#     directories), checked in the git tree before extraction and again after it
#   - an existing file with different content is backed up to
#     <target>/mahabharat/backup/<sha>/<relpath> before it is replaced (never under agents/)
#   - writes <target>/mahabharat/install-manifest.json: {ref, sha, installed: [{path, sha256}]}
#   - never deletes anything; stale files from an older install are reported, not removed
#
# Bash 3.2 compatible (macOS /bin/bash).
set -euo pipefail

PROG="scripts/install.sh"

usage() {
    sed -n '4,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

die() {
    printf '%s: error: %s\n' "$PROG" "$*" >&2
    exit 1
}

warn() {
    printf '%s: warning: %s\n' "$PROG" "$*" >&2
}

FROM="HEAD"
TARGET=""
DRY_RUN=0
FORCE_REPLACE=0
SKIP_SKILLS=" "

while [ $# -gt 0 ]; do
    case "$1" in
        --from)
            [ $# -ge 2 ] || die "--from needs a git ref"
            FROM="$2"; shift 2 ;;
        --from=*)
            FROM="${1#--from=}"; shift ;;
        --target)
            [ $# -ge 2 ] || die "--target needs 'user' or a project directory"
            TARGET="$2"; shift 2 ;;
        --target=*)
            TARGET="${1#--target=}"; shift ;;
        --dry-run)
            DRY_RUN=1; shift ;;
        --force-replace)
            FORCE_REPLACE=1; shift ;;
        --skip-skill)
            [ $# -ge 2 ] || die "--skip-skill needs a skill name"
            SKIP_SKILLS="$SKIP_SKILLS$2 "; shift 2 ;;
        --skip-skill=*)
            SKIP_SKILLS="$SKIP_SKILLS${1#--skip-skill=} "; shift ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            usage >&2
            die "unknown argument: $1" ;;
    esac
done

[ -n "$FROM" ] || die "--from must not be empty"
[ -n "$TARGET" ] || die "--target is required: pass --target <project-dir>, or --target user to change ${CLAUDE_CONFIG_DIR:-$HOME/.claude} (your live user config)"

command -v git >/dev/null 2>&1 || die "git is required"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)" \
    || die "$SCRIPT_DIR is not inside a git checkout of mahabharat-agents"

SHA="$(git -C "$REPO" rev-parse --verify --quiet "${FROM}^{commit}")" \
    || die "cannot resolve git ref '$FROM' to a commit in $REPO"

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# ---------------------------------------------------------------- target ---

if [ "$TARGET" = "user" ]; then
    BASE_RAW="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
    SCOPE_DESC="user scope"
else
    [ -d "$TARGET" ] || die "project directory '$TARGET' does not exist"
    [ -L "$TARGET" ] && die "project directory '$TARGET' is a symlink; pass the real path"
    BASE_RAW="$(cd -P "$TARGET" && pwd)/.claude"
    SCOPE_DESC="project scope"
fi
BASE_RAW="${BASE_RAW%/}"
[ -n "$BASE_RAW" ] || die "empty target directory"

# The target dir itself must not be a symlink; its ancestors (e.g. /var -> /private/var
# on macOS) are resolved physically and are not ours to judge.
if [ -L "$BASE_RAW" ]; then
    die "target $BASE_RAW is a symlink; refusing to install through it"
fi
BASE_PARENT_RAW="$(dirname "$BASE_RAW")"
[ -d "$BASE_PARENT_RAW" ] || die "parent of target ($BASE_PARENT_RAW) does not exist"
BASE="$(cd -P "$BASE_PARENT_RAW" && pwd)/$(basename "$BASE_RAW")"

# Refuse if BASE or any component of BASE/<rel> is a symlink, or a non-directory
# sits where a directory is needed.
check_dest() {
    local rel="$1" p="$BASE" rest comp
    if [ -L "$p" ]; then die "refusing: $p is a symlink"; fi
    rest="$rel"
    while [ -n "$rest" ]; do
        comp="${rest%%/*}"
        if [ "$comp" = "$rest" ]; then rest=""; else rest="${rest#*/}"; fi
        p="$p/$comp"
        if [ -L "$p" ]; then
            die "refusing: $p is a symlink (destination paths and their parents must be real files/directories)"
        fi
        if [ -n "$rest" ] && [ -e "$p" ] && [ ! -d "$p" ]; then
            die "refusing: $p exists and is not a directory"
        fi
    done
    if [ -e "$p" ] && [ ! -f "$p" ]; then
        die "refusing: $p exists and is not a regular file"
    fi
}

valid_rel() {
    case "$1" in
        ""|/*|*..*|*//*) return 1 ;;
    esac
    printf '%s' "$1" | grep -Eq '^[A-Za-z0-9._/-]+$'
}

# ---------------------------------------------------------------- export ---

TMP="$(mktemp -d "${TMPDIR:-/tmp}/mahabharat-install.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Refuse symlinks anywhere under the installable trees, before anything is extracted.
# A symlinked directory (say skills/shared -> /elsewhere) would otherwise be followed
# after extraction, installing files from the installing machine as if they came from
# the reviewed ref. Symlinks elsewhere in the ref (docs, spikes) are never installed.
LINKS="$(git -C "$REPO" ls-tree -r --full-tree "$SHA" -- agents skills workflows \
    | awk -F '\t' '$1 ~ /^120000 / {print $2}')"
if [ -n "$LINKS" ]; then
    {
        printf '%s: error: ref %s contains symlinks under agents/, skills/ or workflows/ (nothing was written):\n' "$PROG" "$SHA"
        printf '%s\n' "$LINKS" | sed 's/^/  /'
    } >&2
    exit 1
fi

mkdir "$TMP/src"
git -C "$REPO" archive --format=tar "$SHA" | tar -xf - -C "$TMP/src"
SRC="$TMP/src"
# Belt and braces: the extracted installable trees must hold no symlinks either.
for top in agents skills workflows; do
    if [ -e "$SRC/$top" ] || [ -L "$SRC/$top" ]; then
        [ -L "$SRC/$top" ] && die "refusing: '$top' is a symlink in ref $SHA"
        if [ -n "$(find "$SRC/$top" -type l -print -quit)" ]; then
            die "refusing: ref $SHA contains a symlink under $top/"
        fi
    fi
done

ROSTER="$SRC/agents/roster.yaml"
[ -f "$ROSTER" ] || die "ref '$FROM' ($SHA) has no agents/roster.yaml; it predates the v1 layout"

# Print the `name:` value of a file's frontmatter (frontmatter must start on line 1).
frontmatter_name() {
    awk '
        NR == 1 { if ($0 != "---") exit 1; next }
        $0 == "---" { exit }
        /^name:[[:space:]]*/ {
            v = $0
            sub(/^name:[[:space:]]*/, "", v)
            sub(/[[:space:]]+$/, "", v)
            gsub(/^["\047]|["\047]$/, "", v)
            print v
            exit
        }
    ' "$1"
}

# Plan: parallel arrays of source path, destination path (relative to BASE), and the
# source's path inside the ref (used to recognise earlier versions of the same file).
PLAN_SRC=()
PLAN_REL=()
PLAN_ORIG=()
SEEN_NAMES=" "
PLANNED_SKILLS=()
SKIPPED=()

add_plan() {
    local src="$1" rel="$2"
    valid_rel "$rel" || die "unsafe destination path '$rel'"
    [ -L "$src" ] && die "refusing: '${src#"$SRC"/}' is a symlink in ref $SHA"
    [ -f "$src" ] || die "missing file '${src#"$SRC"/}' in ref $SHA"
    PLAN_SRC+=("$src")
    PLAN_REL+=("$rel")
    PLAN_ORIG+=("${src#"$SRC"/}")
}

# Agents, from the roster.
roster_count=0
while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
        *"{name:"*) ;;
        *) continue ;;
    esac
    parsed="$(printf '%s\n' "$line" | sed -nE \
        's/^[[:space:]]*-[[:space:]]*\{[[:space:]]*name:[[:space:]]*([a-z][a-z0-9-]*)[[:space:]]*,[[:space:]]*file:[[:space:]]*([A-Za-z0-9._/-]+)[[:space:]]*,[[:space:]]*rank:[[:space:]]*(god|master|sepoy)[[:space:]]*\}[[:space:]]*$/\1 \2 \3/p')"
    [ -n "$parsed" ] || die "cannot parse roster line (keep one {name, file, rank} mapping per line): $line"
    set -- $parsed
    name="$1"; file="$2"
    case "$file" in
        agents/*.md) ;;
        *) die "roster file for '$name' must be agents/**/*.md, got '$file'" ;;
    esac
    valid_rel "$file" || die "unsafe roster path '$file'"
    case "$SEEN_NAMES" in
        *" $name "*) die "agent '$name' is listed twice in agents/roster.yaml" ;;
    esac
    SEEN_NAMES="$SEEN_NAMES$name "
    [ -f "$SRC/$file" ] || die "roster lists '$file' for '$name', but ref $SHA has no such file"
    fm_name="$(frontmatter_name "$SRC/$file" || true)"
    [ "$fm_name" = "$name" ] || die "$file: frontmatter name is '${fm_name:-<missing>}', roster says '$name' (frontmatter must start on line 1)"
    add_plan "$SRC/$file" "agents/$name.md"
    roster_count=$((roster_count + 1))
done < "$ROSTER"
[ "$roster_count" -gt 0 ] || die "agents/roster.yaml lists no agents"
set --

# Workflows.
workflow_count=0
if [ -d "$SRC/workflows" ]; then
    for f in "$SRC/workflows/"*.js; do
        [ -e "$f" ] || [ -L "$f" ] || continue
        add_plan "$f" "workflows/$(basename "$f")"
        workflow_count=$((workflow_count + 1))
    done
fi

# Skills (shared + role-specific; zero-bias is retired and never installed).
skill_count=0
SEEN_SKILLS=" "
for kind in shared role-specific; do
    [ -d "$SRC/skills/$kind" ] || continue
    for d in "$SRC/skills/$kind/"*/; do
        [ -d "$d" ] || continue
        d="${d%/}"
        sname="$(basename "$d")"
        [ "$sname" = "zero-bias" ] && continue
        [ -f "$d/SKILL.md" ] || continue
        case "$SKIP_SKILLS" in
            *" $sname "*) SKIPPED+=("skills/$sname"); continue ;;
        esac
        case "$SEEN_SKILLS" in
            *" $sname "*) die "skill '$sname' exists in more than one skills/ group" ;;
        esac
        SEEN_SKILLS="$SEEN_SKILLS$sname "
        if [ -n "$(find "$d" -type l -print -quit)" ]; then
            die "refusing: skill '$sname' contains a symlink in ref $SHA"
        fi
        while IFS= read -r sf; do
            add_plan "$sf" "skills/$sname/${sf#"$d"/}"
        done < <(find "$d" -type f ! -name '.DS_Store' | LC_ALL=C sort)
        PLANNED_SKILLS+=("$sname ${d#"$SRC"/}")
        skill_count=$((skill_count + 1))
    done
done

# -------------------------------------------------------------- validate ---
# All checks run before the first write, so a refusal leaves the target untouched.

MANIFEST_REL="mahabharat/install-manifest.json"
BACKUP_REL="mahabharat/backup/$SHA"
check_dest "$MANIFEST_REL"
check_dest "$BACKUP_REL/.probe"

case "$SKIP_SKILLS" in
    " ") ;;
    *)
        for s in $SKIP_SKILLS; do
            [ -d "$SRC/skills/shared/$s" ] || [ -d "$SRC/skills/role-specific/$s" ] \
                || warn "--skip-skill $s: ref $SHA has no such skill"
        done ;;
esac

# Paths a previous install of this package recorded (one per line, padded with spaces).
PREV_PATHS=" "
if [ -f "$BASE/$MANIFEST_REL" ]; then
    while IFS= read -r old; do
        PREV_PATHS="$PREV_PATHS$old "
    done < <(grep -oE '"path": "[^"]+"' "$BASE/$MANIFEST_REL" | sed -E 's/^"path": "(.*)"$/\1/')
fi

in_prev_manifest() {
    case "$PREV_PATHS" in *" $1 "*) return 0 ;; esac
    return 1
}

# Is <file> byte-identical to some committed version of <path-in-repo>, in any ref?
matches_repo_history() {
    local file="$1" orig="$2" blob
    blob="$(git -C "$REPO" hash-object --no-filters "$file" 2>/dev/null)" || return 1
    git -C "$REPO" log --all --format= --raw --no-abbrev -- "$orig" 2>/dev/null \
        | awk '{print $3; print $4}' | grep -qx "$blob"
}

FOREIGN=()

# Skill directories: an existing skills/<name>/ must be ours (or skipped) before any of
# its files are touched. Another package's skill with the same name is left whole.
for entry in ${PLANNED_SKILLS[@]+"${PLANNED_SKILLS[@]}"}; do
    sname="${entry%% *}"; sorig="${entry#* }"
    sdir="$BASE/skills/$sname"
    check_dest "skills/$sname/SKILL.md"
    [ -d "$sdir" ] || continue
    nfiles="$(find "$sdir" -type f ! -name '.DS_Store' | wc -l | tr -d ' ')"
    [ "$nfiles" -gt 0 ] || continue
    case "$PREV_PATHS" in *" skills/$sname/"*) continue ;; esac
    if [ -f "$sdir/SKILL.md" ] && matches_repo_history "$sdir/SKILL.md" "$sorig/SKILL.md"; then
        continue
    fi
    other="$(frontmatter_name "$sdir/SKILL.md" 2>/dev/null || true)"
    FOREIGN+=("skills/$sname/ (existing skill${other:+ named '$other'}, $nfiles file(s); not installed by mahabharat-agents and not a version of its '$sname' skill)")
done

n=${#PLAN_REL[@]}
ACTIONS=()
i=0
while [ "$i" -lt "$n" ]; do
    rel="${PLAN_REL[$i]}"
    check_dest "$rel"
    dest="$BASE/$rel"
    if [ ! -e "$dest" ]; then
        ACTIONS+=("new")
    elif cmp -s "${PLAN_SRC[$i]}" "$dest"; then
        ACTIONS+=("same")
    else
        check_dest "$BACKUP_REL/$rel"
        ACTIONS+=("replace")
        case "$rel" in
            skills/*) ;;  # ownership was decided per skill directory above
            *)
                owned=0
                if in_prev_manifest "$rel" || matches_repo_history "$dest" "${PLAN_ORIG[$i]}"; then
                    owned=1
                else
                    case "$rel" in
                        agents/*.md)
                            aname="${rel#agents/}"; aname="${aname%.md}"
                            [ "$(frontmatter_name "$dest" 2>/dev/null || true)" = "$aname" ] && owned=1 ;;
                    esac
                fi
                if [ "$owned" -eq 0 ]; then
                    FOREIGN+=("$rel (existing file is not from mahabharat-agents: not in a previous install manifest and not a version of ${PLAN_ORIG[$i]})")
                fi ;;
        esac
    fi
    i=$((i + 1))
done

if [ "${#FOREIGN[@]}" -gt 0 ]; then
    if [ "$FORCE_REPLACE" -eq 1 ]; then
        for f in "${FOREIGN[@]}"; do
            warn "--force-replace: replacing $f; the current files are backed up first, and files of a foreign skill that this install does not ship are left in place"
        done
    else
        {
            printf '%s: error: refusing to replace files this installer does not own (nothing was written):\n' "$PROG"
            for f in "${FOREIGN[@]}"; do printf '  %s\n' "$f"; done
            printf 'Move them out of %s, pass --skip-skill <name> to leave a skill alone, or pass\n' "$BASE"
            printf -- '--force-replace to back them up and replace them anyway.\n'
        } >&2
        exit 1
    fi
fi

# ----------------------------------------------------------------- apply ---

echo "mahabharat-agents installer"
echo "  ref:    $FROM ($SHA)"
echo "  target: $BASE ($SCOPE_DESC)"
[ "$DRY_RUN" -eq 1 ] && echo "  mode:   dry run (nothing is written)"
echo ""
for s in ${SKIPPED[@]+"${SKIPPED[@]}"}; do
    echo "  - $s (skipped: --skip-skill; left as it is)"
done

backup_path_for() {
    local rel="$1" src="$2" bp
    bp="$BASE/$BACKUP_REL/$rel"
    if [ -e "$bp" ]; then
        if cmp -s "$src" "$bp"; then
            printf '%s\n' "$bp"; return
        fi
        local k=1
        # A dangling symlink is false for -e but still taken: never pick it, or cp would
        # write through it. A symlink is never reused as an existing backup either.
        while [ -e "$bp.$k" ] || [ -L "$bp.$k" ]; do
            if [ ! -L "$bp.$k" ] && cmp -s "$src" "$bp.$k"; then printf '%s\n' "$bp.$k"; return; fi
            k=$((k + 1))
        done
        bp="$bp.$k"
    fi
    printf '%s\n' "$bp"
}

# The temp file is created exclusively by mktemp (a symlink planted at a predictable
# temp name could otherwise redirect cp), then renamed over the destination.
copy_into_place() {
    local src="$1" dest="$2" tmpf
    mkdir -p "$(dirname "$dest")"
    tmpf="$(mktemp "$(dirname "$dest")/.$(basename "$dest").mahabharat-tmp.XXXXXX")" \
        || die "cannot create a temp file next to $dest"
    cp "$src" "$tmpf"
    chmod 644 "$tmpf"
    mv -f "$tmpf" "$dest"
}

changed=0
i=0
while [ "$i" -lt "$n" ]; do
    rel="${PLAN_REL[$i]}"
    src="${PLAN_SRC[$i]}"
    dest="$BASE/$rel"
    case "${ACTIONS[$i]}" in
        same)
            echo "  = $rel (unchanged)" ;;
        new)
            changed=$((changed + 1))
            if [ "$DRY_RUN" -eq 1 ]; then
                echo "  + $rel (would install)"
            else
                copy_into_place "$src" "$dest"
                echo "  + $rel"
            fi ;;
        replace)
            changed=$((changed + 1))
            bp="$(backup_path_for "$rel" "$dest")"
            # backup_path_for runs in a subshell, so check the chosen path here, in the
            # main shell: no symlink anywhere on it (the suffixed .N candidates included).
            check_dest "${bp#"$BASE"/}"
            if [ "$DRY_RUN" -eq 1 ]; then
                echo "  ~ $rel (would replace; current file would be backed up to ${bp#"$BASE"/})"
            else
                if [ ! -e "$bp" ]; then
                    mkdir -p "$(dirname "$bp")"
                    cp -p "$dest" "$bp"
                fi
                copy_into_place "$src" "$dest"
                echo "  ~ $rel (replaced; previous version saved to ${bp#"$BASE"/})"
            fi ;;
    esac
    i=$((i + 1))
done

# -------------------------------------------------------------- manifest ---

MANIFEST_TMP="$TMP/install-manifest.json"
{
    printf '{\n'
    printf '  "ref": "%s",\n' "$(json_escape "$FROM")"
    printf '  "sha": "%s",\n' "$SHA"
    printf '  "installed": ['
    i=0
    while [ "$i" -lt "$n" ]; do
        [ "$i" -gt 0 ] && printf ','
        printf '\n    {"path": "%s", "sha256": "%s"}' "${PLAN_REL[$i]}" "$(sha256_of "${PLAN_SRC[$i]}")"
        i=$((i + 1))
    done
    printf '\n  ]\n}\n'
} > "$MANIFEST_TMP"

MANIFEST="$BASE/$MANIFEST_REL"

# Report files a previous install put in place that this ref no longer ships.
if [ -f "$MANIFEST" ]; then
    while IFS= read -r old; do
        found=0
        i=0
        while [ "$i" -lt "$n" ]; do
            if [ "${PLAN_REL[$i]}" = "$old" ]; then found=1; break; fi
            i=$((i + 1))
        done
        if [ "$found" -eq 0 ] && [ -e "$BASE/$old" ]; then
            warn "stale: $old was installed by a previous manifest but is not in $SHA; left in place (remove it by hand)"
        fi
    done < <(grep -oE '"path": "[^"]+"' "$MANIFEST" | sed -E 's/^"path": "(.*)"$/\1/')
fi

# Old layouts (agents/sepoys/, _template.md) redefine agent names; Claude Code scans
# agents/ recursively. Report them; moving the user's files is the user's call.
if [ -d "$BASE/agents" ]; then
    while IFS= read -r f; do
        relf="${f#"$BASE"/}"
        case " ${PLAN_REL[*]} " in
            *" $relf "*) continue ;;
        esac
        case "$relf" in
            */_template.md|*/sepoys/*)
                warn "old-layout file $relf is still under agents/; move it OUT of $BASE/agents (see docs/upgrading-to-v1.md)"
                continue ;;
        esac
        fname="$(frontmatter_name "$f" 2>/dev/null || true)"
        if [ -n "$fname" ]; then
            case "$SEEN_NAMES" in
                *" $fname "*) warn "$relf also defines agent '$fname'; move it out of $BASE/agents (duplicate definition)" ;;
            esac
        fi
    done < <(find "$BASE/agents" -name '*.md' \( -type f -o -type l \) 2>/dev/null | LC_ALL=C sort)
fi

if [ "$DRY_RUN" -eq 1 ]; then
    echo ""
    echo "  would write ${MANIFEST_REL} ($n files)"
else
    if [ -f "$MANIFEST" ] && cmp -s "$MANIFEST_TMP" "$MANIFEST"; then
        :
    else
        copy_into_place "$MANIFEST_TMP" "$MANIFEST"
    fi
    echo ""
    echo "  wrote ${MANIFEST_REL} ($n files)"
fi

echo ""
echo "Done: $roster_count agents, $skill_count skills, $workflow_count workflows; $changed file(s) $( [ "$DRY_RUN" -eq 1 ] && echo 'would change' || echo 'changed')."
if [ "$TARGET" = "user" ]; then
    echo "Verify with: scripts/smoke.sh --user"
else
    echo "Verify with: scripts/smoke.sh --project $(dirname "$BASE")"
fi
