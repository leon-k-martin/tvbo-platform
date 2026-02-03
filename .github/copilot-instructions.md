# Copilot Coding Agent Instructions for TVB-O Platform

## Project Overview

TVB-O Platform is an Odoo-based web application for the Virtual Brain Ontology. It runs in Docker containers with:
- **tvbo-odoo**: Odoo 17 with custom TVBO module
- **tvbo-db**: PostgreSQL database
- **tvbo-api**: TVBO Python API server

## Code Organization Principles

### File Structure

```
odoo-addons/tvbo/
├── static/src/
│   ├── css/           # All stylesheets (CSS files only)
│   ├── js/            # JavaScript files (logic only, NO CSS)
│   └── img/           # Images and icons
├── views/             # XML templates
├── data/              # Data files
└── models/            # Python Odoo models
```

### Critical Rules

#### 1. **NEVER define CSS inside JavaScript files**

CSS must ALWAYS be in separate `.css` files, not injected via JavaScript.

**WRONG:**
```javascript
// kg_components.js
const style = document.createElement('style');
style.textContent = `.my-class { color: red; }`;
document.head.appendChild(style);
```

**CORRECT:**
```css
/* kg_components.css */
.my-class { color: red; }
```

Then include the CSS in the XML template:
```xml
<link rel="stylesheet" href="/tvbo/static/src/css/kg_components.css"/>
```

**Why:** Maintainability. CSS-in-JS is hard to find, edit, and debug. Separate files enable browser caching and proper tooling support.

#### 2. **Component CSS files should match JS file names**

| JavaScript | CSS |
|------------|-----|
| `kg_browser.js` | `kg_browser.css` |
| `kg_components.js` | `kg_components.css` |
| `kg_graph.js` | `kg_graph.css` |

#### 3. **Load order in XML templates**

Always load CSS before JS, and load dependencies before dependent files:
```xml
<!-- CSS first -->
<link rel="stylesheet" href="/tvbo/static/src/css/kg_browser.css"/>
<link rel="stylesheet" href="/tvbo/static/src/css/kg_components.css"/>

<!-- JS: dependencies first -->
<script src="/tvbo/static/src/js/kg_components.js"></script>
<script src="/tvbo/static/src/js/kg_graph.js"></script>
<script src="/tvbo/static/src/js/kg_browser.js"></script>
```

## Development Workflow

### Updating the Odoo Module

After making changes to XML templates, you must upgrade the module:

```bash
make update-odoo
```

This runs `odoo -u tvbo` to reload templates from disk.

### Common Commands

```bash
make up              # Start all services
make down            # Stop all services
make update-odoo     # Update TVBO Odoo module (reload XML templates)
make logs-odoo       # View Odoo logs
make rebuild         # Rebuild Docker images
```

### File Changes That Require Module Upgrade

- Any `.xml` file changes (templates, views, data)
- Changes to `__manifest__.py`

### File Changes That DON'T Require Module Upgrade

- CSS files (browser refresh is enough, use Ctrl+Shift+R for hard refresh)
- JavaScript files (browser refresh is enough)
- Python model changes (Odoo auto-reloads in dev mode)

## Code Style

1. **Minimal & Clean:** Write the shortest code that works. No boilerplate.
2. **No Redundancy:** Check if logic exists before creating new code.
3. **MVP First:** No fallbacks or defensive coding. If it breaks, we fix it.
4. **Readable:** Clear names, simple control flow.

## Knowledge Graph Browser Architecture

The KG browser consists of:

| File | Purpose |
|------|---------|
| `kg_browser.js` | Main browser: search, facets, view switching |
| `kg_graph.js` | D3.js force-directed graph visualization |
| `kg_components.js` | Shared UI components (Modal, DetailPanel, Tooltip) |
| `kg_browser.css` | Browser layout and card styles |
| `kg_components.css` | Modal, tooltip, and detail panel styles |

### Component Pattern

Shared components are registered on `window.KGComponents`:

```javascript
// kg_components.js
window.KGComponents = window.KGComponents || {};

KGComponents.Modal = class {
    // ...
};

KGComponents.DetailPanel = class {
    // ...
};
```

Usage in other files:
```javascript
// kg_browser.js
this.modal = new KGComponents.Modal({ onClose: () => {} });
this.detailPanel = new KGComponents.DetailPanel();
```
