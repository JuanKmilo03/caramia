/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onWillUpdateProps, useState } from "@odoo/owl";

export class CarteraListController extends ListController {
    static template = "caramia_facturacion.CarteraListView";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.resumen = useState({ facturado: 0, abonado: 0, saldo: 0, moneda: "COP", decimales: 0 });
        onWillStart(() => this.cargarResumen());
        onWillUpdateProps(() => this.cargarResumen());
    }

    async cargarResumen() {
        const datos = await this.orm.call("cara.mia.cuenta.cobro", "get_resumen_cartera", []);
        Object.assign(this.resumen, datos);
    }

    formatear(valor) {
        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: this.resumen.moneda,
            minimumFractionDigits: this.resumen.decimales,
            maximumFractionDigits: this.resumen.decimales,
        }).format(valor || 0);
    }
}

registry.category("views").add("cartera_list", {
    ...listView,
    Controller: CarteraListController,
});