/* ==========================================================================
   Cara Mia · Encabezado de página con pestañas de sección (OWL)
   Se monta debajo del ControlPanel (ver caramia_nav.xml) solo para apps
   Caramia (menú raíz cuyo nombre empieza por "CARAMIA_").

   - Título: nombre visible del menú raíz (app), sin el prefijo CARAMIA_.
   - Descripción: x_caramia_descripcion de la sección activa o de la app.
   - Botón: x_caramia_boton_* de la sección activa o de la app.
   - Pestañas: hijos directos del menú raíz (nivel 2). Nivel 3 = desplegable.

   Patrones tomados de web_responsive / web (Odoo 18):
     * import { useService, useBus } from "@web/core/utils/hooks";
     * import { ControlPanel } from "@web/search/control_panel/control_panel";
     * Object.assign(ControlPanel.components, { ... });
   ========================================================================== */
import { Component, onWillStart, useState } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { router } from "@web/core/browser/router";
import { cleanMenuName, isCaramiaMenu, menuHref } from "@caramia_nav/js/utils.esm";

export class HeaderTabs extends Component {
    static template = "caramia_nav.HeaderTabs";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.menu = useService("menu");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            mode: false,
            appName: "",
            sections: [],
            activeSectionId: null,
            descripcion: "",
            botonEtiqueta: "",
            botonAccion: "",
        });

        /* Refresca al navegar (cambio de acción) y al cambiar de app. */
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this._refresh());
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this._refresh());
    }

    async onWillStart() {
        await this._refresh();
    }

    async _refresh() {
        const token = (this._refreshToken = (this._refreshToken || 0) + 1);
        const app = this.menu.getCurrentApp();
        const isCaramia = isCaramiaMenu(app);

        this.state.mode = isCaramia;
        document.body.classList.toggle("o-caramia-mode", isCaramia);

        if (!isCaramia) {
            this.state.appName = "";
            this.state.sections = [];
            this.state.activeSectionId = null;
            this.state.descripcion = "";
            this.state.botonEtiqueta = "";
            this.state.botonAccion = "";
            return;
        }

        this.state.appName = cleanMenuName(app.name);

        /* getMenuAsTree es la API real de menuService (Odoo 18).
           app.children solo contiene IDs; childrenTree contiene los objetos. */
        const tree = this.menu.getMenuAsTree(app.id);
        this.state.sections = this._normalizeSections((tree && tree.childrenTree) || []);

        const actionKeys = this._getCurrentActionKeys();
        const activeId = this._detectActiveSectionId(this.state.sections, actionKeys);
        this.state.activeSectionId = activeId;

        await this._loadTexts(app.id, activeId, token);
    }

    /* Normaliza childrenTree -> children para que el template sea simple
       y recursivo (soporta niveles 3, 4, ...). */
    _normalizeSections(items) {
        return (items || []).map((section) => ({
            ...section,
            children: this._normalizeSections(section.childrenTree || []),
        }));
    }

    /* Claves de la acción actual: id y path. router.current.action es la
       fuente principal; currentController.action cubre la carga inicial. */
    _getCurrentActionKeys() {
        const keys = new Set();
        const routeAction = router.current && router.current.action;
        if (routeAction !== undefined && routeAction !== null && routeAction !== "") {
            keys.add(String(routeAction));
        }
        const controller = this.action.currentController;
        const action = controller && controller.action;
        if (action) {
            if (action.id !== undefined && action.id !== null) {
                keys.add(String(action.id));
            }
            if (action.path) {
                keys.add(String(action.path));
            }
        }
        return keys;
    }

    _menuMatchesAction(menu, keys) {
        if (!menu) {
            return false;
        }
        if (menu.actionID && keys.has(String(menu.actionID))) {
            return true;
        }
        if (menu.actionPath && keys.has(String(menu.actionPath))) {
            return true;
        }
        return false;
    }

    _containsAction(items, keys) {
        return (items || []).some(
            (item) =>
                this._menuMatchesAction(item, keys) ||
                this._containsAction(item.children, keys)
        );
    }

    _detectActiveSectionId(sections, keys) {
        if (!keys.size) {
            return null;
        }
        for (const section of sections) {
            if (this._menuMatchesAction(section, keys)) {
                return section.id;
            }
            if (this._containsAction(section.children, keys)) {
                return section.id;
            }
        }
        return null;
    }

    /* Descripción y botón: sección activa con fallback al menú raíz (app). */
    async _loadTexts(appId, sectionId, token) {
        try {
            const ids = [appId];
            if (sectionId && sectionId !== appId) {
                ids.push(sectionId);
            }
            const records = await this.orm.read("ir.ui.menu", ids, [
                "x_caramia_descripcion",
                "x_caramia_boton_etiqueta",
                "x_caramia_boton_accion",
            ]);
            if (token !== this._refreshToken) {
                return;
            }
            const byId = {};
            for (const record of records) {
                byId[record.id] = record;
            }
            const root = byId[appId] || {};
            const section = (sectionId && byId[sectionId]) || {};

            this.state.descripcion =
                section.x_caramia_descripcion || root.x_caramia_descripcion || "";

            /* Etiqueta + acción se toman como un par: si la sección define
               cualquiera de las dos, se usa el par de la sección; si no,
               se hereda el par del menú raíz (app). */
            const sectionLabel = section.x_caramia_boton_etiqueta || "";
            const sectionAction = section.x_caramia_boton_accion || "";
            if (sectionLabel || sectionAction) {
                this.state.botonEtiqueta = sectionLabel;
                this.state.botonAccion = sectionAction;
            } else {
                this.state.botonEtiqueta = root.x_caramia_boton_etiqueta || "";
                this.state.botonAccion = root.x_caramia_boton_accion || "";
            }
        } catch (error) {
            console.warn("[caramia_nav] No se pudieron leer los campos del menú", error);
            this.state.descripcion = "";
            this.state.botonEtiqueta = "";
            this.state.botonAccion = "";
        }
    }

    menuHref(menu) {
        return menuHref(menu);
    }

    /* Navegación común a pestañas y al desplegable de nivel 3+.
       menuService.selectMenu() usa actionID y actualiza app + historial.
       Si algún menú solo tuviera actionPath, se navega por URL. */
    async _navigate(menu) {
        if (!menu) {
            return;
        }
        if (menu.actionID) {
            await this.menu.selectMenu(menu);
            return;
        }
        if (menu.actionPath) {
            window.location.assign(menuHref(menu));
        }
    }

    /* Clic en una pestaña: navega si tiene acción; si solo agrupa, el caret
       abre el desplegable nativo de Odoo. */
    onSectionClick(ev, section) {
        ev.preventDefault();
        ev.stopPropagation();
        this._navigate(section);
    }

    /* Clic en un hijo del desplegable de nivel 3+. */
    onMenuSelected(item) {
        this._navigate(item);
    }

    /* Teclado: flechas para moverse entre pestañas, Home/End. */
    onTabKeydown(ev) {
        const keys = ["ArrowRight", "ArrowLeft", "Home", "End"];
        if (!keys.includes(ev.key)) {
            return;
        }
        const nav = ev.currentTarget.closest(".o-caramia-tabs");
        if (!nav) {
            return;
        }
        const tabs = [...nav.querySelectorAll(".o-caramia-tab")];
        const index = tabs.indexOf(ev.currentTarget);
        if (index < 0) {
            return;
        }
        ev.preventDefault();
        let next = index;
        if (ev.key === "ArrowRight") {
            next = (index + 1) % tabs.length;
        }
        if (ev.key === "ArrowLeft") {
            next = (index - 1 + tabs.length) % tabs.length;
        }
        if (ev.key === "Home") {
            next = 0;
        }
        if (ev.key === "End") {
            next = tabs.length - 1;
        }
        tabs[next].focus();
    }

    /* Botón principal: XML ID de acción, ID numérico o URL absoluta. */
    async onMainButtonClick() {
        const raw = this.state.botonAccion;
        if (!raw) {
            return;
        }
        if (/^https?:\/\//i.test(raw)) {
            window.open(raw, "_blank", "noopener,noreferrer");
            return;
        }
        const action = /^\d+$/.test(raw) ? Number(raw) : raw;
        try {
            await this.action.doAction(action);
        } catch (error) {
            console.warn("[caramia_nav] No se pudo ejecutar el botón principal", raw, error);
        }
    }
}

/* Registrar HeaderTabs en los componentes de ControlPanel para que
   <HeaderTabs/> resuelva en la herencia de web.ControlPanel. */
Object.assign(ControlPanel.components, { HeaderTabs });
