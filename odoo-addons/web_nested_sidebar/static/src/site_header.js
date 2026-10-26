import { Component, markup } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { NavBar } from "@web/webclient/navbar/navbar";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { preferencesItem } from "@web/webclient/user_menu/user_menu_items";
import { SideMenu } from "./side_menu";

/** The account menu's entries when the platform does not send its own as ``account_menu`` in the session info. */
const DEFAULT_ACCOUNT_MENU = [
    { key: "website", label: _t("Website"), url: "/", icon: "fa-globe" },
    { key: "preferences", label: _t("Preferences"), url: "/odoo", icon: "fa-sliders" },
    { key: "log_out", label: _t("Log out"), url: "/web/session/logout?redirect=/", icon: "fa-sign-out" },
];

/** The user's name and login at the top of the account menu. */
class AccountMenuHeader extends Component {
    static template = "web_nested_sidebar.AccountMenuHeader";
    static props = {};

    setup() {
        this.user = user;
    }
}

// Odoo's account menu moves from the systray into the strip.
registry.category("systray").remove("web.user_menu");

const accountItems = registry.category("user_menuitems");
// Odoo's Help, Shortcuts, Odoo.com account and Install app items are left out, with the divider that followed the first two.
for (const key of ["support", "shortcuts", "separator", "odoo_account", "install_pwa"]) {
    accountItems.remove(key);
}
accountItems.add("account_header", (env) => ({ type: "component", contentComponent: AccountMenuHeader, hide: env.isSmall, sequence: 1 }));
(session.account_menu || DEFAULT_ACCOUNT_MENU).forEach((entry, index) => {
    if (entry.key === "log_out") {
        accountItems.add("log_out_separator", () => ({ type: "separator", sequence: 99 }));
    }
    // An entry named like one of Odoo's items (preferences, log_out) takes its place; preferences keeps Odoo's dialog.
    accountItems.add(entry.key, (env) => ({
        type: "item",
        id: entry.key,
        description: markup`<span><i class="fa fa-fw ${entry.icon} me-2" aria-hidden="true"></i>${entry.label}</span>`,
        href: entry.url,
        callback: entry.key === "preferences" ? preferencesItem(env).callback : () => (browser.location.href = entry.url),
        sequence: entry.key === "log_out" ? 100 : 50 + index,
    }), { force: true });
});

patch(NavBar, { components: { ...NavBar.components, SideMenu, UserMenu } });

patch(NavBar.prototype, {
    /** Name and logo of the strip above the navbar, set by the server in the session info. */
    get siteHeader() {
        return session.site_header;
    },
});
