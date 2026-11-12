/* ==========================================================================
   Cara Mia · Utilidades compartidas de navegación (OWL)
   ========================================================================== */

/* Prefijo técnico opcional en el nombre del menú (compatibilidad). */
export const CARAMIA_PREFIX = "CARAMIA_";

/* Los módulos de Caramia se llaman caramia_* (caramia_facturacion,
   caramia_customer, caramia_production, ...). Es la fuente de verdad:
   el xmlid del menú raíz es "modulo.nombre". */
export const CARAMIA_MODULE = "caramia";

/** Módulo dueño de un menú a partir de su xmlid ("modulo.nombre"). */
function menuModule(menu) {
    const xmlid = (menu && menu.xmlid) || "";
    const dot = xmlid.indexOf(".");
    return dot > 0 ? xmlid.slice(0, dot).toLowerCase() : "";
}

/** ¿El menú es una app de Caramia?
 *  Se considera app Caramia si su menú raíz pertenece a un módulo
 *  caramia_* (o caramia). Como respaldo, si el nombre empieza por
 *  "CARAMIA_". */
export function isCaramiaMenu(menu) {
    if (!menu) {
        return false;
    }
    const mod = menuModule(menu);
    if (mod === CARAMIA_MODULE || mod.startsWith(CARAMIA_MODULE + "_")) {
        return true;
    }
    return (
        typeof menu.name === "string" &&
        menu.name.toUpperCase().startsWith(CARAMIA_PREFIX)
    );
}

/** Nombre visible: quita el prefijo técnico y cambia guiones bajos por espacios. */
export function cleanMenuName(name) {
    return String(name || "")
        .replace(/^CARAMIA[_\s-]*/i, "")
        .replace(/_/g, " ")
        .trim();
}

/** URL interna de un menú, igual que la que usa web.NavBar.getMenuItemHref. */
export function menuHref(menu) {
    if (!menu) {
        return "#";
    }
    if (menu.actionPath) {
        return `/odoo/${String(menu.actionPath).replace(/^\/+/, "")}`;
    }
    if (menu.actionID) {
        return `/odoo/action-${menu.actionID}`;
    }
    return "#";
}
