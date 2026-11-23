# Interactive bash: ble.sh highlighting, suggestions and Shift-selection, a starship prompt and colourful tools.
[[ $- == *i* ]] || return

[[ -f ~/.local/share/blesh/ble.sh ]] && source ~/.local/share/blesh/ble.sh --noattach

export BAT_THEME=ansi
if command -v eza >/dev/null; then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -l --icons --git --group-directories-first'
  alias la='eza -la --icons --git --group-directories-first'
  alias lt='eza -la --icons --git --sort=modified --time-style=relative'
  alias tree='eza --tree --icons'
fi
command -v bat >/dev/null && alias cat='bat --paging=never'
command -v starship >/dev/null && eval "$(starship init bash)"

[[ ${BLE_VERSION-} ]] && ble-attach
