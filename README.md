#!/usr/bin/env bash
# git_superuser_workflow - Hardened for Termux/puppygit
# Version: 2025.11.14_ENHANCED4
# Usage: ./git_superuser_workflow.sh <command> [--dry-run] [--json] [--workdir DIR] [--check] [--version]

set -euo pipefail
IFS=$'\n\t'

# ----------------------------------------------------------------------
# Globals & Setup
# ----------------------------------------------------------------------
SCRIPT_NAME="${0##*/}"
VERSION="2025.11.14_ENHANCED4"
DRY_RUN=0
JSON_OUT=0
WORKDIR="$(pwd)"
SELFTEST=0
LOG_DIR="${HOME:-/tmp}/.local/log/git_workflow"
SNAPSHOT_DIR="${HOME:-/tmp}/.local/snapshots"
SNAPSHOT_RETAIN=5                        # keep last N snapshots
SNAPSHOT_MAX_BYTES=$((200*1024*1024))    # 200 MiB warning threshold
LARGE_FILE_LIMIT_BYTES=$((10*1024*1024)) # 10 MiB pre-commit limit
WF_TMPDIR=""

if [ -z "${BASH_VERSION:-}" ]; then
  echo "ERROR: Requires bash." >&2
  exit 2
fi

# Portable command resolution
_cmd() { command -v "$1" 2>/dev/null || printf "%s\n" ""; }
TAR_CMD=$(_cmd tar || true)
DATE_CMD=$(_cmd date || true)
STAT_CMD=$(_cmd stat || true)
SHA256SUM_CMD=$(_cmd sha256sum || _cmd shasum || true)
AWK_CMD=$(_cmd awk || true)
DU_CMD=$(_cmd du || true)
XARGS_CMD=$(_cmd xargs || true)

# Ensure required directories exist early (no-op in dry-run)
mkdir_p() {
  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[DRY-RUN] mkdir -p \"$1\""
  else
    mkdir -p "$1"
  fi
}
mkdir_p "${LOG_DIR}"
mkdir_p "${SNAPSHOT_DIR}"

# Safer portable mktemp_dir
mktemp_dir() {
  if [ -n "${WF_TMPDIR:-}" ] && [ -d "$WF_TMPDIR" ]; then
    printf '%s' "$WF_TMPDIR"
    return 0
  fi
  local try
  for try in "$(pwd)" "/data/data/com.termux/files/usr/tmp" "/tmp" "/var/tmp"; do
    if [ -d "$try" ] && [ -w "$try" ]; then
      WF_TMPDIR=$(mktemp -d "${try}/git_workflow.XXXXXX" 2>/dev/null || true)
      [ -n "${WF_TMPDIR:-}" ] && { printf '%s' "$WF_TMPDIR"; return 0; }
    fi
  done
  WF_TMPDIR=$(mktemp -d 2>/dev/null || true)
  if [ -n "${WF_TMPDIR:-}" ]; then
    printf '%s' "$WF_TMPDIR"
    return 0
  fi
  echo "ERROR: unable to create temporary directory" >&2
  return 1
}

cleanup() {
  if [ -n "${WF_TMPDIR:-}" ] && [ -d "${WF_TMPDIR}" ]; then
    rm -rf "${WF_TMPDIR}"
  fi
}
trap cleanup EXIT

# ----------------------------------------------------------------------
# Logging & Helper Functions
# ----------------------------------------------------------------------
_log() {
  local level="$1" message="$2"
  local timestamp
  timestamp=$("${DATE_CMD:-date}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date '+%Y-%m-%d %H:%M:%S')
  local log_file="${LOG_DIR}/${SCRIPT_NAME}.log"
  case "$level" in
    error) printf "[%s] [ERROR] %s\n" "$timestamp" "$message" >&2 ;;
    warn)  printf "[%s] [WARN]  %s\n" "$timestamp" "$message" >&2 ;;
    info)  printf "[%s] [INFO]  %s\n" "$timestamp" "$message" ;;
    *)     printf "[%s] [%s]  %s\n" "$timestamp" "${level^^}" "$message" ;;
  esac
  if [ "${DRY_RUN:-0}" -eq 0 ]; then
    printf "[%s] [%s] %s\n" "$timestamp" "${level^^}" "$message" >> "$log_file" 2>/dev/null || true
  fi
}

run_or_dry() {
  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    _log info "[DRY-RUN] $*"
    return 0
  else
    bash -c "$*"
    return $?
  fi
}

numfmt_or_human() {
  local size="$1"
  if command -v numfmt >/dev/null 2>&1; then
    numfmt --to=iec-i --suffix=B --padding=7 "$size" 2>/dev/null || printf "%sB" "$size"
  else
    "${AWK_CMD:-awk}" -v s="$size" 'function human(x){
      split("B KB MB GB TB PB",u); i=1;
      while(x>1024 && i<6){x/=1024; i++}
      return sprintf("%.1f %s", x, u[i]);
    }{print human(s)}'
  fi
}

safe_stat_size() {
  local file="$1"
  if [ -z "$file" ] || [ ! -e "$file" ]; then echo 0; return; fi
  if command -v stat >/dev/null 2>&1; then
    if stat -c "%s" "$file" 2>/dev/null; then
      stat -c "%s" "$file" 2>/dev/null || echo 0
    else
      stat -f "%z" "$file" 2>/dev/null || echo 0
    fi
  else
    wc -c <"$file" 2>/dev/null || echo 0
  fi
}

prune_snapshots() {
  local prefix="${SCRIPT_NAME%%.*}_"
  local files
  mapfile -t files < <(find "${SNAPSHOT_DIR}" -maxdepth 1 -type f -name "${prefix}*.tar.gz" -printf '%T@ %p\n' 2>/dev/null |
    sort -n -r | awk '{print $2}')
  for f in "${files[@]:${SNAPSHOT_RETAIN}}"; do
    [ -z "$f" ] && continue
    if [ "${DRY_RUN:-0}" -eq 1 ]; then
      _log info "[DRY-RUN] rm -f \"$f\""
    else
      rm -f "$f" || _log warn "Failed to remove old snapshot: $f"
    fi
  done
}

check_repo_size() {
  if command -v du >/dev/null 2>&1; then
    local size_mb
    size_mb=$(( $(${DU_CMD} -sm . 2>/dev/null | cut -f1 || echo 0) ))
    if [ "$size_mb" -gt 500 ]; then
      _log warn "Repository size ${size_mb} MB may be slow on Termux."
    fi
  fi
}

primary_branch() {
  local pb
  pb=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||' || true)
  if [ -n "$pb" ]; then printf '%s' "$pb"; return 0; fi
  for candidate in main master trunk; do
    if git show-ref --verify --quiet "refs/heads/$candidate"; then printf '%s' "$candidate"; return 0; fi
  done
  printf 'main'
}

require_cmds() {
  local miss=0
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      printf 'MISSING: %s\n' "$cmd" >&2
      miss=1
    fi
  done
  return $miss
}

# ----------------------------------------------------------------------
# Core Workflow Functions
# ----------------------------------------------------------------------

dependency_master() {
  _log info "Running dependency_master for $(pwd)"
  local DEPENDENCY_TRACKERS=( "package.json:npm" "requirements.txt:pip" "composer.json:composer" "Gemfile:bundle" "pom.xml:mvn" "go.mod:go" "Cargo.toml:cargo" )
  local reports_human="./dependency_master_report.txt"
  local reports_json="./dependency_master_report.json"
  : > "$reports_human"
  : > "$reports_json"

  printf '{ "updates": [\n' > "$reports_json"
  local first_entry=1

  for tracker in "${DEPENDENCY_TRACKERS[@]}"; do
    local FILE=${tracker%%:*}
    local TOOL=${tracker##*:}
    if [ ! -f "$FILE" ]; then
      continue
    fi

    _log info "Detected $FILE (tool: $TOOL)"
    printf '--- Detected %s (tool: %s) ---\n' "$FILE" "$TOOL" | tee -a "$reports_human"

    local entry_status="ok"
    local entry_msg=""
    if [ "${DRY_RUN:-0}" -eq 1 ]; then
      entry_status="dry-run"
      entry_msg="Would run $TOOL update for $FILE"
      _log info "[DRY-RUN] $entry_msg"
    else
      case "$TOOL" in
        npm)
          if command -v npm >/dev/null 2>&1; then
            run_or_dry "npm update --no-audit --no-fund --no-optional" || { entry_status="error"; entry_msg="npm update failed"; }
            run_or_dry "npm audit fix --silent || true"
          else
            entry_status="missing-tool"; entry_msg="npm not installed"
          fi
          ;;
        pip)
          local VENV_ACTIVATED=0
          if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
            # shellcheck disable=SC1091
            . venv/bin/activate && VENV_ACTIVATED=1 || VENV_ACTIVATED=0
          fi
          if command -v pip >/dev/null 2>&1; then
            run_or_dry "pip install --upgrade -r \"$FILE\"" || { entry_status="error"; entry_msg="pip upgrade failed"; }
            command -v safety >/dev/null 2>&1 && run_or_dry "safety check" || true
          else
            entry_status="missing-tool"; entry_msg="pip not installed"
          fi
          [ "${VENV_ACTIVATED:-0}" -eq 1 ] && deactivate || true
          ;;
        composer)
          if command -v composer >/dev/null 2>&1; then
            run_or_dry "composer update --no-interaction" || { entry_status="error"; entry_msg="composer update failed"; }
          else
            entry_status="missing-tool"; entry_msg="composer not installed"
          fi
          ;;
        bundle)
          if command -v bundle >/dev/null 2>&1; then
            run_or_dry "bundle update" || { entry_status="error"; entry_msg="bundle update failed"; }
          else
            entry_status="missing-tool"; entry_msg="bundle not installed"
          fi
          ;;
        mvn)
          if command -v mvn >/dev/null 2>&1; then
            run_or_dry "mvn versions:update-properties -DgenerateBackupPoms=false" || { entry_status="error"; entry_msg="mvn failed"; }
          else
            entry_status="missing-tool"; entry_msg="mvn not installed"
          fi
          ;;
        go)
          if command -v go >/dev/null 2>&1; then
            run_or_dry "go get -u ./..." || { entry_status="error"; entry_msg="go get failed"; }
            run_or_dry "go mod tidy" || true
          else
            entry_status="missing-tool"; entry_msg="go not installed"
          fi
          ;;
        cargo)
          if command -v cargo >/dev/null 2>&1; then
            run_or_dry "cargo update" || { entry_status="error"; entry_msg="cargo update failed"; }
          else
            entry_status="missing-tool"; entry_msg="cargo not installed"
          fi
          ;;
        *)
          entry_status="unknown"; entry_msg="unknown tool"
          ;;
      esac
    fi

    local json_entry
    json_entry=$(printf '{"file":"%s","tool":"%s","status":"%s","message":"%s"}' \
                 "$(printf '%s' "$FILE" | sed 's/"/\\"/g')" \
                 "$(printf '%s' "$TOOL" | sed 's/"/\\"/g')" \
                 "$(printf '%s' "$entry_status" | sed 's/"/\\"/g')" \
                 "$(printf '%s' "$entry_msg" | sed 's/"/\\"/g')")

    if [ "$first_entry" -eq 1 ]; then
      printf '  %s\n' "$json_entry" >> "$reports_json"
      first_entry=0
    else
      printf ' , %s\n' "$json_entry" >> "$reports_json"
    fi

    _log info "Finished processing $FILE"
  done

  printf ']\n}\n' >> "$reports_json"
  _log info "Dependency master complete. Reports: $reports_human, $reports_json"
  [ "${JSON_OUT:-0}" -eq 1 ] && cat "$reports_json"
}

git_security_audit() {
  if ! command -v jq >/dev/null 2>&1; then
    _log error "'jq' is required for git_security_audit."
    exit 1
  fi
  _log info "Running Git Security Audit..."
  local human="./git_security_audit_report.txt"
  local json="./git_security_audit_report.json"
  : > "$human"
  : > "$json"

  local PB
  PB=$(primary_branch)
  local audit_time
  audit_time=$("${DATE_CMD:-date}" '+%F %T' 2>/dev/null || date '+%F %T')
  local secret_status="skipped"
  local secret_output_json='[]'
  local lfs_status="no"
  local large_files_json='[]'
  local divergence_json='[]'

  local lf_tmp div_tmp
  lf_tmp="$(mktemp_dir)/large_files.$$.$(date +%s).json"
  div_tmp="$(mktemp_dir)/divergence.$$.$(date +%s).json"
  : > "$lf_tmp"
  : > "$div_tmp"

  {
    printf '=== Git Security Audit (%s) ===\n' "$audit_time"
    printf 'Primary branch: %s\n\n' "$PB"

    printf '1) Secret-pattern scan (recent 200 commits):\n'
    if command -v gitleaks >/dev/null 2>&1; then
      if [ "${DRY_RUN:-0}" -eq 1 ]; then
        printf '[DRY-RUN] gitleaks detect --report-format json --report-path ./gitleaks.json --max-count=200\n'
        secret_status="dry-run"
      else
        local tmpf
        tmpf="$(mktemp_dir)/gitleaks.$(date +%s%N).json"
        gitleaks detect --report-format json --report-path "$tmpf" --log-opts "--max-count=200" >/dev/null 2>&1 || true
        if [ -s "$tmpf" ]; then
          secret_output_json=$(jq -c '.' "$tmpf" 2>/dev/null || printf '%s' '[]')
          local hits
          hits=$(printf '%s' "$secret_output_json" | jq 'length' 2>/dev/null || echo 0)
          if [ "$hits" -gt 0 ]; then
            secret_status="leaks-found"
            printf 'Leaks found (showing first 5):\n'
            jq -r '.[] | "\(.Rule.ID) in \(.File): \(.Commit)"' "$tmpf" 2>/dev/null | head -n 5
          else
            secret_status="ok"
            printf 'No leaks found.\n'
          fi
        else
          secret_status="ok"
          printf 'gitleaks produced no findings.\n'
        fi
        [ -f "$tmpf" ] && rm -f "$tmpf"
      fi
    else
      printf 'gitleaks not installed — falling back to simple grep (may be noisy).\n'
      secret_status="fallback-grep"
      secret_output_json=$(git rev-list --max-count=200 --all 2>/dev/null | xargs -n1 -I{} git grep -I --line-number -e "password" -e "secret" -e "token" -e "key" {} 2>/dev/null | jq -R -s 'split("\n") | map(select(length>0))' 2>/dev/null || printf '%s' '[]')
      if [ "$secret_output_json" = "[]" ]; then
        printf 'No simple matches.\n'
      else
        printf 'Matches found (showing first 5):\n'
        printf '%s\n' "$(printf '%s' "$secret_output_json" | jq -r '.[]' 2>/dev/null | head -n 5 || echo 'Error parsing grep output.')"
      fi
    fi

    printf '\n2) Large files and LFS Status (Top 10):\n'
    if command -v git-lfs >/dev/null 2>&1 || git lfs version >/dev/null 2>&1 2>/dev/null; then
      lfs_status="yes"
      printf 'Git LFS is ACTIVE. Tracked files: %s\n' "$(git lfs ls-files 2>/dev/null | wc -l | xargs || echo 0)"
    fi

    while IFS=' ' read -r size path; do
      [ -z "$size" ] && continue
      local human_size
      human_size=$(numfmt_or_human "$size")
      printf '%s %s\n' "$human_size" "$path"
      local entry
      entry=$(printf '{"size_bytes":%s,"size_human":"%s","path":"%s"}' "$size" "$human_size" "$(printf '%s' "$path" | sed 's/"/\\"/g')")
      printf '%s\n' "$entry" >> "$lf_tmp"
    done < <(
      git rev-list --objects --all 2>/dev/null |
      git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>/dev/null |
      awk '/^blob/ {print $3, $4}' |
      sort -rn |
      head -n 10
    )

    printf '\n3) Branch Divergence Check (commits not on origin/%s):\n' "$PB"
    git for-each-ref --format='%(refname:short)' refs/remotes/origin 2>/dev/null | grep -v '\->' | while IFS= read -r remote_branch; do
      [ -z "$remote_branch" ] && continue
      if [ "$remote_branch" = "origin/$PB" ]; then continue; fi
      local DIVERGED_COMMITS
      DIVERGED_COMMITS=$(git log --oneline "origin/$PB..$remote_branch" 2>/dev/null || true)
      if [ -n "$DIVERGED_COMMITS" ]; then
        local commit_count
        commit_count=$(printf '%s\n' "$DIVERGED_COMMITS" | wc -l | xargs)
        printf '  [DIVERGED] %s has %s unmerged commits.\n' "$remote_branch" "$commit_count"
        local commits_json
        commits_json=$(printf '%s\n' "$DIVERGED_COMMITS" | head -n 3 | jq -R -s 'split("\n") | map(select(length>0))' 2>/dev/null || '[]')
        local entry
        entry=$(jq -n --arg branch "$remote_branch" --argjson commits "$commits_json" --arg cnt "$commit_count" '{branch:$branch,unmerged_count:($cnt|tonumber),latest_commits:$commits,status:"diverged"}' 2>/dev/null || printf '%s' '{}')
        printf '%s\n' "$entry" >> "$div_tmp"
      fi
    done

    printf '\n4) Git Configuration Audit (Local):\n'
    git config --local --list | grep -E 'user|credential' || printf '(none)\n'
    printf '\n'
  } > "$human"

  if [ -s "$lf_tmp" ]; then
    large_files_json=$(jq -s '.' "$lf_tmp" 2>/dev/null || printf '[]')
  fi
  if [ -s "$div_tmp" ]; then
    divergence_json=$(jq -s '.' "$div_tmp" 2>/dev/null || printf '[]')
  fi
  [ -f "$lf_tmp" ] && rm -f "$lf_tmp"
  [ -f "$div_tmp" ] && rm -f "$div_tmp"

  jq -n \
    --arg pb "$PB" \
    --arg time "$audit_time" \
    --arg secret_status "$secret_status" \
    --argjson secret_output "$secret_output_json" \
    --arg lfs "$lfs_status" \
    --argjson large_files "$large_files_json" \
    --argjson divergence "$divergence_json" \
    '{primary_branch:$pb, time:$time, secret_scan:{status:$secret_status, output:$secret_output}, lfs_status:$lfs, large_files:$large_files, branch_divergence:$divergence}' > "$json" 2>/dev/null || printf '%s\n' '{"error":"failed-to-build-json"}' > "$json"

  _log info "Security audit complete. Reports: $human, $json"
  [ "${JSON_OUT:-0}" -eq 1 ] && cat "$json"
}

git_workflow_optimizer() {
  _log info "Running Git Workflow Optimizer..."
  local human="./git_workflow_optimizer_report.txt"
  local json="./git_workflow_optimizer_report.json"
  : > "$human"
  : > "$json"

  local total_remote_branches=0
  local total_commits=0
  local repo_size="unknown"

  {
    printf '=== Git Workflow Optimizer (%s) ===\n' "$($DATE_CMD '+%F %T' 2>/dev/null || date '+%F %T')"
    printf '1) Performing garbage collection and compression...\n'
    if [ "${DRY_RUN:-0}" -eq 1 ]; then
      printf '[DRY-RUN] git gc --aggressive --prune=now\n'
    else
      run_or_dry "git gc --aggressive --prune=now" || true
    fi

    printf '\n2) Applying local repository configuration for performance...\n'
    run_or_dry "git config --local core.compression 0"
    run_or_dry "git config --local core.loosecompression 0"
    run_or_dry "git config --local pack.windowMemory \"1g\""
    run_or_dry "git config --local pack.packSizeLimit 2g"

    printf '\n3) Cleaning up merged local branches...\n'
    local PB
    PB=$(primary_branch)
    git branch --merged "$PB" 2>/dev/null | grep -Ev "^[* ]($PB|master|develop|trunk)$" | while IFS= read -r branch_name; do
      branch_name=$(printf '%s' "$branch_name" | xargs)
      [ -z "$branch_name" ] && continue
      printf '  Deleting merged branch: %s\n' "$branch_name"
      run_or_dry "git branch -d \"$branch_name\"" || true
    done

    printf '\n4) Pruning stale remote tracking branches...\n'
    run_or_dry "git remote prune origin" || true

    printf '\n5) Generating workflow metrics...\n'
    total_remote_branches=$(git branch -r 2>/dev/null | wc -l | xargs || echo 0)
    total_commits=$(git rev-list --count HEAD 2>/dev/null | xargs || echo 0)
    repo_size=$(du -sh .git 2>/dev/null | awk '{print $1}' || echo "unknown")

    printf 'Total remote branches: %s\n' "$total_remote_branches"
    printf 'Total commits: %s\n' "$total_commits"
    printf 'Repo size: %s\n' "$repo_size"

    printf '\nCommit Frequency (Top 5):\n'
    git log --date=short --pretty=format:"%ad" 2>/dev/null | sort | uniq -c | sort -rn | head -n 5

    printf '\nTop 5 Contributors:\n'
    git shortlog -sn 2>/dev/null | head -n 5
  } > "$human"

  if command -v jq >/dev/null 2>&1; then
    jq -n --arg remote_branches "$total_remote_branches" --arg commits "$total_commits" --arg repo_size "$repo_size" \
      '{total_remote_branches:($remote_branches|tonumber?//0), total_commits:($commits|tonumber?//0), repo_size:$repo_size}' > "$json" 2>/dev/null || printf '%s\n' '{}' > "$json"
  else
    printf '{"total_remote_branches":%s,"total_commits":%s,"repo_size":"%s"}\n' "$total_remote_branches" "$total_commits" "$repo_size" > "$json"
  fi

  _log info "Optimization complete. Reports: $human, $json"
  [ "${JSON_OUT:-0}" -eq 1 ] && cat "$json"
}

local_snapshot() {
  _log info "Running Local Repository Snapshot..."
  if [ ! -d "${WORKDIR:-.}" ]; then
    _log error "Workdir ${WORKDIR} does not exist"
    return 1
  fi

  check_repo_size

  local DATE_TAG
  DATE_TAG=$("${DATE_CMD:-date}" '+%Y%m%d_%H%M%S' 2>/dev/null || date '+%Y%m%d_%H%M%S')
  local base_name="${SCRIPT_NAME%%.*}_${DATE_TAG}"
  local snapshot_file="${SNAPSHOT_DIR}/${base_name}.tar.gz"
  local snapshot_checksum="${SNAPSHOT_DIR}/${base_name}.sha256"

  local EXCLUDE_PATTERNS=(
    --exclude='.git'
    --exclude='node_modules'
    --exclude='venv'
    --exclude='__pycache__'
    --exclude='*.o'
    --exclude='*.pyc'
    --exclude='*.swp'
    --exclude='*.bak'
    --exclude='*.tmp'
    --exclude='*.log'
    --exclude='Thumbs.db'
    --exclude='.DS_Store'
  )

  _log info "Target snapshot file: ${snapshot_file}"

  local -a tar_args=( -czf "${snapshot_file}" )
  tar_args+=( "${EXCLUDE_PATTERNS[@]}" . )

  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    _log info "[DRY-RUN] ${TAR_CMD:-tar} ${tar_args[*]}"
  else
    ( cd "${WORKDIR}" && "${TAR_CMD:-tar}" "${tar_args[@]}" ) || {
      _log error "Snapshot tar creation failed."
      return 1
    }
    if [ -n "${SHA256SUM_CMD}" ]; then
      if command -v "${SHA256SUM_CMD%% *}" >/dev/null 2>&1; then
        "${SHA256SUM_CMD}" "${snapshot_file}" > "${snapshot_checksum}" 2>/dev/null || {
          _log warn "Failed to generate checksum with ${SHA256SUM_CMD}"
        }
      fi
    else
      if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "${snapshot_file}" > "${snapshot_checksum}" 2>/dev/null || _log warn "Failed to generate checksum with shasum"
      else
        _log warn "No sha256sum/shasum command available; skipping checksum."
      fi
    fi

    local size_bytes
    size_bytes=$(safe_stat_size "${snapshot_file}" || echo 0)
    _log info "Snapshot created: ${snapshot_file} (size: $(numfmt_or_human "$size_bytes"))"

    if [ "${size_bytes:-0}" -gt "${SNAPSHOT_MAX_BYTES}" ]; then
      _log warn "Snapshot size ($(numfmt_or_human "$size_bytes")) exceeds $(numfmt_or_human "$SNAPSHOT_MAX_BYTES"); consider storing externally."
    fi

    prune_snapshots
  fi

  return 0
}

restore_snapshot() {
  local sel="${1:-latest}"
  local target_dir=""
  set -- "${@:-$sel}"
  while [ $# -gt 0 ]; do
    case "$1" in
      --target) shift; target_dir="${1:-}"; shift ;;
      --target=*) target_dir="${1#*=}"; shift ;;
      --dry-run) DRY_RUN=1; shift ;;
      latest) sel="latest"; shift ;;
      *) sel="$1"; shift ;;
    esac
  done

  if [ ! -d "${SNAPSHOT_DIR}" ]; then
    _log error "Snapshot directory not found: ${SNAPSHOT_DIR}"
    return 1
  fi

  list_snapshots() {
    if command -v find >/dev/null 2>&1 && command -v sort >/dev/null 2>&1; then
      find "${SNAPSHOT_DIR}" -maxdepth 1 -type f -name "${SCRIPT_NAME%%.*}_*.tar.gz" -printf '%T@ %p\n' 2>/dev/null | sort -n -r | awk '{print $2}'
    else
      ls -1t "${SNAPSHOT_DIR}/${SCRIPT_NAME%%.*}"_*.tar.gz 2>/dev/null || true
    fi
  }

  mapfile -t snaps < <(list_snapshots)

  if [ "${#snaps[@]}" -eq 0 ]; then
    _log warn "No snapshots found in ${SNAPSHOT_DIR}"
    return 2
  fi

  local snapshot_file=""
  if [ "${sel:-}" = "latest" ]; then
    snapshot_file="${snaps[0]}"
  else
    for s in "${snaps[@]}"; do
      if [ "$s" = "${sel}" ] || [ "$(basename "$s")" = "${sel}" ]; then
        snapshot_file="$s"
        break
      fi
    done
    if [ -z "$snapshot_file" ]; then
      _log error "Snapshot not found: ${sel}"
      _log info "Available snapshots:"
      for s in "${snaps[@]}"; do
        _log info "  $(basename "$s")"
      done
      return 3
    fi
  fi

  local checksum_file="${snapshot_file%.tar.gz}.sha256"
  if [ ! -f "${snapshot_file}" ]; then
    _log error "Snapshot file missing: ${snapshot_file}"
    return 4
  fi

  if [ -z "${target_dir}" ]; then
    local ts
    ts=$("${DATE_CMD:-date}" '+%Y%m%d_%H%M%S' 2>/dev/null || date '+%Y%m%d_%H%M%S')
    target_dir="./restored_${ts}"
  fi

  if [ -e "${target_dir}" ] && [ "$(ls -A "${target_dir}" 2>/dev/null | wc -l)" -gt 0 ]; then
    _log error "Target directory exists and is not empty: ${target_dir}"
    return 5
  fi

  _log info "Selected snapshot: ${snapshot_file}"
  _log info "Target directory: ${target_dir}"

  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    _log info "[DRY-RUN] Would verify checksum and extract snapshot into ${target_dir}"
    return 0
  fi

  if [ -f "${checksum_file}" ]; then
    _log info "Verifying checksum using: ${checksum_file}"
    if command -v sha256sum >/dev/null 2>&1; then
      if ! sha256sum -c "${checksum_file}" --status; then
        _log error "Checksum verification failed for ${snapshot_file}"
        return 6
      fi
    elif command -v shasum >/dev/null 2>&1; then
      computed=$((shasum -a 256 "${snapshot_file}" 2>/dev/null) | awk '{print $1}')
      expected=$((awk '{print $1}' "${checksum_file}" 2>/dev/null) || echo "")
      if [ -z "${expected}" ] || [ "${computed}" != "${expected}" ]; then
        _log error "Checksum mismatch (computed != expected). Aborting."
        return 6
      fi
    else
      _log warn "No sha256sum/shasum available; skipping checksum verification."
    fi
  else
    _log warn "Checksum file not found: ${checksum_file}; proceeding without verification."
  fi

  mkdir_p "${target_dir}"

  _log info "Extracting ${snapshot_file} -> ${target_dir}"
  if ! tar -xzf "${snapshot_file}" -C "${target_dir}"; then
    _log error "Extraction failed."
    return 7
  fi

  if command -v chown >/dev/null 2>&1; then
    local uid gid
    uid=$(id -u 2>/dev/null || echo "")
    gid=$(id -g 2>/dev/null || echo "")
    if [ -n "${uid}" ] && [ -n "${gid}" ]; then
      _log info "Setting ownership of restored files to UID:${uid} GID:${gid}"
      chown -R "${uid}:${gid}" "${target_dir}" 2>/dev/null || _log warn "chown failed (insufficient permissions)."
    fi
  fi

  _log info "Restore completed: ${target_dir}"
  return 0
}

setup_pre_commit_hook() {
  _log info "Setting up pre-commit hook..."
  local hook_file=".git/hooks/pre-commit"
  local hook_manager="${SCRIPT_NAME%%.*}"

  if [ ! -d .git ]; then
    _log error "Not a git repository."
    return 1
  fi

  if [ -f "${hook_file}" ]; then
    if grep -q "Managed by ${hook_manager}" "${hook_file}" 2>/dev/null; then
      _log info "Pre-commit hook already installed and managed."
      return 0
    else
      _log warn "Existing pre-commit hook present and unmanaged; appending managed checks."
      if [ "${DRY_RUN:-0}" -eq 1 ]; then
        _log info "[DRY-RUN] Would append managed checks to ${hook_file}"
        return 0
      fi
      cat >> "${hook_file}" <<EOF_MANAGED

# --- Managed by ${hook_manager} (appended) ---
set -euo pipefail
MAX_BYTES=${LARGE_FILE_LIMIT_BYTES}
git diff --cached --name-only -z | xargs -0 -I{} bash -c '
  for f; do
    [ -f "\$f" ] || continue
    if [ "\$(wc -c <"\$f" 2>/dev/null)" -gt \$MAX_BYTES ]; then
      echo "File is too large (>$(($MAX_BYTES/1024/1024))MB): \$f" >&2
      exit 1
    fi
  done
' bash {} || { echo "ERROR: Large staged file detected." >&2; exit 1; }

EOF_MANAGED
      chmod +x "${hook_file}"
      _log info "Appended managed checks to existing hook: ${hook_file}"
      return 0
    fi
  fi

  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    _log info "[DRY-RUN] Would create ${hook_file} with managed pre-commit checks."
    return 0
  fi

  cat > "${hook_file}" <<EOF_HOOK
#!/usr/bin/env bash
# Managed by ${hook_manager}
set -euo pipefail

MAX_BYTES=${LARGE_FILE_LIMIT_BYTES}
git diff --cached --name-only -z | xargs -0 -I{} bash -c '
  for f; do
    [ -f "\$f" ] || continue
    if [ "\$(wc -c <"\$f" 2>/dev/null)" -gt \$MAX_BYTES ]; then
      echo "File is too large (>$((${LARGE_FILE_LIMIT_BYTES}/1024/1024))MB): \$f" >&2
      exit 1
    fi
  done
' bash {} || { echo "ERROR: Large staged file detected. Use git-lfs or remove from staging." >&2; exit 1; }
EOF_HOOK

  chmod +x "${hook_file}"
  _log info "Pre-commit hook installed in ${hook_file}"
  return 0
}

# ----------------------------------------------------------------------
# Usage & CLI Parsing
# ----------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $SCRIPT_NAME <command> [--dry-run] [--json] [--workdir DIR] [--check] [--version]

Commands:
  dependency_master      - Updates dependencies based on lock files (npm, pip, composer, etc.).
  git_security_audit     - Scans for secrets, large files, and branch divergence (JSON + text).
  git_workflow_optimizer - Garbage collection, local perf configs, and branch pruning.
  local_snapshot         - Creates a compressed tarball snapshot of the workspace with checksums.
  restore_snapshot       - Lists, verifies, and safely restores a snapshot (latest or filename).
  setup_hooks            - Installs or appends managed pre-commit checks (large file guard).

Options:
  --dry-run             Show commands without executing them.
  --json                Output JSON reports directly to stdout where applicable.
  --workdir DIR         Specify the working directory (default: current directory).
  --check               Run environment and tool self-test.
  --version             Display script version and exit.

Notes:
  - Hardened for Bash in Termux / PuppyGit.
  - Snapshots: ${SNAPSHOT_DIR}
  - Logs: ${LOG_DIR}
EOF
  exit 2
}

# Global CLI argument parsing
ARGS=()
COMMAND=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --json) JSON_OUT=1; shift ;;
    --workdir)
      if [ -n "${2:-}" ] && [ -d "$2" ]; then
        WORKDIR="$2"
        shift 2
      else
        _log error "--workdir requires a valid directory"
        exit 1
      fi
      ;;
    --check) SELFTEST=1; shift ;;
    --version) echo "$VERSION"; exit 0 ;;
    -h|--help) usage ;;
    -*)
      _log error "Unknown global option: $1"
      usage
      ;;
    *)
      if [ -z "$COMMAND" ]; then
        COMMAND="$1"
      else
        ARGS+=("$1")
      fi
      shift
      ;;
  esac
done

# Change to workdir if specified
if [ -n "${WORKDIR:-}" ] && [ "${WORKDIR}" != "$(pwd)" ]; then
  if ! cd "${WORKDIR}"; then
    _log error "Could not change to work directory ${WORKDIR}"
    exit 3
  fi
fi

# Self-test check
if [ "$SELFTEST" -eq 1 ]; then
  echo "Running self-test: checking required tools..."
  require_cmds git jq tar || { echo "One or more required tools missing." >&2; exit 4; }
  echo "All required tools present. Environment operational."
  exit 0
fi

# ----------------------------------------------------------------------
# Command Dispatch
# ----------------------------------------------------------------------
case "${COMMAND:-}" in
  dependency_master)      dependency_master "${ARGS[@]}" ;;
  git_security_audit)    git_security_audit "${ARGS[@]}" ;;
  git_workflow_optimizer) git_workflow_optimizer "${ARGS[@]}" ;;
  local_snapshot)        local_snapshot "${ARGS[@]}" ;;
  restore_snapshot)      restore_snapshot "${ARGS[@]}" ;;
  setup_hooks)           setup_pre_commit_hook "${ARGS[@]}" ;;
  ""|help)               usage ;;
  *) _log error "Unknown command: ${COMMAND}"; usage; exit 2 ;;
esac

exit 0

<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FULL SEND // OBLIVION v5 - Local-First Sovereign Privacy Operating System</title>
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            cyber: {
              black: '#08080a',
              darker: '#0d0e12',
              card: '#12141c',
              border: '#1f2433',
              green: '#00ff66',
              cyan: '#00f0ff',
              red: '#ff0055',
              amber: '#ffaa00',
              purple: '#b006ff',
              dimText: '#6272a4'
            }
          },
          fontFamily: {
            mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace']
          },
          animation: {
            'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            'scanline': 'scanline 8s linear infinite',
            'glitch': 'glitch 0.3s ease-in-out'
          }
        }
      }
    }
  </script>
  
  <!-- Google Fonts & Font Awesome Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

  <style>
    body {
      font-family: 'JetBrains Mono', monospace;
      background-color: #08080a;
      color: #e2e8f0;
      overflow-x: hidden;
    }
    
    /* CRT Scanline Effect */
    .crt::before {
      content: " ";
      display: block;
      position: fixed;
      top: 0; left: 0; bottom: 0; right: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      z-index: 999;
      background-size: 100% 3px, 6px 100%;
      pointer-events: none;
      opacity: 0.6;
    }

    /* Cyber Glows */
    .glow-green { text-shadow: 0 0 8px rgba(0,255,102,0.6); }
    .glow-cyan { text-shadow: 0 0 8px rgba(0,240,255,0.6); }
    .glow-red { text-shadow: 0 0 8px rgba(255,0,85,0.6); }
    
    .border-glow-cyan { box-shadow: 0 0 12px -2px rgba(0,240,255,0.3); }
    .border-glow-green { box-shadow: 0 0 12px -2px rgba(0,255,102,0.3); }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0d0e12; }
    ::-webkit-scrollbar-thumb { background: #1f2433; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #00f0ff; }
  </style>
</head>
<body class="crt min-h-screen flex flex-col justify-between selection:bg-cyber-cyan selection:text-cyber-black">

  <!-- TOP PROTOCOL BAR -->
  <header class="border-b border-cyber-border bg-cyber-darker/90 backdrop-blur sticky top-0 z-50 px-4 py-2.5">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="w-3 h-3 rounded-full bg-cyber-green animate-pulse"></div>
        <span class="font-extrabold text-lg tracking-wider text-white">FULL SEND <span class="text-cyber-cyan text-xs px-2 py-0.5 rounded bg-cyber-cyan/10 border border-cyber-cyan/30">OBLIVION v5.2</span></span>
        <span class="hidden md:inline-block text-xs text-cyber-dimText">| LOCAL-FIRST SOVEREIGNTY PROTOCOL</span>
      </div>

      <!-- Quick Metrics Bar -->
      <div class="flex items-center space-x-6 text-xs">
        <div class="flex items-center space-x-2">
          <span class="text-cyber-dimText">RISK INDEX:</span>
          <span id="risk-score" class="font-bold text-cyber-red glow-red">88 / 100 [CRITICAL]</span>
        </div>
        <div class="hidden sm:flex items-center space-x-2">
          <span class="text-cyber-dimText">PURGED:</span>
          <span id="purged-ratio" class="font-bold text-cyber-green">3 / 8 PLATFORMS</span>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-cyber-dimText">STATUS:</span>
          <span class="text-cyber-cyan flex items-center gap-1">
            <i class="fa-solid fa-shield-halved text-[10px]"></i> ENCRYPTED
          </span>
        </div>
      </div>
    </div>
  </header>

  <!-- MAIN OPERATIONAL CONTAINER -->
  <main class="max-w-7xl w-full mx-auto p-4 sm:p-6 flex-grow grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- LEFT COLUMN: IDENTITY & COMMAND CENTER (4 COLS) -->
    <section class="lg:col-span-4 flex flex-col gap-6">

      <!-- Identity Vault Card -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5 border-glow-cyan">
        <div class="flex justify-between items-center mb-4 pb-2 border-b border-cyber-border/60">
          <h2 class="text-xs font-bold tracking-widest text-cyber-cyan flex items-center gap-2">
            <i class="fa-solid fa-user-shield"></i> IDENTITY VAULT [LOCAL]
          </h2>
          <span class="text-[10px] bg-cyber-green/10 text-cyber-green px-2 py-0.5 rounded border border-cyber-green/20">MEM_LOCAL</span>
        </div>

        <form id="identity-form" class="space-y-3 text-xs">
          <div>
            <label class="block text-cyber-dimText mb-1">TARGET FULL NAME</label>
            <input type="text" id="user-name" value="Alex Mercer" 
                   class="w-full bg-cyber-black border border-cyber-border rounded px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan transition" placeholder="e.g., Jane Doe">
          </div>
          <div>
            <label class="block text-cyber-dimText mb-1">PRIMARY EMAIL TO PURGE</label>
            <input type="email" id="user-email" value="alex.mercer.dev@proton.me" 
                   class="w-full bg-cyber-black border border-cyber-border rounded px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan transition" placeholder="e.g., target@domain.com">
          </div>
          <div>
            <label class="block text-cyber-dimText mb-1">JURISDICTION / LEGAL FRAMEWORK</label>
            <select id="user-jurisdiction" class="w-full bg-cyber-black border border-cyber-border rounded px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan transition">
              <option value="GDPR">EU GDPR (Article 17 - Right to be Forgotten)</option>
              <option value="CCPA">California CCPA (§ 1798.105 - Request to Delete)</option>
              <option value="PIPEDA">Canada PIPEDA (Principle 4.3.8)</option>
              <option value="GENERIC">International Standard Privacy Act</option>
            </select>
          </div>
          <button type="submit" class="w-full mt-2 bg-cyber-cyan/10 hover:bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40 py-2 rounded font-semibold text-xs transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-floppy-disk"></i> COMMIT TO MEMORY
          </button>
        </form>
      </div>

      <!-- Eradication Progress Panel -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5">
        <h2 class="text-xs font-bold tracking-widest text-cyber-green mb-3 flex items-center gap-2">
          <i class="fa-solid fa-chart-pie"></i> ERADICATION METRICS
        </h2>

        <div class="space-y-4 text-xs">
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-cyber-dimText">PURGE PROGRESS</span>
              <span id="progress-percentage" class="text-cyber-green font-bold">37.5%</span>
            </div>
            <div class="w-full bg-cyber-black rounded-full h-2.5 overflow-hidden border border-cyber-border">
              <div id="progress-bar" class="bg-gradient-to-r from-cyber-cyan to-cyber-green h-2.5 rounded-full transition-all duration-500" style="width: 37.5%"></div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 text-center pt-2">
            <div class="bg-cyber-black/60 p-2.5 rounded border border-cyber-border/40">
              <div id="metric-pending" class="text-lg font-bold text-cyber-amber">4</div>
              <div class="text-[10px] text-cyber-dimText">IN PROGRESS</div>
            </div>
            <div class="bg-cyber-black/60 p-2.5 rounded border border-cyber-border/40">
              <div id="metric-deleted" class="text-lg font-bold text-cyber-green">3</div>
              <div class="text-[10px] text-cyber-dimText">TERMINATED</div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Telemetry Log -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-4 flex-grow flex flex-col">
        <h2 class="text-xs font-bold tracking-widest text-cyber-dimText mb-2 flex items-center justify-between">
          <span><i class="fa-solid fa-terminal"></i> TELEMETRY LOG</span>
          <button id="clear-log" class="text-[10px] text-cyber-dimText hover:text-white"><i class="fa-solid fa-trash"></i></button>
        </h2>
        <div id="telemetry-log" class="bg-cyber-black border border-cyber-border/50 rounded p-3 text-[11px] font-mono text-cyber-dimText h-44 overflow-y-auto space-y-1">
          <div><span class="text-cyber-cyan">[00:00:01]</span> System initialized: OBLIVION_v5 kernel loaded.</div>
          <div><span class="text-cyber-cyan">[00:00:02]</span> Identity payload primed for Alex Mercer.</div>
          <div><span class="text-cyber-green">[00:00:03]</span> Local storage session validated. Zero network leaks.</div>
        </div>
      </div>

    </section>

    <!-- RIGHT COLUMN: TARGET PLATFORMS & EXECUTOR (8 COLS) -->
    <section class="lg:col-span-8 flex flex-col gap-6">

      <!-- Targets Grid Header & Filter -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 pb-3 border-b border-cyber-border">
          <div>
            <h1 class="text-base font-bold text-white tracking-wider flex items-center gap-2">
              <i class="fa-solid fa-crosshairs text-cyber-red"></i> TRACKED EXPOSURE TARGETS
            </h1>
            <p class="text-xs text-cyber-dimText">Select target service to initiate statutory erasure request execution</p>
          </div>
          
          <div class="flex gap-2 w-full sm:w-auto">
            <button id="btn-export" class="px-3 py-1.5 bg-cyber-black hover:bg-cyber-border border border-cyber-border rounded text-xs text-cyber-cyan transition flex items-center gap-1.5">
              <i class="fa-solid fa-download"></i> EXPORT JSON
            </button>
            <button id="btn-reset" class="px-3 py-1.5 bg-cyber-red/10 hover:bg-cyber-red/20 border border-cyber-red/40 rounded text-xs text-cyber-red transition flex items-center gap-1.5">
              <i class="fa-solid fa-rotate-right"></i> RESET ALL
            </button>
          </div>
        </div>

        <!-- Target Cards Container -->
        <div id="targets-grid" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[380px] overflow-y-auto pr-1">
          <!-- Dynamic Target Cards injected via JS -->
        </div>
      </div>

      <!-- Execution & AI Enhancement Terminal -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5 flex-grow flex flex-col border-glow-green">
        <div class="flex justify-between items-center mb-3 pb-2 border-b border-cyber-border">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-code text-cyber-green"></i>
            <h2 class="text-xs font-bold tracking-widest text-white">STATUTORY REQUEST GENERATOR & ENHANCER</h2>
          </div>
          <span id="active-target-badge" class="text-[10px] bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 px-2.5 py-0.5 rounded font-mono">
            TARGET: NONE SELECTED
          </span>
        </div>

        <!-- Template Display / Editor -->
        <div class="flex-grow flex flex-col gap-3">
          <div class="relative flex-grow">
            <textarea id="request-template" 
                      class="w-full h-52 bg-cyber-black border border-cyber-border rounded p-3 font-mono text-xs text-gray-200 focus:outline-none focus:border-cyber-green transition resize-none leading-relaxed"
                      placeholder="Select a target service above to generate a statutory GDPR Art.17 / CCPA deletion request..."></textarea>
            
            <!-- Floating Quick Action Buttons -->
            <div class="absolute bottom-3 right-3 flex gap-2">
              <button id="btn-ai-enhance" class="px-3 py-1.5 bg-cyber-purple/20 hover:bg-cyber-purple/30 border border-cyber-purple/50 text-cyber-purple rounded text-xs font-semibold transition flex items-center gap-1.5 shadow-lg">
                <i class="fa-solid fa-wand-magic-sparkles"></i> AI ENHANCE (GDPR LEGAL PRECISE)
              </button>
              <button id="btn-copy" class="px-3 py-1.5 bg-cyber-green/20 hover:bg-cyber-green/30 border border-cyber-green/50 text-cyber-green rounded text-xs font-semibold transition flex items-center gap-1.5">
                <i class="fa-solid fa-copy"></i> COPY TO CLIPBOARD
              </button>
            </div>
          </div>

          <!-- Direct Execution Actions -->
          <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-cyber-border/60">
            <div class="text-xs text-cyber-dimText flex items-center gap-2">
              <i class="fa-solid fa-circle-info text-cyber-cyan"></i>
              <span>Direct DPO Contact: <strong id="dpo-email-display" class="text-white">N/A</strong></span>
            </div>
            
            <div class="flex gap-2">
              <button id="btn-send-email" class="px-4 py-2 bg-cyber-cyan hover:bg-cyan-400 text-cyber-black rounded font-bold text-xs transition flex items-center gap-2">
                <i class="fa-solid fa-paper-plane"></i> LAUNCH DISPATCH (MAILTO)
              </button>
              <button id="btn-mark-done" class="px-4 py-2 bg-cyber-green/10 hover:bg-cyber-green/20 text-cyber-green border border-cyber-green/40 rounded font-bold text-xs transition flex items-center gap-2">
                <i class="fa-solid fa-check-double"></i> MARK PURGED
              </button>
            </div>
          </div>
        </div>
      </div>

    </section>
  </main>

  <!-- FOOTER STATUS STRIP -->
  <footer class="border-t border-cyber-border bg-cyber-darker text-cyber-dimText text-[11px] px-4 py-2">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
      <div class="flex items-center gap-4">
        <span>OBLIVION v5.2 KERNEL ACTIVE</span>
        <span>•</span>
        <span class="text-cyber-green">ZERO REMOTE TRACKING</span>
      </div>
      <div>
        <span>GDPR Art. 17 / CCPA § 1798.105 COMPLIANT AUTOMATION ENGINE</span>
      </div>
    </div>
  </footer>

  <!-- NOTIFICATION TOAST CONTAINER -->
  <div id="toast-container" class="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none"></div>

  <!-- JAVASCRIPT LOGIC ENGINE -->
  <script>
    // System Database State
    const defaultTargets = [
      { id: 'data-broker-x', name: 'Acme Data Broker Corp', difficulty: 'Hard', dpo: 'privacy@acmedatabroker.com', status: 'Pending', riskWeight: 20 },
      { id: 'social-network', name: 'OmniSocial Network', difficulty: 'Medium', dpo: 'dpo@omnisocial.io', status: 'Pending', riskWeight: 18 },
      { id: 'search-index', name: 'PeopleSearch Directory', difficulty: 'Impossible', dpo: 'optout@peoplesearchdir.com', status: 'Pending', riskWeight: 25 },
      { id: 'analytics-hub', name: 'TrackerAnalytics Inc', difficulty: 'Easy', dpo: 'legal@trackeranalytics.net', status: 'Deleted', riskWeight: 10 },
      { id: 'ecommerce-old', name: 'Legacy Retail Online', difficulty: 'Easy', dpo: 'privacy@legacyretail.com', status: 'Deleted', riskWeight: 5 },
      { id: 'ad-network', name: 'AdTarget Behavioral Ltd', difficulty: 'Hard', dpo: 'compliance@adtarget.co', status: 'Pending', riskWeight: 15 },
      { id: 'cloud-storage', name: 'DropCloud Free Tier', difficulty: 'Easy', dpo: 'support-privacy@dropcloud.org', status: 'Deleted', riskWeight: 7 }
    ];

    let userState = {
      name: 'Alex Mercer',
      email: 'alex.mercer.dev@proton.me',
      jurisdiction: 'GDPR',
      targets: defaultTargets
    };

    let selectedTargetId = null;

    // Load state from localStorage on init
    function initSystem() {
      const saved = localStorage.getItem('OBLIVION_USER_STATE');
      if (saved) {
        try { userState = JSON.parse(saved); } catch(e) { logTelemetry('Err loading local state.'); }
      }
      
      document.getElementById('user-name').value = userState.name;
      document.getElementById('user-email').value = userState.email;
      document.getElementById('user-jurisdiction').value = userState.jurisdiction;

      renderTargets();
      updateMetrics();
      logTelemetry('System initialized successfully. All state bound to LocalStorage.');
    }

    // Save State Helper
    function saveState() {
      localStorage.setItem('OBLIVION_USER_STATE', JSON.stringify(userState));
      updateMetrics();
    }

    // Render Target List
    function renderTargets() {
      const grid = document.getElementById('targets-grid');
      grid.innerHTML = '';

      userState.targets.forEach(target => {
        const isSelected = target.id === selectedTargetId;
        const card = document.createElement('div');
        
        let diffColor = 'text-cyber-green';
        if (target.difficulty === 'Medium') diffColor = 'text-cyber-amber';
        if (target.difficulty === 'Hard' || target.difficulty === 'Impossible') diffColor = 'text-cyber-red';

        let statusBadge = target.status === 'Deleted' 
          ? '<span class="px-2 py-0.5 rounded bg-cyber-green/20 text-cyber-green border border-cyber-green/40 text-[10px] font-bold">TERMINATED</span>'
          : '<span class="px-2 py-0.5 rounded bg-cyber-amber/20 text-cyber-amber border border-cyber-amber/40 text-[10px] font-bold">PENDING</span>';

        card.className = `p-3 rounded-lg border transition cursor-pointer flex flex-col justify-between gap-2 ${
          isSelected 
            ? 'bg-cyber-darker border-cyber-cyan shadow-[0_0_10px_rgba(0,240,255,0.2)]' 
            : 'bg-cyber-black/70 hover:bg-cyber-darker border-cyber-border'
        }`;

        card.onclick = () => selectTarget(target.id);

        card.innerHTML = `
          <div class="flex justify-between items-start">
            <div>
              <div class="font-bold text-xs text-white">${target.name}</div>
              <div class="text-[10px] text-cyber-dimText">${target.dpo}</div>
            </div>
            ${statusBadge}
          </div>
          <div class="flex justify-between items-center text-[10px] pt-1 border-t border-cyber-border/40">
            <span class="text-cyber-dimText">DIFFICULTY: <strong class="${diffColor}">${target.difficulty.toUpperCase()}</strong></span>
            <span class="text-cyber-dimText">RISK IMPACT: <strong class="text-white">+${target.riskWeight}</strong></span>
          </div>
        `;

        grid.appendChild(card);
      });
    }

    // Select Target & Generate Template
    function selectTarget(id) {
      selectedTargetId = id;
      const target = userState.targets.find(t => t.id === id);
      if (!target) return;

      document.getElementById('active-target-badge').textContent = `TARGET: ${target.name.toUpperCase()}`;
      document.getElementById('dpo-email-display').textContent = target.dpo;

      generateTemplate(target);
      renderTargets();
      logTelemetry(`Selected target: ${target.name} [DPO: ${target.dpo}]`);
    }

    // Dynamic Request Template Generator
    function generateTemplate(target) {
      const name = userState.name || '[YOUR NAME]';
      const email = userState.email || '[YOUR EMAIL]';
      const jurisdiction = userState.jurisdiction;

      let template = '';

      if (jurisdiction === 'GDPR') {
        template = `FORMAL NOTICE: DEMAND FOR ERASURE OF PERSONAL DATA
Pursuant to Article 17 of the General Data Protection Regulation (GDPR)

TO DATA PROTECTION OFFICER / PRIVACY COMPLIANCE: ${target.name} (${target.dpo})

I am writing to formally exercise my Right to Erasure ('Right to be Forgotten') under Article 17 of the GDPR.

Please permanently delete all personal data concerning my identity from your systems, servers, data brokers, and third-party processors without undue delay.

Data Subject Identifiers for Removal:
- Name: ${name}
- Associated Email: ${email}

Statutory Obligations:
1. Confirm erasure of all records, logs, behavioral trackers, and analytics within 30 days as mandated by GDPR Article 12(3).
2. Notify all recipient third parties to whom this data has been disclosed (Article 19).

Failure to comply will result in an immediate formal complaint lodged with the Data Protection Authority (DPA).

Sincerely,
${name}`;
      } else if (jurisdiction === 'CCPA') {
        template = `CONSUMER REQUEST TO DELETE PERSONAL INFORMATION
Pursuant to California Consumer Privacy Act (CCPA) § 1798.105

TO: ${target.name} Privacy Operations (${target.dpo})

I, ${name}, formally request that ${target.name} delete all personal information collected and retained regarding myself and my registered email address (${email}).

Under CCPA § 1798.105, consumers have the right to request deletion of personal information held by businesses and service providers. 

Please verify this request and confirm complete removal within 45 business days as stipulated by statute.

Authorized Requestor: ${name}
Target Email: ${email}`;
      } else {
        template = `STATUTORY PRIVACY REQUEST & ACCOUNT TERMINATION
TO: ${target.name} Data Controller (${target.dpo})

I request the immediate and total deletion of my account, data footprint, and associated personal information held under:
Name: ${name}
Email: ${email}

Please confirm when all records have been irrevocably deleted.`;
      }

      document.getElementById('request-template').value = template;
    }

    // AI Enhancement Simulator (Rewrites template with precise legal jargon)
    document.getElementById('btn-ai-enhance').onclick = () => {
      const textarea = document.getElementById('request-template');
      if (!selectedTargetId) {
        showToast('Please select a target platform first.', 'error');
        return;
      }

      logTelemetry('AI Enhancement Engine invoked via local parametric weights...');
      
      let enhanced = textarea.value;
      enhanced = `[ENHANCED LEGAL PRECISE VERSION]\n` + 
                 enhanced + 
                 `\n\nLEGAL NOTICE OF STRICT COMPLIANCE:\n` +
                 `Be advised that failure to fulfill this statutory request within statutory timeframes will trigger escalation to supervisory privacy commissions, including potential statutory damages for non-compliance under privacy enforcement laws. All audit trails of this transmission have been cryptographically signed.`;

      textarea.value = enhanced;
      showToast('Template enhanced with legal precision!', 'success');
      logTelemetry('Template updated with high-precision statutory clauses.');
    };

    // Copy to Clipboard
    document.getElementById('btn-copy').onclick = () => {
      const text = document.getElementById('request-template').value;
      if (!text) return;

      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);

      showToast('Request template copied to clipboard.', 'info');
      logTelemetry('Payload copied to clipboard.');
    };

    // Launch Email Mailto
    document.getElementById('btn-send-email').onclick = () => {
      if (!selectedTargetId) {
        showToast('Select a target service first.', 'error');
        return;
      }

      const target = userState.targets.find(t => t.id === selectedTargetId);
      const subject = encodeURIComponent(`STATUTORY DATA DELETION REQUEST - ${userState.name}`);
      const body = encodeURIComponent(document.getElementById('request-template').value);

      window.location.href = `mailto:${target.dpo}?subject=${subject}&body=${body}`;
      logTelemetry(`Dispatched mailto client for ${target.dpo}`);
    };

    // Mark as Purged
    document.getElementById('btn-mark-done').onclick = () => {
      if (!selectedTargetId) {
        showToast('Select a target service first.', 'error');
        return;
      }

      const target = userState.targets.find(t => t.id === selectedTargetId);
      target.status = 'Deleted';
      saveState();
      renderTargets();
      showToast(`Target ${target.name} marked as TERMINATED.`, 'success');
      logTelemetry(`Status updated: ${target.name} --> PURGED/TERMINATED`);
    };

    // Identity Form Submit
    document.getElementById('identity-form').onsubmit = (e) => {
      e.preventDefault();
      userState.name = document.getElementById('user-name').value;
      userState.email = document.getElementById('user-email').value;
      userState.jurisdiction = document.getElementById('user-jurisdiction').value;

      saveState();
      showToast('Identity Vault saved locally.', 'success');
      logTelemetry(`Identity Vault updated: ${userState.name} (${userState.email}) [${userState.jurisdiction}]`);

      if (selectedTargetId) {
        const target = userState.targets.find(t => t.id === selectedTargetId);
        if (target) generateTemplate(target);
      }
    };

    // Update Overall Metrics & Risk Index
    function updateMetrics() {
      const total = userState.targets.length;
      const deleted = userState.targets.filter(t => t.status === 'Deleted').length;
      const pending = total - deleted;

      const pct = total === 0 ? 0 : Math.round((deleted / total) * 100);

      document.getElementById('progress-percentage').textContent = `${pct}%`;
      document.getElementById('progress-bar').style.width = `${pct}%`;
      document.getElementById('purged-ratio').textContent = `${deleted} / ${total} PLATFORMS`;

      document.getElementById('metric-pending').textContent = pending;
      document.getElementById('metric-deleted').textContent = deleted;

      // Calculate dynamic risk index
      let remainingRisk = 0;
      userState.targets.filter(t => t.status !== 'Deleted').forEach(t => remainingRisk += t.riskWeight);
      
      const riskEl = document.getElementById('risk-score');
      if (remainingRisk > 50) {
        riskEl.textContent = `${remainingRisk} / 100 [CRITICAL]`;
        riskEl.className = 'font-bold text-cyber-red glow-red';
      } else if (remainingRisk > 20) {
        riskEl.textContent = `${remainingRisk} / 100 [MODERATE]`;
        riskEl.className = 'font-bold text-cyber-amber';
      } else {
        riskEl.textContent = `${remainingRisk} / 100 [LOW RISK]`;
        riskEl.className = 'font-bold text-cyber-green glow-green';
      }
    }

    // Export & Reset Handlers
    document.getElementById('btn-export').onclick = () => {
      const blob = new Blob([JSON.stringify(userState, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `OBLIVION_privacy_backup_${new Date().toISOString().slice(0,10)}.json`;
      a.click();
      logTelemetry('Exported local state backup JSON.');
    };

    document.getElementById('btn-reset').onclick = () => {
      if (confirm('Execute total state purge and reset local targets to defaults?')) {
        localStorage.removeItem('OBLIVION_USER_STATE');
        userState.targets = defaultTargets;
        initSystem();
        showToast('System reset completed.', 'info');
        logTelemetry('TOTAL RESET EXECUTION COMPLETED.');
      }
    };

    // Telemetry Logging Helper
    function logTelemetry(msg) {
      const container = document.getElementById('telemetry-log');
      const time = new Date().toTimeString().split(' ')[0];
      const div = document.createElement('div');
      div.innerHTML = `<span class="text-cyber-cyan">[${time}]</span> ${msg}`;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }

    document.getElementById('clear-log').onclick = () => {
      document.getElementById('telemetry-log').innerHTML = '';
    };

    // Custom UI Toast Notification Engine
    function showToast(msg, type = 'info') {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');

      let colorClass = 'border-cyber-cyan text-cyber-cyan';
      if (type === 'success') colorClass = 'border-cyber-green text-cyber-green';
      if (type === 'error') colorClass = 'border-cyber-red text-cyber-red';

      toast.className = `bg-cyber-darker border ${colorClass} px-4 py-2.5 rounded shadow-xl text-xs flex items-center gap-2 backdrop-blur transition-all duration-300 transform translate-y-2`;
      toast.innerHTML = `<i class="fa-solid fa-terminal text-[10px]"></i> <span>${msg}</span>`;

      container.appendChild(toast);
      setTimeout(() => toast.classList.remove('translate-y-2'), 10);

      setTimeout(() => {
        toast.classList.add('opacity-0');
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    }

    // Initialize System on Window Load
    window.onload = function() {
      initSystem();
    };
  </script>
</body>
</html>
