#!/usr/bin/env bash
# Copy live research/workflow outputs from the scratchpad into dev-notes, then commit and push ONLY dev-notes.
SP=/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad
S=/root/.claude/projects/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a
cd /home/user/m || exit 1
python3 /home/user/m/dev-notes/progress.py >/dev/null 2>&1
cp $SP/brief/study/*.md dev-notes/study/ 2>/dev/null
cp $SP/brief/STUDY.md $SP/brief/ROADMAP.md dev-notes/study/ 2>/dev/null
cp $S/workflows/scripts/*.js dev-notes/workflows/ 2>/dev/null
for d in $S/subagents/workflows/wf_*; do [ -f $d/journal.jsonl ] && cp $d/journal.jsonl dev-notes/runs/$(basename $d)-journal.jsonl; done
git add dev-notes CLAUDE.md apex
if ! git diff --cached --quiet -- dev-notes CLAUDE.md apex; then
  git commit -q -m "dev-notes: sync research and workflow state

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01LHSxJrY7ayMCWKn7R95Bj9" -- dev-notes CLAUDE.md apex
  for i in 1 2 3 4; do git push -q -u origin claude/determined-lovelace-erktyz && break; sleep $((2**i)); done
fi
