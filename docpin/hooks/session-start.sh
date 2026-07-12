#!/bin/sh
# docpin SessionStart hook — LOCAL ONLY. Reads manifests, emits a version map.
# Never touches the network, never writes files, never errors the session.
set -u
root="${DOCPIN_ROOT:-$PWD}"
maxdeps=40
enabled=1

cfg="$root/.docpin/config.json"
if [ -f "$cfg" ]; then
  # Isolate the "hook" object's own braces so a "false"/"maxDeps" belonging to some
  # other object (e.g. "cache") can never be mistaken for the hook's own settings.
  hookobj=$(tr -d '\n' < "$cfg" 2>/dev/null | sed -n 's/.*"hook"[[:space:]]*:[[:space:]]*{\([^}]*\)}.*/\1/p')
  printf '%s' "$hookobj" | grep -q '"enabled"[[:space:]]*:[[:space:]]*false' && enabled=0
  md=$(printf '%s' "$hookobj" | grep -o '"maxDeps"[[:space:]]*:[[:space:]]*[0-9]\{1,\}' | grep -o '[0-9]\{1,\}' | head -1)
  [ -n "${md:-}" ] && maxdeps="$md"
fi
[ "$enabled" -eq 0 ] && exit 0

emit=""   # accumulated lines
add_line() { emit="${emit}$1
"; }

# --- npm: package.json dependencies + devDependencies ---
npm_deps() {
  f="$root/package.json"; [ -f "$f" ] || return 0
  # Use awk's record separator to split the file right at the opening brace of each
  # dependencies/devDependencies object. This works regardless of whether the JSON is
  # pretty-printed (multi-line) or minified (single-line), unlike a line-based state
  # machine which breaks when the whole object appears on one line.
  awk '
    BEGIN { RS="\"(dependencies|devDependencies)\"[[:space:]]*:[[:space:]]*\\{" }
    NR>1 {
      end = index($0, "}");
      body = (end>0) ? substr($0,1,end-1) : $0;
      n = split(body, pairs, ",");
      for (i=1;i<=n;i++) {
        p = pairs[i];
        colon = index(p, ":");
        if (colon>0) {
          rawv = substr(p,colon+1);
          gsub(/^[[:space:]]+/,"",rawv);
          # Only emit STRING-valued entries. An object value (nested "{...}") must never
          # produce a "name@{..." garbage line — skip it outright.
          if (rawv ~ /^\{/) continue;
          k = substr(p,1,colon-1); v = rawv;
          gsub(/"/,"",k); gsub(/"/,"",v);
          gsub(/^[[:space:]]+/,"",k); gsub(/[[:space:]]+$/,"",k);
          gsub(/[[:space:]]/,"",v);
          if (k!="") print k "@" v;
        }
      }
    }' "$f"
}
# --- PyPI: requirements.txt (name==ver / name>=ver) ---
pypi_deps() {
  f="$root/requirements.txt"; [ -f "$f" ] || { [ -f "$root/pyproject.toml" ] && f="$root/pyproject.toml" || return 0; }
  case "$f" in
    */requirements.txt)
      # awk, not sed: pip directive lines (-r/-e/-c/--index-url/...) are skipped outright;
      # extras (`name[extra]`) and environment markers (`; python_version < "3.11"`) are
      # stripped before matching; sole upper-bound constraints (< or <=) are reported as
      # a bare name (no misleading "pinned" version), while ==, ~=, >=, > keep their version.
      grep -v '^[[:space:]]*#' "$f" | grep -v '^[[:space:]]*$' | \
      awk '
        {
          line=$0;
          gsub(/^[[:space:]]+/,"",line);
          if (line ~ /^-/) next;               # pip directive (-r, -e, -c, --index-url, --hash, ...)
          sub(/#.*/,"",line);                   # inline comment
          sub(/;.*/,"",line);                   # environment marker
          gsub(/\[[^]]*\]/,"",line);            # extras, e.g. requests[security]
          gsub(/[[:space:]]/,"",line);          # remaining whitespace
          if (line=="") next;
          if (match(line,/(==|~=|>=|>)/)) {
            name=substr(line,1,RSTART-1);
            ver=substr(line,RSTART+RLENGTH);
            print name "@" ver;
            next;
          }
          if (match(line,/(<=|<)/)) {
            name=substr(line,1,RSTART-1);
            print name;
            next;
          }
          if (line ~ /^[A-Za-z0-9._-]+$/) print line;
        }' ;;
    */pyproject.toml)
      # pyproject.toml has two real dependency shapes; everything else in [project] or
      # [tool.poetry.*] is scalar metadata (name, version, requires-python, ...) that must
      # NEVER be emitted:
      #   PEP 621:  [project].dependencies = [ "pkg==1.0", ... ]   (an ARRAY, not a table)
      #   Poetry:   [tool.poetry.dependencies]  pkg = "^1.0"  /  pkg = { version = "1.0", ... }
      awk '
        function trim(s) { gsub(/^[[:space:]]+/,"",s); gsub(/[[:space:]]+$/,"",s); return s }
        # Parse one PEP 508 requirement string with the same rules as the requirements.txt
        # path: strip extras / environment markers, then a leading comparator for the
        # version, or bare name for a sole upper bound / no version at all.
        function emit_requirement(line,    name,ver) {
          sub(/#.*/,"",line);
          sub(/;.*/,"",line);
          gsub(/\[[^]]*\]/,"",line);
          gsub(/[[:space:]]/,"",line);
          if (line=="") return;
          if (match(line,/(==|~=|>=|>)/)) {
            name=substr(line,1,RSTART-1); ver=substr(line,RSTART+RLENGTH);
            sub(/,.*/,"",ver);            # drop any further comma-separated constraint (e.g. ",<3")
            print name "@" ver; return;
          }
          if (match(line,/(<=|<)/)) { print substr(line,1,RSTART-1); return; }
          if (line ~ /^[A-Za-z0-9._-]+$/) print line;
        }
        # Extract each quoted (double- or single-quoted) item from an array line/fragment,
        # emitting each as a requirement, and report whether the closing "]" was reached.
        # Quote-aware throughout: a comma or "]" INSIDE a quoted item (e.g. the extras
        # bracket in "requests[security]==2.31.0") is never mistaken for array syntax —
        # only a "]" OUTSIDE any quotes ends the array.
        function emit_array_items(s,    rest,qpos,qlen,bpos,it) {
          rest=s;
          for (;;) {
            qpos=match(rest,/"[^"]*"/) ? RSTART : 0; qlen=RLENGTH;
            if (qpos==0 && match(rest,/'"'"'[^'"'"']*'"'"'/)) { qpos=RSTART; qlen=RLENGTH; }
            bpos=index(rest,"]");
            if (bpos>0 && (qpos==0 || bpos<qpos)) return 1;   # unquoted "]" -> array closed
            if (qpos==0) return 0;                            # no more items, no close on this fragment
            # Capture RSTART/RLENGTH-derived positions into locals (qpos/qlen) BEFORE
            # calling emit_requirement(), whose own match() calls would otherwise
            # clobber the global RSTART/RLENGTH out from under this loop.
            it=substr(rest,qpos+1,qlen-2);
            rest=substr(rest,qpos+qlen);
            emit_requirement(it);
          }
        }
        /^\[project\]/{project=1; poetry=0; indeps=0; next}
        /^\[tool\.poetry\.dependencies\]/{poetry=1; project=0; indeps=0; next}
        /^\[/{project=0; poetry=0; indeps=0; next}

        # --- PEP 621: only the dependencies = [ ... ] array is a dependency list ---
        project && !indeps && /^dependencies[[:space:]]*=[[:space:]]*\[/{
          indeps=1;
          rest=$0; sub(/^[^\[]*\[/,"",rest);
          if (emit_array_items(rest)) indeps=0;
          next;
        }
        project && indeps {
          if (emit_array_items($0)) indeps=0;
          next;
        }
        project { next }  # any other [project] line (name, version, requires-python, ...) — ignore

        # --- Poetry: [tool.poetry.dependencies] pkg = "spec" | pkg = { version = "spec", ... } ---
        poetry && /=/{
          line=$0;
          eq=index(line,"=");
          key=trim(substr(line,1,eq-1));
          val=trim(substr(line,eq+1));
          if (key=="" || key=="python") next;
          if (val ~ /^\{/) {
            if (match(val,/version[[:space:]]*=[[:space:]]*"[^"]*"/)) {
              v=substr(val,RSTART,RLENGTH); sub(/^version[[:space:]]*=[[:space:]]*"/,"",v); sub(/"$/,"",v);
              sub(/^[\^~]/,"",v); sub(/^(==|~=|>=|<=|>|<)/,"",v); sub(/,.*/,"",v);
              if (v!="") print key "@" v;
            }
            next;
          }
          gsub(/"/,"",val);
          sub(/^[\^~]/,"",val); sub(/^(==|~=|>=|<=|>|<)/,"",val); sub(/,.*/,"",val);
          if (val!="") print key "@" val;
        }
      ' "$f" ;;
  esac
}
# --- crates: Cargo.toml [dependencies] (+ [dependencies.<name>] sub-tables) ---
crates_deps() {
  f="$root/Cargo.toml"; [ -f "$f" ] || return 0
  awk '
       /^\[dependencies\]/{ind=1;subname="";next}
       /^\[dependencies\.[A-Za-z0-9_-]+\]$/{
         ind=0;
         subname=$0; sub(/^\[dependencies\./,"",subname); sub(/\]$/,"",subname);
         next;
       }
       /^\[/{ind=0;subname=""}
       ind && /=/{
         line=$0; sub(/#.*/,"",line);
         if (match(line,/^[A-Za-z0-9._-]+[[:space:]]*=[[:space:]]*"[^"]+"/)) {
           name=line; sub(/[[:space:]]*=.*/,"",name);
           ver=line; sub(/^[^"]*"/,"",ver); sub(/".*/,"",ver);
           print name "@" ver;
         } else if (match(line,/version[[:space:]]*=[[:space:]]*"[^"]+"/)) {
           name=line; sub(/[[:space:]]*=.*/,"",name);
           ver=line; sub(/^.*version[[:space:]]*=[[:space:]]*"/,"",ver); sub(/".*/,"",ver);
           print name "@" ver;
         }
       }
       subname!="" && /=/{
         line=$0; sub(/#.*/,"",line);
         if (match(line,/^[[:space:]]*version[[:space:]]*=[[:space:]]*"[^"]+"/)) {
           ver=line; sub(/^.*version[[:space:]]*=[[:space:]]*"/,"",ver); sub(/".*/,"",ver);
           print subname "@" ver;
         }
       }' "$f"
}
# --- Go: go.mod require lines ---
go_deps() {
  f="$root/go.mod"; [ -f "$f" ] || return 0
  awk '/^require[[:space:]]*\(/{inb=1;next} inb&&/\)/{inb=0}
       inb && NF>=2 {print $1 "@" $2}
       /^require[[:space:]]+[^(]/{print $2 "@" $3}' "$f"
}

npm=$(npm_deps); py=$(pypi_deps); cr=$(crates_deps); go=$(go_deps)
[ -z "$npm$py$cr$go" ] && exit 0

add_line "docpin active — grounding library code against your installed versions."
detected=""
[ -n "$npm" ] && detected="$detected npm"
[ -n "$py" ]  && detected="$detected PyPI"
[ -n "$cr" ]  && detected="$detected crates"
[ -n "$go" ]  && detected="$detected Go"
add_line "Detected:${detected}"

fmt() { # eco-label  newline-list
  lab="$1"; list="$2"; [ -z "$list" ] && return 0
  shown=$(printf '%s\n' "$list" | sed '/^$/d' | head -n "$maxdeps" | tr '\n' ' ')
  total=$(printf '%s\n' "$list" | sed '/^$/d' | wc -l | tr -d ' ')
  extra=""; [ "$total" -gt "$maxdeps" ] && extra=" …(+$((total-maxdeps)) more)"
  add_line "$lab: ${shown}${extra}"
}
fmt "npm"    "$npm"
fmt "PyPI"   "$py"
fmt "crates" "$cr"
fmt "Go"     "$go"
add_line "Use /docs <library> [topic] for an explicit pull; otherwise I'll fetch version-matched docs before writing library code."

printf '%s' "$emit"
exit 0
