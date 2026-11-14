#!/usr/bin/env python3
"""PreToolUse guard for shell commands: denies anything permanent or outward-facing.

Reads the hook event on stdin. Prints a deny decision for a blocked command and
nothing for an allowed one. It always exits 0; the JSON on stdout is what blocks.
"""
import json
import re
import shlex
import subprocess
import sys

PROTECTED_BRANCHES = re.compile(r'^(main|master|trunk|develop|dev|prod|production|release([/-].*)?)$')
SHELLS = {'sh', 'bash', 'zsh', 'dash', 'ksh', 'fish'}
PREFIXES = {'env', 'command', 'builtin', 'exec', 'time', 'nice', 'nohup', 'stdbuf', 'timeout', 'xargs', 'rtk', 'proxy'}

GH_WRITES = {
    'pr': {'create', 'merge', 'close', 'comment', 'review', 'edit', 'ready', 'reopen', 'lock', 'unlock', 'update-branch'},
    'issue': {'create', 'close', 'comment', 'edit', 'reopen', 'delete', 'lock', 'unlock', 'transfer', 'pin', 'unpin', 'develop'},
    'repo': {'create', 'delete', 'edit', 'rename', 'archive', 'unarchive', 'fork', 'sync', 'deploy-key'},
    'release': {'create', 'delete', 'edit', 'upload', 'delete-asset'},
    'gist': {'create', 'delete', 'edit', 'rename'},
    'workflow': {'run', 'enable', 'disable'},
    'run': {'rerun', 'cancel', 'delete'},
    'label': {'create', 'delete', 'edit', 'clone'},
    'secret': {'set', 'delete'},
    'variable': {'set', 'delete'},
    'cache': {'delete'},
}
GLAB_WRITES = {
    'mr': {'create', 'merge', 'close', 'note', 'approve', 'revoke', 'update', 'reopen', 'delete', 'rebase'},
    'issue': {'create', 'close', 'note', 'update', 'reopen', 'delete'},
    'repo': {'create', 'delete', 'fork', 'archive', 'transfer'},
    'release': {'create', 'delete', 'upload'},
    'ci': {'run', 'retry', 'delete', 'trigger'},
}
PUBLISHERS = {'npm', 'yarn', 'pnpm', 'cargo', 'gem', 'poetry', 'conan', 'vcpkg'}
DEPLOYERS = {'vercel', 'netlify', 'fly', 'flyctl', 'heroku', 'serverless', 'sls', 'eb', 'gcloud', 'helm', 'ansible-playbook'}
DISK = {'dd', 'mkfs', 'fdisk', 'diskutil', 'shred', 'truncate', 'parted', 'wipefs'}

# Checked against the whole command, so text hidden inside quotes or a nested shell is still seen.
RAW_RULES = [
    (r'(^|[\s;&|(`])(sudo|doas)(\s|$)', 'running as root'),
    (r'\bgit\b[^;&|]*\bpush\b[^;&|]*(\s--force\b|\s--force-with-lease\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s--mirror\b)', 'force push'),
    (r'\bgit\b[^;&|]*\breset\b[^;&|]*\s--hard\b', 'git reset --hard'),
    (r'(^|[\s;&|(`])(Remove-Item|rm|ri|rd|rmdir|del|erase)\b[^;&|]*\s-(Recurse|r\b|Force)', 'recursive or forced delete'),
    (r'(^|[\s;&|(`])(rd|rmdir|del|erase)\s[^;&|]*/s\b', 'recursive delete'),
    (r'(^|[\s;&|(`])(format|Format-Volume|Clear-Disk)\s', 'disk-level command'),
]


def tokens_of(segment):
    try:
        return shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return segment.split()


def strip_prefixes(tokens):
    """Drops leading VAR=value assignments and wrappers such as env, time or xargs."""
    index = 0
    while index < len(tokens):
        token = tokens[index]
        name = token.rsplit('/', 1)[-1]
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', token) or name in PREFIXES or (index and token.startswith('-')):
            index += 1
        else:
            break
    return tokens[index:]


def current_branch(cwd):
    try:
        result = subprocess.run(['git', 'symbolic-ref', '--short', '-q', 'HEAD'], cwd=cwd or None,
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ''
    return result.stdout.strip()


def git_options_removed(tokens):
    """Returns the git subcommand and its arguments, skipping options such as -C <dir> before it."""
    index = 1
    while index < len(tokens) and tokens[index].startswith('-'):
        index += 2 if tokens[index] in ('-C', '-c', '--git-dir', '--work-tree', '--namespace') else 1
    return tokens[index:]


def check_git(tokens, cwd):
    arguments = git_options_removed(tokens)
    if not arguments:
        return None
    command, rest = arguments[0], arguments[1:]
    flags = [item for item in rest if item.startswith('-')]
    words = [item for item in rest if not item.startswith('-')]
    if command == 'push':
        if any(flag.startswith(('--force', '--mirror', '--delete', '--prune')) or re.match(r'^-[a-zA-Z]*[fd]', flag) for flag in flags):
            return 'force push or remote branch deletion'
        refspecs = words[1:]
        for refspec in refspecs:
            if refspec.startswith('+') or refspec.startswith(':'):
                return 'force push or remote branch deletion'
            target = refspec.rsplit(':', 1)[-1].removeprefix('refs/heads/')
            if PROTECTED_BRANCHES.match(target):
                return 'push to the protected branch ' + target
        if not refspecs or any(item in ('HEAD', '@') for item in refspecs):
            branch = current_branch(cwd)
            if PROTECTED_BRANCHES.match(branch):
                return 'push to the protected branch ' + branch
        if any(flag in ('--all', '--tags', '--follow-tags') for flag in flags):
            return 'push of every branch or tag'
        return None
    if command == 'reset' and '--hard' in flags:
        return 'git reset --hard discards uncommitted work'
    if command == 'clean' and any(re.match(r'^-[a-zA-Z]*f', flag) or flag == '--force' for flag in flags):
        return 'git clean deletes untracked files'
    if command == 'checkout' and ('--' in rest or '.' in words or any(flag in ('-f', '--force') for flag in flags)):
        return 'git checkout that discards uncommitted changes'
    if command == 'restore' and not ('--staged' in flags and '--worktree' not in flags and '-W' not in flags):
        return 'git restore discards uncommitted changes'
    if command == 'stash' and words[:1] in (['drop'], ['clear']):
        return 'git stash drop/clear'
    if command == 'branch' and any(flag in ('-D', '--delete', '-d') or re.match(r'^-[a-zA-Z]*[dD]', flag) for flag in flags):
        return 'branch deletion'
    if command == 'tag' and any(flag in ('-d', '--delete') for flag in flags):
        return 'tag deletion'
    if command in ('filter-branch', 'filter-repo'):
        return 'history rewrite'
    if command == 'reflog' and words[:1] in (['expire'], ['delete']):
        return 'reflog deletion'
    if command == 'gc' and any(flag.startswith('--prune') for flag in flags):
        return 'git gc --prune'
    if command == 'update-ref' and '-d' in flags:
        return 'ref deletion'
    if command == 'worktree' and words[:1] == ['remove'] and any(flag in ('-f', '--force') for flag in flags):
        return 'forced worktree removal'
    if command == 'remote' and words[:1] in (['remove'], ['rm'], ['set-url']):
        return 'remote change'
    return None


def check_forge(tokens, writes, name):
    words = [item for item in tokens[1:] if not item.startswith('-')]
    if len(words) >= 2 and words[1] in writes.get(words[0], ()):
        return f'{name} {words[0]} {words[1]} changes something other people see'
    if words[:1] == ['api']:
        rest = tokens[1:]
        for index, item in enumerate(rest):
            method = None
            if item in ('-X', '--method') and index + 1 < len(rest):
                method = rest[index + 1]
            elif item.startswith('--method='):
                method = item.split('=', 1)[1]
            elif item.startswith('-X') and len(item) > 2:
                method = item[2:]
            if method and method.upper() != 'GET':
                return f'{name} api {method.upper()} request'
            if item in ('-f', '-F', '--field', '--raw-field', '--input') or item.startswith(('--field=', '--raw-field=', '--input=')):
                return f'{name} api request with a body'
    return None


def check_tokens(tokens, cwd, depth=0):
    tokens = strip_prefixes(tokens)
    if not tokens:
        return None
    name = tokens[0].rsplit('/', 1)[-1]
    rest = tokens[1:]
    flags = [item for item in rest if item.startswith('-')]
    if name in ('sudo', 'doas', 'su', 'pkexec'):
        return 'running as root'
    if name in SHELLS and depth < 3:
        for index, item in enumerate(rest):
            if re.match(r'^-[a-zA-Z]*c$', item) and index + 1 < len(rest):
                return check_command(rest[index + 1], cwd, depth + 1)
    if name == 'eval' and depth < 3:
        return check_command(' '.join(rest), cwd, depth + 1)
    if name == 'git':
        return check_git(tokens, cwd)
    if name == 'gh':
        return check_forge(tokens, GH_WRITES, 'gh')
    if name == 'glab':
        return check_forge(tokens, GLAB_WRITES, 'glab')
    if name == 'rm' and any(re.match(r'^-[a-zA-Z]*[rR]', flag) or flag == '--recursive' for flag in flags):
        return 'recursive delete'
    if name == 'find' and ('-delete' in rest or any(rest[i] in ('-exec', '-execdir', '-ok') and rest[i + 1:i + 2] == ['rm'] for i in range(len(rest)))):
        return 'find that deletes files'
    if name in DISK:
        return 'disk-level command'
    if name in ('chmod', 'chown', 'chgrp') and any(re.match(r'^-[a-zA-Z]*R', flag) or flag == '--recursive' for flag in flags):
        return 'recursive permission change'
    if name in PUBLISHERS and 'publish' in rest:
        return 'package publish'
    if name == 'twine' and 'upload' in rest:
        return 'package publish'
    if name == 'docker' and rest[:1] == ['push']:
        return 'docker push'
    if name in ('terraform', 'tofu') and rest[:1] in (['apply'], ['destroy'], ['import'], ['taint']):
        return 'infrastructure change'
    if name in ('kubectl', 'oc') and rest[:1] in (['apply'], ['delete'], ['create'], ['rollout'], ['scale'], ['patch'], ['replace'], ['edit'], ['drain']):
        return 'cluster change'
    if name in DEPLOYERS and any(item in ('deploy', 'install', 'upgrade', 'rollback', 'uninstall') for item in rest):
        return 'deploy command'
    if name in ('shutdown', 'reboot', 'halt', 'poweroff'):
        return 'machine shutdown'
    if name in ('crontab',) and '-r' in flags:
        return 'crontab removal'
    return None


def segments_of(command):
    return [part for part in re.split(r'\|\||&&|[;|&\n]|\$\(|`|\(|\)', command) if part.strip()]


def check_command(command, cwd, depth=0):
    for pattern, reason in RAW_RULES:
        if re.search(pattern, command, re.IGNORECASE if 'Remove-Item' in pattern or 'format' in pattern else 0):
            return reason
    for segment in segments_of(command):
        reason = check_tokens(tokens_of(segment), cwd, depth)
        if reason:
            return reason
    return None


def decide(event):
    command = (event.get('tool_input') or {}).get('command')
    if not isinstance(command, str) or not command.strip():
        return None
    reason = check_command(command, event.get('cwd') or '')
    if not reason:
        return None
    return {'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': f'Blocked by ~/.claude/hooks/guard.py: {reason}. '
                                    'This is reserved for the user: stop and give them the exact command to run.',
    }}


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = None
    if not isinstance(event, dict):
        # An unreadable event cannot be judged, so it is refused rather than waved through.
        decision = {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                           'permissionDecisionReason': 'guard.py could not read the hook event.'}}
    else:
        decision = decide(event)
    if decision:
        print(json.dumps(decision))


if __name__ == '__main__':
    main()
