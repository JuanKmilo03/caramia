/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class CaramiaDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.user = useService("user");
        this.state = useState({ dashboardData: {} });

        onWillStart(async () => {
            // Llama a tu método Python get_tracking_dashboard
            this.state.dashboardData = await this.orm.call(
                "cara.mia.produccion",
                "get_tracking_dashboard",
                []
            );
        });
    }

    // Acción para el botón superior "Nueva Orden"
    createOrder() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cara.mia.produccion",
            views: [[false, "form"]],
            target: "current",
        });
    }

    // Acción para abrir una orden desde la lista de "Órdenes prioritarias"
    openOrder(orderId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cara.mia.produccion",
            res_id: orderId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

CaramiaDashboard.template = "caramia_tracking.DashboardTemplate";
// Registra el componente como una acción de cliente
registry.category("actions").add("caramia_dashboard_action", CaramiaDashboard);