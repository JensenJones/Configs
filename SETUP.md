# Setting up a new machine

Instructions for Claude Code. The goal: Jensen can sit down at this machine and work the way he does at home. Work through the steps in order, report after each one in a line or two, and finish with the summary in step 9.

## Ground rules

- This is probably a company machine. Before installing anything, ask Jensen once whether company policy restricts installing software, changing terminal or shell settings, or using personal GitHub repositories. Follow what he says.
- Never run `sudo`. When a step needs it, print the exact command and wait for him to run it.
- Prefer installs that stay inside the home directory. Do not touch company-managed configuration: managed Claude settings, proxies, certificates, SSH keys, Git credentials, shell profiles pushed by IT.
- If a download is blocked, a package source is unreachable or a tool is already provided by the company, stop and ask. Do not look for a way round it.
- Do not replace anything that already exists without backing it up and telling him.
- Ask when something is ambiguous. Do not guess.

## 1. Look before changing anything

Report: operating system and version, CPU architecture, shell, package manager (Homebrew, apt, dnf, pacman, winget), desktop environment on Linux, and whether each of these is already present with its version: `git`, `curl`, `python3`, a C/C++ compiler, `nvim`, `rg`, `wezterm`, `herdr`, `rtk`, `clangd`, `clang-format`, `cmake`, `ninja`, `gdb` or `lldb`, `perf` (Linux).

Do not install compilers, build systems or debuggers. The company will have a toolchain; note what is missing and ask.

## 2. Prerequisites

`git`, `curl` and `python3` are required by later steps. Install any that are missing with the package manager, or print the `sudo` command for Jensen.

## 3. Terminal

jvim's shortcuts need a terminal that can send them. Install **WezTerm** (https://wezterm.org/installation.html) unless it is present:

- macOS: `brew install --cask wezterm`
- Linux: the distribution's package or WezTerm's own repository; the commands are in the jvim README. These need `sudo`, so print them.
- Windows: `winget install wez.wezterm`

The jvim installer in the next step writes WezTerm's settings. Do not write them by hand.

## 4. jvim

jvim is Jensen's Neovim configuration: https://github.com/JensenJones/JensenVim. Follow its README section for this operating system. In short:

- macOS: install the Homebrew packages the README lists, clone into `~/JensenVim`, then run `~/JensenVim/install-macos.sh --apply`.
- Linux: `curl -fsSL https://raw.githubusercontent.com/JensenJones/JensenVim/main/bootstrap-linux.sh | sh`
- Windows (PowerShell): set `$env:JVIM_FRONTEND = 'nvim'` first so jvim runs in the terminal, then `irm https://raw.githubusercontent.com/JensenJones/JensenVim/main/bootstrap-windows.ps1 | iex`

Then follow "Setting up jvim on a new machine" in that repository's `AGENTS.md`: install the pinned plugins headlessly, run `python3 scripts/check.py`, and fix what fails on this machine. Skips are expected; failures are not.

## 5. Keyboard shortcuts

- Linux: run `integrations/linux/desktop-keys.py` from the jvim checkout. If it lists desktop shortcuts that clash with jvim, explain them and run it with `--apply` once Jensen agrees.
- macOS: if F4 opens Launchpad, tell him to use Fn+F4 or change it in System Settings. Change nothing yourself.
- Windows: nothing to do.

## 6. Herdr and rtk

- **Herdr** (https://herdr.dev) is the terminal workspace Jensen runs jvim and Claude in. On macOS: `brew install herdr`. Elsewhere, follow the site's install instructions, or say so if this platform is not supported. Then `herdr integration install claude`.
- **rtk** (https://www.rtk-ai.app) condenses command output. On macOS: `brew install rtk-ai/tap/rtk`. Elsewhere, follow the site. Then `rtk init --global`, and confirm `~/.claude/settings.json` now has a `PreToolUse` hook that runs `rtk hook claude`.

Both are optional. If either cannot be installed, skip it, and for rtk also remove the `@RTK.md` line from the installed `CLAUDE.md`.

## 7. Claude Code files

Install the contents of `claude/` in this repository into `~/.claude/` (on Windows, `%USERPROFILE%\.claude\`):

| From | To | How |
| --- | --- | --- |
| `claude/CLAUDE.md`, `claude/CPP.md`, `claude/RTK.md` | `~/.claude/` | Copy. If a `CLAUDE.md` already exists, back it up and show Jensen the difference before replacing it. |
| `claude/hooks/guard.py` | `~/.claude/hooks/guard.py` | Copy. |
| `claude/keybindings.json` | `~/.claude/keybindings.json` | Copy, or merge into an existing file. |
| `claude/settings.json` | `~/.claude/settings.json` | Merge key by key into the existing file. Keep keys this repository does not mention. Append to lists such as `permissions.deny` and `hooks.PreToolUse` without duplicating entries. |

Then:

1. Check the hook's interpreter. The settings call `python3`. If only `python` or `py -3` exists (common on Windows), change the hook command to match.
2. Run `python3 -m unittest tests.test_guard` from this repository. It must pass.
3. Prove the hook is live: in a throwaway Git repository, ask Claude to run `git reset --hard`. It must be refused with a message naming `guard.py`. If it runs, the hook is not installed correctly; fix it before going further.
4. Plugins: `claude plugin install clangd-lsp@claude-plugins-official` and `claude plugin install superpowers@claude-plugins-official`. The clangd plugin needs `clangd` on PATH.
5. If the company manages Claude's settings and refuses `bypassPermissions`, leave its mode in place. The hook and the deny list still apply.

## 8. Git identity

Run `git config --global user.name` and `user.email`. If they are unset, ask Jensen for the name and the work email to use. Do not copy an address from anywhere else.

## 9. Finish

Give Jensen one short summary:

- what was installed, with versions
- what was skipped and why
- every command he still has to run himself (anything needing `sudo`)
- what to try by hand: open WezTerm, start `herdr`, run `jvim .` in a project, and press save, close, the action menu and paste, since no check can press keys in a real window
