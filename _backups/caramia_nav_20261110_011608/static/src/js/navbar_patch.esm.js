/* ==========================================================================
   Cara Mia · Patch de navbar para apps Caramia (OWL)
   Este archivo se mantiene por compatibilidad, pero la activación real de
   .o-caramia-mode ahora la hace HeaderTabs directamente en su onWillStart.
   No se importa ni parchea directamente el componente web.NavBar para no
   depender de rutas internas de tu build.
   ========================================================================== */
export function activateCaramiaNavbar() {
    /* No-op: la activación se hace desde header_tabs.esm.js */
}
