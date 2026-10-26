import { Component, useEffect, useRef, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { SIZES } from "@web/core/ui/ui_service";
import { useBus, useService } from "@web/core/utils/hooks";

const FOLDED_KEY = "web_nested_sidebar.folded";

/**
 * Return the entries from a top-level section down to the first leaf that opens `actionId`, or undefined when no leaf does.
 */
function findPath(entries, actionId) {
    for (const entry of entries) {
        if (!entry.childrenTree.length && entry.actionID === actionId) {
            return [entry];
        }
        const path = findPath(entry.childrenTree, actionId);
        if (path) {
            return [entry, ...path];
        }
    }
}

/**
 * Side menu listing every app with its menus nested underneath, the current app unfolded and the current page marked. On wide screens it stays open beside the page and the menu button folds it to app icons (remembered per browser); on narrower ones the menu button opens it as a drawer over the page.
 */
export class SideMenu extends Component {
    static template = "web_nested_sidebar.SideMenu";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.ui = useState(useService("ui"));
        this.state = useState({ isOpen: false, folded: browser.localStorage.getItem(FOLDED_KEY) === "1", open: {}, activeId: null, top: 0 });
        this.toggleRef = useRef("toggle");
        this.menuRef = useRef("menu");
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.revealCurrent());
        useEffect(
            (isOpen) => isOpen && this.menuRef.el.querySelector("[aria-current]")?.focus(),
            () => [this.state.isOpen]
        );
        useEffect(
            (header) => {
                const observer = new ResizeObserver(() => (this.state.top = header.getBoundingClientRect().bottom));
                observer.observe(header);
                return () => observer.disconnect();
            },
            () => [this.toggleRef.el.closest("header")]
        );
    }

    get docked() {
        return this.ui.size >= SIZES.LG;
    }

    get apps() {
        return this.menuService.getApps();
    }

    children(app) {
        return this.menuService.getMenuAsTree(app.id).childrenTree;
    }

    href(entry) {
        return `/odoo/${entry.actionPath || `action-${entry.actionID}`}`;
    }

    /** Mark the current page and unfold the app and groups that lead to it, leaving other open groups as they are. */
    revealCurrent() {
        const app = this.menuService.getCurrentApp();
        const path = (app && findPath(this.children(app), this.actionService.currentController?.action.id)) || [];
        this.state.activeId = path.length ? path.at(-1).id : app?.id;
        for (const entry of [app, ...path.slice(0, -1)].filter(Boolean)) {
            this.state.open[entry.id] = true;
        }
    }

    onToggle() {
        if (this.docked) {
            this.state.folded = !this.state.folded;
            browser.localStorage.setItem(FOLDED_KEY, this.state.folded ? "1" : "");
        } else if (this.state.isOpen) {
            this.close();
        } else {
            this.revealCurrent();
            this.state.isOpen = true;
        }
    }

    close() {
        this.state.isOpen = false;
        this.toggleRef.el.focus();
    }

    toggleGroup(entry) {
        this.state.open[entry.id] = !this.state.open[entry.id];
    }

    select(entry) {
        if (!this.docked) {
            this.close();
        }
        this.menuService.selectMenu(entry);
    }

    onKeydown(ev) {
        if (ev.key === "Escape" && !this.docked) {
            this.close();
        }
    }
}
