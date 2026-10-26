import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { NavBar } from "@web/webclient/navbar/navbar";
import { preferencesItem } from "@web/webclient/user_menu/user_menu_items";
import { SideMenu } from "./side_menu";

// The strip's account menu is the backend's only one, so Odoo's avatar menu leaves the systray.
registry.category("systray").remove("web.user_menu");

/** The account menu's entries when the platform does not send its own as ``account_menu`` in the session info. */
const DEFAULT_ACCOUNT_MENU = [
    { key: "website", label: _t("Website"), url: "/", icon: "fa-globe" },
    { key: "preferences", label: _t("Preferences"), url: "/odoo", icon: "fa-sliders" },
    { key: "logout", label: _t("Log out"), url: "/web/session/logout?redirect=/", icon: "fa-sign-out" },
];

patch(NavBar, { components: { ...NavBar.components, SideMenu } });

patch(NavBar.prototype, {
    /** Name and logo of the strip above the navbar, set by the server in the session info. */
    get siteHeader() {
        return session.site_header;
    },

    get userName() {
        return user.name;
    },

    get accountMenu() {
        return session.account_menu || DEFAULT_ACCOUNT_MENU;
    },

    /** Open Odoo's preferences dialog for the ``preferences`` entry and leave the web client for any other; entries with a link only mark it, they do not follow it. */
    onAccountEntry(entry) {
        if (entry.key === "preferences") {
            preferencesItem(this.env).callback();
        } else {
            browser.location.href = entry.url;
        }
    },
});
