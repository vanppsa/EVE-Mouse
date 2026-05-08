UUID = com.eve.mouse.desktop
DEST = $(HOME)/.local/share/applications

.PHONY: install uninstall

install:
	@echo "🚀 Installing EVE Mouse..."
	@bash ./setup.sh

uninstall:
	@echo "🗑️ Removing EVE Mouse..."
	@rm -f "$(DEST)/$(UUID)"
	@rm -rf "$(HOME)/.local/share/icons/hicolor/256x256/apps/com.eve.mouse.png"
	@if command -v gtk-update-icon-cache &>/dev/null; then \
		gtk-update-icon-cache -f "$(HOME)/.local/share/icons/hicolor" 2>/dev/null || true; \
	fi
	@echo "✅ Removal completed!"
