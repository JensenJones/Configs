"""Check which shell commands the guard hook blocks and which it lets through."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

GUARD = Path(__file__).resolve().parents[1]/'claude/hooks/guard.py'
spec = importlib.util.spec_from_file_location('guard', GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

BLOCKED = [
    'sudo apt-get install ripgrep',
    'echo hi | sudo tee /etc/hosts',
    'git push --force',
    'git push -f origin feature/x',
    'git push --force-with-lease origin feature/x',
    'git push origin main',
    'git push origin HEAD:refs/heads/master',
    'git push origin feature/x:release/1.2',
    'git push origin +feature/x',
    'git push origin :old-branch',
    'git push --delete origin old-branch',
    'git push --all',
    'git -C repo push origin master',
    'git reset --hard HEAD~1',
    'git clean -fd',
    'cd src && git checkout -- .',
    'git checkout .',
    'git restore src/book.cpp',
    'git stash drop',
    'git branch -D old',
    'git tag -d v1',
    'git filter-branch --tree-filter x',
    "bash -c 'git push --force'",
    'env GIT_TRACE=1 git push -f',
    'gh pr create --fill',
    'gh pr merge 12',
    'gh pr comment 12 -b looks-good',
    'gh pr review 12 --approve',
    'gh issue create -t bug',
    'gh issue comment 4 -b hi',
    'gh release create v1',
    'gh api -X POST repos/a/b/issues',
    'gh api repos/a/b/issues -f title=x',
    'glab mr create',
    'glab mr note 3 -m hi',
    'rm -rf build',
    'rm -r old',
    'find . -name "*.o" -delete',
    'find . -name "*.o" -exec rm {} ;',
    'chmod -R 777 .',
    'dd if=/dev/zero of=/dev/sda',
    'npm publish',
    'docker push registry/image',
    'terraform apply',
    'kubectl delete pod x',
    'Remove-Item -Recurse -Force build',
    'rd /s /q build',
]

ALLOWED = [
    'git status',
    'git add -A',
    'git commit -m "Fix the order book"',
    'git commit --amend --no-edit',
    'git push',
    'git push origin feature/x',
    'git push -u origin feature/x',
    'git pull --ff-only',
    'git checkout -b feature/y',
    'git checkout feature/y',
    'git restore --staged src/book.cpp',
    'git stash',
    'git stash pop',
    'git log --oneline -5',
    'git diff main...HEAD',
    'git rebase main',
    'git branch --list',
    'gh pr view 12',
    'gh pr diff 12',
    'gh pr list',
    'gh pr checks 12',
    'gh api repos/a/b/pulls/12',
    'glab mr view 3',
    'rm notes.txt',
    'cmake --build build -j',
    'ninja -C build test',
    'ctest --test-dir build --output-on-failure',
    'grep -rf patterns.txt src',
    'clang-format -i src/book.cpp',
    'echo "do not force this"',
    'python3 -m unittest',
    'ls -R src',
]


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='guard-')
        self.addCleanup(self.temporary.cleanup)
        self.cwd = self.temporary.name

    def test_permanent_and_outward_facing_commands_are_blocked(self):
        for command in BLOCKED:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.check_command(command, self.cwd), 'allowed: ' + command)

    def test_everyday_commands_are_allowed(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(guard.check_command(command, self.cwd), 'blocked: ' + command)

    def test_a_plain_push_is_blocked_only_on_a_protected_branch(self):
        def git(*arguments):
            subprocess.run(['git', *arguments], cwd=self.cwd, check=True, capture_output=True)
        git('init', '-q', '-b', 'main')
        self.assertIn('main', guard.check_command('git push', self.cwd))
        git('checkout', '-q', '-b', 'feature/x')
        self.assertIsNone(guard.check_command('git push', self.cwd))
        self.assertIsNone(guard.check_command('git push origin HEAD', self.cwd))

    def run_hook(self, payload):
        return subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True, text=True, timeout=10)

    def test_the_hook_prints_a_deny_decision_and_exits_zero(self):
        event = {'tool_name': 'Bash', 'cwd': self.cwd, 'tool_input': {'command': 'git push --force'}}
        result = self.run_hook(json.dumps(event))
        self.assertEqual(result.returncode, 0, result.stderr)
        decision = json.loads(result.stdout)['hookSpecificOutput']
        self.assertEqual(decision['permissionDecision'], 'deny')
        self.assertIn('force push', decision['permissionDecisionReason'])

    def test_the_hook_stays_silent_for_an_allowed_command(self):
        event = {'tool_name': 'Bash', 'cwd': self.cwd, 'tool_input': {'command': 'git status'}}
        result = self.run_hook(json.dumps(event))
        self.assertEqual((result.returncode, result.stdout), (0, ''), result.stderr)

    def test_an_unreadable_event_is_refused(self):
        result = self.run_hook('not json')
        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')


if __name__ == '__main__':
    unittest.main()
