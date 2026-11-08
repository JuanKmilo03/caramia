/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

class TrackingStats extends Component {
    static template = "caramia_tracking.Stats";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, loading: true, chartPeriod: 'semana' });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("cara.mia.produccion", "get_tracking_dashboard", []);
        this.state.loading = false;
    }

    get userName() {
        return session.name || session.username || session.partner_display_name || "";
    }

    get greeting() {
        const h = new Date().getHours();
        let saludo = "Buenos días";
        if (h >= 12 && h < 19) saludo = "Buenas tardes";
        else if (h >= 19 || h < 5) saludo = "Buenas noches";
        const name = this.userName;
        return name ? `${saludo}, ${name}` : saludo;
    }

    refresh() {
        return this.load();
    }

    get periodos() {
        const d = this.state.data;
        return [
            { key: "semana", titulo: "Esta semana", ...d.semana },
        ];
    }

    get series() {
        const d = this.state.data;
        return [
            { key: "s", titulo: "Pares por semana", rows: d.serie_semanal },
        ];
    }

    setChartPeriod(period) {
        this.state.chartPeriod = period;
    }

    get chartPeriod() {
        return this.state.chartPeriod;
    }

    get chartRows() {
        const d = this.state.data;
        if (this.state.chartPeriod === 'mes') return d.serie_mensual;
        if (this.state.chartPeriod === 'año') return d.serie_anual;
        return d.serie_semanal;
    }

    get chartTitle() {
        if (this.state.chartPeriod === 'mes') return 'Pares por mes';
        if (this.state.chartPeriod === 'año') return 'Pares por año';
        return 'Pares por semana';
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
