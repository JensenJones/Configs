# Configs

Everything Claude Code needs to make a new machine comfortable for me: my editor, terminal, and Claude's own rules and guard rails. Works on macOS, Linux and Windows.

## Use

Install [Claude Code](https://code.claude.com/docs/en/setup), then:

```sh
git clone https://github.com/JensenJones/Configs.git
cd Configs
claude "Read SETUP.md and set up this machine."
```

Claude reports what is already there, asks before anything a company policy might restrict, and prints any command that needs `sudo` for me to run.

## What it sets up

- **jvim**, my Neovim configuration ([JensenVim](https://github.com/JensenJones/JensenVim)), with WezTerm and its key bindings.
- **Herdr** and **rtk**, where they are available.
- **Claude Code**, from `claude/`:
  - `CLAUDE.md`: how Claude talks to me and works. Concise, asks instead of guessing, fits the existing code, few comments, verifies before reporting.
  - `CPP.md`: C++ rules for low-latency trading code. Hot path versus cold path, no allocation or locks on the hot path, measure before claiming, tail latency, sanitizers.
  - `hooks/guard.py`: blocks commands that are permanent or reach other people. Force pushes, pushes to protected branches, discarding uncommitted work, recursive deletes, `sudo`, and creating or commenting on pull requests and issues. Committing and pushing a feature branch are allowed.
  - `settings.json`: permissions, the hook, plugins (clangd, superpowers) and spinner phrases.

## Check the guard

```sh
python3 -m unittest tests.test_guard
```

## Where the C++ rules come from

- C++ Core Guidelines, the Performance and Concurrency sections.
- Carl Cook, "When a Microsecond Is an Eternity: High Performance Trading Systems in C++" (CppCon 2017).
- Timur Doumler, "Want fast C++? Know your hardware!" (CppCon 2016).
- David Gross, "Trading at light speed: designing low latency systems in C++" (Meeting C++ 2022).
- Fedor Pikus, *The Art of Writing Efficient Programs*.
- Agner Fog, *Optimizing software in C++*.
