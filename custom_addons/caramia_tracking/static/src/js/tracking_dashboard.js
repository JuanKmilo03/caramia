/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class TrackingStats extends Component {
    static template = "caramia_tracking.Stats";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, loading: true });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("cara.mia.produccion", "get_tracking_dashboard", []);
        this.state.loading = false;
    }

    refresh() {
        return this.load();
    }

    get periodos() {
        const d = this.state.data;
        return [
            { key: "semana", titulo: "Esta semana", ...d.semana },
            { key: "mes", titulo: "Este mes", ...d.mes },
        ];
    }

    get series() {
        const d = this.state.data;
        return [
            { key: "s", titulo: "Pares por semana", rows: d.serie_semanal },
            { key: "m", titulo: "Pares por mes", rows: d.serie_mensual },
        ];
    }

    pct(value, total) {
        if (!total) {
            return 0;
        }
        return Math.min(100, Math.round((100 * value) / total));
    }

    barHeight(value, rows) {
        const max = Math.max(1, ...rows.flatMap((r) => [r.programado, r.finalizado]));
        return Math.round((value / max) * 140);
    }

    fmtDate(iso) {
        const [y, m, d] = iso.split("-");
        return `${d}/${m}/${y}`;
    }

    openOrders(name, domain) {
        const d = this.state.data;
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "cara.mia.produccion",
            views: [[d.list_view_id, "list"], [d.form_view_id, "form"]],
            search_view_id: [d.search_view_id, "search"],
            domain,
            target: "current",
        });
    }

    openPendientes() {
        const d = this.state.data;
        this.openOrders("Entregas pendientes", [
            ["state", "in", d.estados_activos], ["fecha_estimada", "!=", false]]);
    }
    openVencidas() {
        const d = this.state.data;
        this.openOrders("Entregas vencidas", [
            ["state", "in", d.estados_activos], ["fecha_estimada", "<", d.hoy]]);
    }
    openProximas() {
        const d = this.state.data;
        this.openOrders("Entregas próximos 7 días", [
            ["state", "in", d.estados_activos],
            ["fecha_estimada", ">=", d.hoy], ["fecha_estimada", "<=", d.limite_proximas]]);
    }
    openEstancadas() {
        this.openOrders("Órdenes estancadas", [["esta_estancada", "=", true]]);
    }

    // Una orden individual se abre en ventana modal; al cerrarla se refresca la pantalla
    openOrder(id) {
        const d = this.state.data;
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "cara.mia.produccion",
                res_id: id,
                views: [[d.form_view_id, "form"]],
                target: "new",
                context: { dialog_size: "extra-large" },
            },
            { onClose: () => this.refresh() }
        );
    }
}

registry.category("actions").add("caramia_tracking.stats", TrackingStats);
