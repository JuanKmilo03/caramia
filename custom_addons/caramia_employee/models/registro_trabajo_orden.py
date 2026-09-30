from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaramiaRegistroTrabajo(models.Model):
    _name = 'cara.mia.registro.trabajo.orden'
    _description = 'Registro de Tiquetes / Trabajo Realizado'
    _order = 'fecha desc, id desc'

    produccion_id = fields.Many2one(
        'cara.mia.produccion', 
        string='Orden de Producción', 
        compute='_compute_produccion_id',
        store=True,
        readonly=True
    )
    
    # Campo principal oculto (lo llenamos automáticamente)
    orden_codigo = fields.Char(string='Código de Orden', required=True)

    # NUEVO: Campo "Fantasma" solo para recibir el texto y dar Enter
    codigo_escaner = fields.Char(string='Escanear Código', store=False)

    codigos_extra_ids = fields.One2many(
        'cara.mia.registro.trabajo.orden.extra', 
        'registro_id', 
        string='Códigos Adicionales'
    )

    fecha = fields.Date(string='Fecha de Registro', default=fields.Date.context_today, required=True)
    total_pares = fields.Integer(related='produccion_id.total_pares', string='Pares', store=True)
    currency_id = fields.Many2one('res.currency', related='produccion_id.currency_id')

    empleado_id = fields.Many2one('cara.mia.empleado', string='Empleado / Operario', required=True)
    tipo_labor_id = fields.Many2one(
        'cara.mia.tipo.labor', related='empleado_id.tipo_labor_id', store=True, string='Labor Realizada', readonly=True
    )

    tarifa_pago = fields.Monetary(string='Tarifa por Par', compute='_compute_tarifa_pago', store=True, currency_field='currency_id')
    subtotal = fields.Monetary(string='Subtotal a Pagar', compute='_compute_subtotal', store=True, currency_field='currency_id')
    
    estado = fields.Selection([
        ('sin_asignar', 'Sin Asignar'),
        ('pendiente', 'Pendiente'),
        ('pagado', 'Registrado en Nómina')
    ], string='Estado', compute='_compute_estado', store=True, default='sin_asignar')

    # ---------------------------------------------------------
    # NUEVA LÓGICA: Al dar Enter, pasa el código a la tabla
    # ---------------------------------------------------------
    @api.onchange('codigo_escaner')
    def _onchange_codigo_escaner(self):
        if self.codigo_escaner:
            codigo = self.codigo_escaner.strip().upper()
            
            # 1. Agrega el código como una nueva línea en la tabla
            self.codigos_extra_ids = [(0, 0, {'orden_codigo': codigo})]
            
            # 2. Llena el campo principal con un texto temporal para que Odoo no bloquee el guardado
            if not self.orden_codigo:
                self.orden_codigo = 'EN_PROCESO'
                
            # 3. Vacía el campo del escáner para el siguiente tiquete
            self.codigo_escaner = False

    @api.constrains('produccion_id')
    def _check_estado_orden_produccion(self):
        for rec in self:
            if rec.produccion_id:
                if rec.produccion_id.state == 'draft':
                    raise ValidationError(f"La Orden '{rec.produccion_id.name}' se encuentra en estado BORRADOR.\nInicie la producción antes de asignar tiquetes.")
                elif rec.produccion_id.state in ('done', 'canceled'):
                    raise ValidationError(f"La Orden '{rec.produccion_id.name}' ya está finalizada o cancelada.")

    @api.depends('orden_codigo')
    def _compute_produccion_id(self):
        for rec in self:
            if rec.orden_codigo and rec.orden_codigo != 'EN_PROCESO':
                codigo_limpio = rec.orden_codigo.strip().upper()
                orden = self.env['cara.mia.produccion'].search([('name', '=', codigo_limpio)], limit=1)
                rec.produccion_id = orden.id if orden else False
            else:
                rec.produccion_id = False

    @api.constrains('orden_codigo', 'produccion_id')
    def _check_orden_valida(self):
        for rec in self:
            if rec.orden_codigo and rec.orden_codigo != 'EN_PROCESO' and not rec.produccion_id:
                raise ValidationError(f"La Orden de Producción '{rec.orden_codigo}' no existe en el sistema.")

    @api.constrains('produccion_id', 'empleado_id')
    def _check_labor_en_orden_produccion(self):
        for rec in self:
            if rec.produccion_id and rec.empleado_id and rec.tipo_labor_id:
                labores_validas = rec.produccion_id.labor_ids.mapped('tipo_labor_id')
                if rec.tipo_labor_id not in labores_validas:
                    raise ValidationError(f"El empleado '{rec.empleado_id.nombre_empleado}' realiza la labor '{rec.tipo_labor_id.name}', pero no está presupuestada en la Orden '{rec.produccion_id.name}'.")

    @api.depends('empleado_id')
    def _compute_estado(self):
        for rec in self:
            if not rec.empleado_id:
                rec.estado = 'sin_asignar'
            elif rec.estado == 'pagado':
                rec.estado = 'pagado'
            else:
                rec.estado = 'pendiente'

    @api.depends('produccion_id', 'tipo_labor_id')
    def _compute_tarifa_pago(self):
        for rec in self:
            if rec.produccion_id and rec.tipo_labor_id:
                linea_labor = rec.produccion_id.labor_ids.filtered(lambda l: l.tipo_labor_id == rec.tipo_labor_id)
                rec.tarifa_pago = linea_labor[:1].tarifa_pago if linea_labor else 0.0
            else:
                rec.tarifa_pago = 0.0

    @api.depends('total_pares', 'tarifa_pago')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.total_pares * rec.tarifa_pago

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            extras = vals.pop('codigos_extra_ids', [])
            valid_codes = []
            
            # Extraer todos los códigos de la tabla
            for extra in extras:
                if extra[0] == 0 and isinstance(extra[2], dict) and extra[2].get('orden_codigo'):
                    valid_codes.append(extra[2]['orden_codigo'].strip().upper())
            
            # Si el usuario llenó la tabla, construimos los registros desde la tabla
            if valid_codes:
                vals['orden_codigo'] = valid_codes[0]
                new_vals_list.append(vals)
                
                # Prevenir duplicados si escaneó el mismo código dos veces en la misma vista
                codigos_agregados = {valid_codes[0]}
                for code in valid_codes[1:]:
                    if code not in codigos_agregados:
                        extra_vals = vals.copy()
                        extra_vals['orden_codigo'] = code
                        new_vals_list.append(extra_vals)
                        codigos_agregados.add(code)
            else:
                if not vals.get('orden_codigo') or vals.get('orden_codigo') == 'EN_PROCESO':
                    raise ValidationError("¡La lista está vacía! Debe escanear al menos un código de orden antes de guardar.")
                vals['orden_codigo'] = vals['orden_codigo'].strip().upper()
                new_vals_list.append(vals)

        # Lógica de validación con el mensaje personalizado de error
        errores_duplicados = []
        combinaciones_vistas = set()

        for v in new_vals_list:
            codigo = v.get('orden_codigo')
            empleado_id = v.get('empleado_id')
            
            if codigo and empleado_id:
                orden = self.env['cara.mia.produccion'].search([('name', '=', codigo)], limit=1)
                empleado = self.env['cara.mia.empleado'].browse(empleado_id)
                labor_id = empleado.tipo_labor_id.id if empleado.tipo_labor_id else False
                
                if orden and labor_id:
                    llave = (orden.id, labor_id)
                    if llave in combinaciones_vistas:
                        errores_duplicados.append(f"{codigo} (Escaneado repetidas veces)")
                        continue
                    combinaciones_vistas.add(llave)

                    existe = self.env['cara.mia.registro.trabajo.orden'].search([
                        ('produccion_id', '=', orden.id),
                        ('tipo_labor_id', '=', labor_id)
                    ], limit=1)
                    if existe:
                        errores_duplicados.append(codigo)

        if errores_duplicados:
            lista_errores = "\n- ".join(set(errores_duplicados))
            raise ValidationError(
                f"No se puede guardar. Las siguientes órdenes ya fueron registradas previamente para este operario/labor:\n\n"
                f"- {lista_errores}\n\n"
                f"Por favor borre las órdenes repetidas de la lista (ícono de papelera) antes de guardar."
            )

        records = super().create(new_vals_list)
        for rec in records:
            if rec.produccion_id:
                rec.produccion_id._check_auto_finish()
        return records

    def write(self, vals):
        if 'orden_codigo' in vals and vals['orden_codigo']:
            vals['orden_codigo'] = vals['orden_codigo'].strip().upper()
        res = super().write(vals)
        for rec in self:
            if rec.produccion_id:
                rec.produccion_id._check_auto_finish()
        return res

    _sql_constraints = [
        ('orden_labor_unica', 'unique(produccion_id, tipo_labor_id)', 'Labor ya registrada')
    ]

class CaramiaProductionInherit(models.Model):
    _inherit = 'cara.mia.produccion'

    registro_trabajo_ids = fields.One2many(
        'cara.mia.registro.trabajo.orden', 'produccion_id', string='Tiquetes Registrados'
    )

    def _check_auto_finish(self):
        for rec in self:
            if rec.state == 'in_progress':
                labores_orden = set(rec.labor_ids.mapped('tipo_labor_id.id'))
                labores_registradas = set(
                    rec.registro_trabajo_ids.filtered(lambda r: r.empleado_id).mapped('tipo_labor_id.id')
                )
                if labores_orden and labores_orden.issubset(labores_registradas):
                    rec.write({'state': 'done', 'fecha_finalizacion': fields.Datetime.now()})

class CaramiaRegistroTrabajoExtra(models.Model):
    _name = 'cara.mia.registro.trabajo.orden.extra'
    _description = 'Códigos Adicionales Temporales'

    registro_id = fields.Many2one('cara.mia.registro.trabajo.orden', ondelete='cascade')
    orden_codigo = fields.Char(string='Código de Orden', required=True)
    alerta_duplicado = fields.Char(compute='_compute_alerta_duplicado')

    @api.onchange('orden_codigo')
    def _onchange_orden_codigo(self):
        if self.orden_codigo:
            self.orden_codigo = self.orden_codigo.strip().upper()

    @api.depends('orden_codigo', 'registro_id.empleado_id')
    def _compute_alerta_duplicado(self):
        for rec in self:
            rec.alerta_duplicado = False
            if rec.orden_codigo and rec.registro_id.empleado_id and rec.registro_id.empleado_id.tipo_labor_id:
                codigo = rec.orden_codigo.strip().upper()
                orden = self.env['cara.mia.produccion'].search([('name', '=', codigo)], limit=1)
                if orden:
                    existe = self.env['cara.mia.registro.trabajo.orden'].search([
                        ('produccion_id', '=', orden.id),
                        ('tipo_labor_id', '=', rec.registro_id.empleado_id.tipo_labor_id.id)
                    ], limit=1)
                    if existe:
                        rec.alerta_duplicado = "Ya registrado para esta labor"