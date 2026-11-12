/* ==========================================================================
   Cara Mia · Encabezado de página con pestañas de sección (OWL)
   Componente auto-suficiente: usa menuService, orm y actionService.
   Se monta debajo del ControlPanel solo para apps Caramia
   (menú raíz cuyo nombre empieza con "CARAMIA_").
   Activa la clase .o-caramia-mode en <body> para que el CSS se aplique.

   Servicios Odoo 18 usados (nombres estándar de la versión):
     * useService("menu")   -> this.menu.currentApp, this.menu.currentApp.children
     * useService("orm")    -> this.orm.read(model, ids, fields)
     * useService("action") -> this.action.doAction(action)

   Si algún nombre de servicio o forma de dato difiere en tu build exacta,
   ajusta únicamente las líneas marcadas con ⚠ VERIFICAR.
   ========================================================================== */
import { Component, onWillStart, mounted, useState } from "@odoo/owl";
import { useService } from "@odoo/owl";

export class HeaderTabs extends Component {
    static template = "caramia_nav.HeaderTabs";
    static props = {};

    setup() {
        this.menu = useService("menu");          // ⚠ VERIFICAR nombre exacto en tu web 18
        this.orm = useService("orm");            // ⚠ VERIFICAR
        this.action = useService("action");      // ⚠ VERIFICAR

        this.state = useState({
            mode: false,
            app: null,
            sections: [],
            activeSectionId: null,
            descripcion: "",
            botonEtiqueta: "",
            botonAccion: "",
            loading: true,
        });
    }

    async onWillStart() {
        await this._refresh();
    }

    mounted() {
        /* Insertar el encabezado justo después del .o_control_panel_main
           (migas de pan + buscador), dentro del o_control_panel. */
        const cpMain = document.querySelector(".o_control_panel_main");
        if (cpMain && this.el && !document.querySelector(".o-caramia-header")) {
            cpMain.parentNode?.insertBefore(this.el, cpMain.nextSibling);
        }
    }

    /* Activa la clase .o-caramia-mode en <body> si la app es de Caramia.
       Esa clase es la que activa todo el CSS de caramia_nav.scss. */
    _activateCaramiaMode() {
        const app = this.menu.currentApp; // ⚠ VERIFICAR forma de currentApp
        const isCaramia =
            app && typeof app.name === "string" && app.name.startsWith("CARAMIA_");
        if (isCaramia) {
            document.body.classList.add("o-caramia-mode");
        } else {
            document.body.classList.remove("o-caramia-mode");
        }
        return isCaramia;
    }

    /* Lee app activa, secciones (hijos directos del menú raíz) y campos x_caramia_*. */
    async _refresh() {
        const isCaramia = this._activateCaramiaMode();
        this.state.mode = isCaramia;
        if (!isCaramia) {
            this.state.loading = false;
            return;
        }

        const app = this.menu.currentApp; // ⚠ VERIFICAR forma de currentApp
        this.state.app = app;

        /* Secciones = hijos directos del menú raíz, ordenados por sequence. */
        const children = Array.isArray(app.children) ? app.children : []; // ⚠ VERIFICAR forma
        this.state.sections = children
            .slice()
            .sort((a, b) => (a.sequence ?? 0) - (b.sequence ?? 0));

        /* Sección activa: intenta detectar por acción actual. */
        this.state.activeSectionId = this._detectActiveSectionId(children); // ⚠ VERIFICAR

        /* Descripción y botón principal desde los campos x_caramia_* del menú raíz. */
        try {
            const root = await this.orm.read("ir.ui.menu", [app.id], [
                "x_caramia_descripcion",
                "x_caramia_boton_etiqueta",
                "x_caramia_boton_accion",
            ]); // ⚠ VERIFICAR firma de orm.read en tu build
            const r = (root && root[0]) || {};
            this.state.descripcion = r.x_caramia_descripcion || "";
            this.state.botonEtiqueta = r.x_caramia_boton_etiqueta || "";
            this.state.botonAccion = r.x_caramia_boton_accion || "";
        } catch (e) {
            console.warn("[caramia_nav] no se pudieron leer campos del menú raíz", e);
        }

        this.state.loading = false;
    }

    /* Intenta adivinar qué sección está activa según la acción vigente. */
    _detectActiveSectionId(children) {
        const currentAction = this.action.currentAction; // ⚠ VERIFICAR existencia/nombre
        if (!currentAction || !children) return null;
        const ref = String(
            currentAction.res_model ||
            currentAction.name ||
            currentAction.id ||
            ""
        );
        const hit = children.find(
            (s) =>
                s.action &&
                (String(s.action).includes(ref) ||
                    String(s.action).includes(String(currentAction.id || "")))
        );
        return hit ? hit.id : null;
    }

    /* Clic en una pestaña: navega a la acción de la sección (historial del navegador). */
    async onSectionClick(ev, section) {
        ev.preventDefault();
        if (!section || !section.action) return;
        try {
            await this.action.doAction(section.action); // ⚠ VERIFICAR: historial del navegador
        } catch (e) {
            if (typeof section.action === "string" && /^https?:\/\//i.test(section.action)) {
                window.location.href = section.action;
            } else {
                console.warn("[caramia_nav] no se navegó a la sección", section.action, e);
            }
        }
    }

    /* Clic en el botón principal (igual para toda la app). */
    onMainButtonClick() {
        const accion = this.state.botonAccion;
        if (!accion) return;
        if (/^https?:\/\//i.test(accion)) {
            window.open(accion, "_blank");
            return;
        }
        /* Asume identificador XML de acción (module.action_id) o id numérico. */
        try {
            this.action.doAction(accion); // ⚠ VERIFICAR
        } catch (e) {
            console.warn("[caramia_nav] botón principal falló", accion, e);
        }
    }
}
