/* ==========================================================================
   Cara Mia · App switcher de la navbar (OWL)
   Lista horizontal con las apps Caramia (menús raíz que empiezan por
   "CARAMIA_"). La app activa va en blanco con línea inferior dorada.
   Solo se muestra cuando la app activa es de Caramia.

   Patrones tomados de web_responsive / web (Odoo 18):
     * import { NavBar } from "@web/webclient/navbar/navbar";
     * import { useService } from "@web/core/utils/hooks";
     * import { patch } from "@web/core/utils/patch";
     * Object.assign(NavBar.components, { ... });
   ========================================================================== */
import { Component, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { cleanMenuName, isCaramiaMenu, menuHref } from "@caramia_nav/js/utils.esm";

export class CaramiaAppSwitcher extends Component {
    static template = "caramia_nav.AppSwitcher";
    static props = {
        apps: { type: Array, optional: true },
        currentApp: { type: Object, optional: true },
    };

    setup() {
        this.menu = useService("menu");

        /* Sincroniza la clase .o-caramia-mode en <body> con la app activa.
           Es la fuente de verdad más estable: la navbar siempre está montada. */
        useEffect(
            () => {
                document.body.classList.toggle("o-caramia-mode", this.isCaramia);
            },
            () => [this.props.currentApp && this.props.currentApp.id]
        );
    }

    get isCaramia() {
        return isCaramiaMenu(this.props.currentApp);
    }

    get caramiaApps() {
        return (this.props.apps || []).filter(isCaramiaMenu);
    }

    get currentAppId() {
        return this.props.currentApp ? this.props.currentApp.id : null;
    }

    appLabel(app) {
        return cleanMenuName(app && app.name);
    }

    appHref(app) {
        return menuHref(app);
    }

    onAppClick(ev, app) {
        if (!app) {
            return;
        }
        /* Deja que el navegador abra en otra pestaña con Ctrl/Cmd/Shift/Alt. */
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey) {
            return;
        }
        ev.preventDefault();
        this.menu.selectMenu(app);
    }
}

/* El template heredado de web.NavBar.SectionsMenu usa this.isCaramiaApp(). */
patch(NavBar.prototype, {
    isCaramiaApp() {
        return isCaramiaMenu(this.currentApp);
    },
});

/* Registrar el switcher en los componentes de NavBar para que
   <CaramiaAppSwitcher/> resuelva en la herencia de web.NavBar. */
Object.assign(NavBar.components, { CaramiaAppSwitcher });
