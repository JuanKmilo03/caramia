from odoo import models, fields, api
from odoo.exceptions import UserError


class GuardarReferenciaWizard(models.TransientModel):
    _name = 'caramia.guardar.referencia.wizard'
    _description = 'Guardar o Actualizar Referencia desde Cotización'

    costo_id = fields.Many2one(
        'caramia.costo',
        string='Cotización',
        required=True,
        readonly=True
    )
    modo = fields.Selection([
        ('nueva', 'Crear nueva referencia'),
        ('actualizar', 'Actualizar referencia existente'),
    ], string='¿Qué desea hacer?', default='nueva', required=True)

    nombre_modelo = fields.Char(string='Nombre del Modelo')

    precio_venta_sugerido = fields.Monetary(
        string='Precio de Venta Sugerido',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    referencia_a_actualizar_id = fields.Many2one(
        'cara.mia.referencia',
        string='Referencia a Actualizar',
        domain="[('estado', '=', 'activo')]"
    )
    actualizar_materiales = fields.Boolean(
        string='Actualizar Materiales / Insumos',
        default=True
    )
    actualizar_labores = fields.Boolean(
        string='Actualizar Labores',
        default=True
    )
    actualizar_precio_venta = fields.Boolean(
        string='Actualizar Precio de Venta Sugerido',
        default=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        costo_id = res.get('costo_id') or self.env.context.get('default_costo_id')
        if costo_id:
            costo = self.env['caramia.costo'].browse(costo_id)
            if costo.exists():
                res['costo_id'] = costo.id
                res['precio_venta_sugerido'] = costo.precio_venta_par

                if costo.referencia_id:
                    # Ya hay referencia elegida → modo actualizar
                    res['modo'] = 'actualizar'
                    res['referencia_a_actualizar_id'] = costo.referencia_id.id
                    res['nombre_modelo'] = costo.referencia_id.nombre_modelo
                elif costo.nombre_modelo:
                    # Escribió un modelo nuevo → modo crear
                    res['modo'] = 'nueva'
                    res['nombre_modelo'] = costo.nombre_modelo
                    res['referencia_a_actualizar_id'] = False
        return res
    
    def _sincronizar_referencia(self, ref, costo):
        """Actualiza insumos, labores y precio de una referencia existente."""
        if self.actualizar_precio_venta:
            ref.precio_venta_sugerido = self.precio_venta_sugerido

        if self.actualizar_materiales:
            ref.insumo_ids.unlink()
            for linea in costo.material_ids:
                if not linea.insumo_catalogo_id:
                    continue
                self.env['cara.mia.insumo.referencia'].create({
                    'referencia_id': ref.id,
                    'insumo_catalogo_id': linea.insumo_catalogo_id.id,
                    'cantidad': linea.cantidad_par,
                    'costo_estimado': linea.precio_unitario,
                })

        if self.actualizar_labores:
            ref.labor_ids.unlink()
            for linea in costo.labor_ids:
                if not linea.tipo_labor_id:
                    continue
                self.env['cara.mia.precio.labor.ref'].create({
                    'referencia_id': ref.id,
                    'tipo_labor_id': linea.tipo_labor_id.id,
                    'tarifa_pago': linea.costo_par,
                })

    def action_confirmar(self):
        self.ensure_one()
        costo = self.costo_id
        if not costo:
            raise UserError('No se encontró la cotización.')

        if self.modo == 'nueva':
            nueva_ref = self._crear_nueva_referencia(costo)
            ref = nueva_ref
        else:
            self._actualizar_referencia_existente(costo)
            ref = self.referencia_a_actualizar_id
        costo.write({'referencia_id': ref.id})
        if self.env.context.get('continuar_a_produccion'):
            return costo._crear_orden_produccion()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cara.mia.referencia',
            'res_id': ref.id,
            'view_mode': 'form',
            'target': 'current',
        }
            

    def _crear_nueva_referencia(self, costo):
        if not self.nombre_modelo:
            raise UserError('Debe ingresar un nombre para la nueva referencia.')

        insumo_vals = []
        for linea in costo.material_ids:
            if not linea.insumo_catalogo_id:
                continue
            insumo_vals.append((0, 0, {
                'insumo_catalogo_id': linea.insumo_catalogo_id.id,
                'cantidad':           linea.cantidad_par,
                'costo_estimado':     linea.costo_par,
            }))

        labor_vals = []
        for linea in costo.labor_ids:
            if not linea.tipo_labor_id:
                continue
            labor_vals.append((0, 0, {
                'tipo_labor_id': linea.tipo_labor_id.id,
                'tarifa_pago':   linea.costo_par,
            }))

        return self.env['cara.mia.referencia'].create({
            'nombre_modelo':         self.nombre_modelo,
            'precio_venta_sugerido': self.precio_venta_sugerido or costo.precio_venta_par,
            'estado':                'activo',
            'insumo_ids':            insumo_vals,
            'labor_ids':             labor_vals,
        })

    def _actualizar_referencia_existente(self, costo):
        ref = self.referencia_a_actualizar_id
        if not ref:
            raise UserError('Debe seleccionar una referencia a actualizar.')
        self._sincronizar_referencia(ref, costo)