/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { onMounted } from "@odoo/owl";

const STATE_NAMES = {
    draft: "Borrador",
    in_progress: "En Progreso",
    stopped: "Detenida",
    done: "Hecha",
    canceled: "Cancelada",
};

patch(KanbanController.prototype, {
    setup() {
        super.setup();
        onMounted(() => {
            // Inyectar nombres de estado en las columnas del kanban de producción
            setTimeout(() => {
                const groups = document.querySelectorAll(".o_kanban_group");
                groups.forEach((g) => {
                    const dataId = g.getAttribute("data-id");
                    const title = g.querySelector(".o_column_title");
                    if (dataId && title && STATE_NAMES[dataId]) {
                        const existing = title.textContent.trim();
                        if (!existing.includes(STATE_NAMES[dataId])) {
                            const span = document.createElement("span");
                            span.textContent = STATE_NAMES[dataId];
                            span.style.display = "block";
                            span.style.fontFamily = "'Source Serif 4', Georgia, serif";
                            span.style.fontSize = "1rem";
                            span.style.fontWeight = "600";
                            span.style.color = "#14161c";
                            span.style.marginBottom = "0.15rem";
                            title.insertBefore(span, title.firstChild);
                        }
                    }
                });
            }, 500);
        });
    },
});