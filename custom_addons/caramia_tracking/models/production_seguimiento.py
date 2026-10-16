from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta

from markupsafe import Markup, escape

from odoo import api, fields, models

ESTADOS_ACTIVOS = ('draft', 'in_progress', 'stopped')


class CaramiaProductionLabor(models.Model):
    _inherit = 'cara.mia.produccion.labor'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Orden', default=10)


class CaramiaProductionTracking(models.Model):
    _inherit = 'cara.mia.produccion'

    # --- Estado Detenido -------------------------------------------------
    state = fields.Selection(
        selection_add=[('stopped', 'Detenido')],
        ondelete={'stopped': 'set default'},
    )
    fecha_estado = fields.Datetime(
        string='Fecha del último cambio de estado',
        default=fields.Datetime.now, readonly=True, copy=False,
    )

    # La fecha estimada de entrega se digita al crear la orden
    fecha_estimada = fields.Date(string='Fecha Estimada de Entrega', readonly=False)

    # --- Campos de seguimiento -------------------------------------------
    dias_transcurridos = fields.Integer(compute='_compute_tracking', store=True)
    labores_total = fields.Integer(compute='_compute_tracking', store=True)
    labores_hechas = fields.Integer(compute='_compute_tracking', store=True)
    progreso = fields.Float(string='Avance (%)', compute='_compute_tracking', store=True)
    proxima_labor_id = fields.Many2one(
        'cara.mia.tipo.labor', string='Labor actual',
        compute='_compute_tracking', store=True,
    )
    cargo_actual = fields.Char(string='Cargo / Labor actual', compute='_compute_tracking', store=True)
    dias_en_etapa = fields.Integer(string='Días sin avance', compute='_compute_tracking', store=True)
    esta_estancada = fields.Boolean(string='Estancada', compute='_compute_tracking', store=True)
    motivo_estancamiento = fields.Char(compute='_compute_tracking', store=True)
    etapas_html = fields.Html(string='Etapas de avance', compute='_compute_etapas_html', sanitize=False)

    @api.depends(
        'state', 'esta_estancada', 'proxima_labor_id',
        'labor_ids.sequence', 'labor_ids.tipo_labor_id',
        'registro_trabajo_ids.fecha', 'registro_trabajo_ids.tipo_labor_id',
        'registro_trabajo_ids.empleado_id', 'registro_trabajo_ids.empleado_id.nombre_empleado',
    )
    def _compute_etapas_html(self):
        oro, gris, naranja = '#C9A227', '#adb5bd', '#fd7e14'
        for rec in self:
            labores = rec.labor_ids.sorted(lambda l: l.sequence)
            if not labores:
                rec.etapas_html = False
                continue
            hechas = {}
            for r in rec.registro_trabajo_ids.filtered('empleado_id'):
                hechas.setdefault(r.tipo_labor_id.id, r)
            actual = rec.proxima_labor_id.id if rec.state in ('in_progress', 'stopped') else False

            partes = []
            for i, labor in enumerate(labores, 1):
                tid = labor.tipo_labor_id.id
                hecha = tid in hechas
                tip = ''
                es_actual = bool(actual) and tid == actual and not hecha
                if hecha:
                    circulo = f'background:{oro};border:3px solid {oro};color:#fff;'
                    interior = '<i class="fa fa-check"></i>'
                    reg = hechas[tid]
                    pie = reg.fecha.strftime('%d/%m') if reg.fecha else ''
                    txt = '#212529'
                    tip = 'Realizado por: %s' % (reg.empleado_id.nombre_empleado or '')
                elif es_actual:
                    color = naranja if rec.esta_estancada else oro
                    circulo = (f'background:#fff;border:3px solid {color};color:{color};'
                               f'box-shadow:0 0 0 4px {color}33;')
                    interior = str(i)
                    pie = 'En curso'
                    txt = color
                else:
                    circulo = f'background:#fff;border:3px solid {gris};color:{gris};'
                    interior = str(i)
                    pie = ''
                    txt = '#6c757d'
                partes.append(
                    f'<div title="{escape(tip)}" style="display:flex;flex-direction:column;'
                    'align-items:center;min-width:96px;text-align:center;">'
                    '<div style="width:46px;height:46px;border-radius:50%;display:flex;'
                    'align-items:center;justify-content:center;font-weight:700;font-size:18px;'
                    f'{circulo}">{interior}</div>'
                    f'<div style="margin-top:6px;font-size:12px;font-weight:600;color:{txt};">'
                    f'{escape(labor.tipo_labor_id.name or "")}</div>'
                    f'<div style="font-size:11px;color:#6c757d;min-height:14px;">{pie}</div>'
                    '</div>'
                )
                if i < len(labores):
                    flecha = oro if hecha else gris
                    partes.append(
                        '<div style="flex:0 0 26px;height:46px;display:flex;align-items:center;'
                        f'justify-content:center;color:{flecha};"><i class="fa fa-long-arrow-right"></i></div>'
                    )
            rec.etapas_html = Markup(
                '<div style="display:flex;align-items:flex-start;overflow-x:auto;padding:6px 0 4px;">'
                + ''.join(partes) + '</div>'
            )

    # ---------------------------------------------------------------------
    @api.depends(
        'state', 'fecha_creacion', 'fecha_estado', 'fecha_finalizacion',
        'labor_ids.sequence', 'labor_ids.tipo_labor_id',
        'registro_trabajo_ids.fecha', 'registro_trabajo_ids.tipo_labor_id',
        'registro_trabajo_ids.empleado_id',
    )
    def _compute_tracking(self):
        icp = self.env['ir.config_parameter'].sudo()
        lim_borrador = int(icp.get_param('caramia_production.dias_borrador', 3))
        lim_etapa = int(icp.get_param('caramia_production.dias_etapa', 7))
        today = fields.Date.context_today(self)

        for rec in self:
            fin = rec.fecha_finalizacion.date() if rec.fecha_finalizacion else today
            rec.dias_transcurridos = (fin - rec.fecha_creacion).days if rec.fecha_creacion else 0

            labores = rec.labor_ids.sorted(lambda l: l.sequence)
            registros = rec.registro_trabajo_ids.filtered('empleado_id')
            hechas_ids = set(registros.mapped('tipo_labor_id').ids)
            pendientes = labores.filtered(lambda l: l.tipo_labor_id.id not in hechas_ids)
            rec.labores_total = len(labores)
            rec.labores_hechas = len(labores) - len(pendientes)
            rec.progreso = 100.0 * rec.labores_hechas / len(labores) if labores else 0.0
            rec.proxima_labor_id = pendientes[:1].tipo_labor_id

            if rec.state == 'done':
                rec.cargo_actual = 'Finalizada'
            elif rec.state == 'canceled':
                rec.cargo_actual = 'Cancelada'
            elif rec.state == 'draft':
                rec.cargo_actual = 'Sin iniciar'
            else:
                rec.cargo_actual = pendientes[:1].tipo_labor_id.name or 'Finalizada'

            # Días sin avance: desde el último cambio de estado o último registro
            ref_dt = rec.fecha_estado or rec.create_date or fields.Datetime.now()
            base = ref_dt.date()
            fechas = [f for f in registros.mapped('fecha') if f]
            if fechas and max(fechas) > base:
                base = max(fechas)
            dias = (today - base).days
            rec.dias_en_etapa = dias if rec.state in ESTADOS_ACTIVOS else 0

            # Estancamiento
            rec.esta_estancada = False
            rec.motivo_estancamiento = False
            if rec.state == 'draft' and dias >= lim_borrador:
                rec.esta_estancada = True
                rec.motivo_estancamiento = f'En borrador hace {dias} días (límite {lim_borrador}).'
            elif rec.state == 'in_progress' and dias > lim_etapa:
                rec.esta_estancada = True
                rec.motivo_estancamiento = (
                    f'Sin avance en "{rec.cargo_actual}" hace {dias} días (límite {lim_etapa}).'
                )
            elif rec.state == 'stopped' and dias > lim_etapa:
                rec.esta_estancada = True
                rec.motivo_estancamiento = f'Detenida hace {dias} días (límite {lim_etapa}).'

    # --- Cambio de estado -----------------------------------------------
    def write(self, vals):
        if 'state' in vals:
            vals = dict(vals, fecha_estado=fields.Datetime.now())
        return super().write(vals)

    def action_set_stopped(self):
        self.write({'state': 'stopped'})

    def action_resume(self):
        self.write({'state': 'in_progress'})

    # --- Orden de labores desde la referencia ---------------------------
    @api.onchange('referencia_id')
    def _onchange_referencia_id(self):
        self.labor_ids = [(5, 0, 0)]
        if self.referencia_id:
            lineas = []
            labores_ref = self.referencia_id.labor_ids.sorted(lambda l: (l.secuencia, l.id))
            for labor in labores_ref:
                if not labor.tipo_labor_id:
                    continue
                lineas.append((0, 0, {
                    'tipo_labor_id': labor.tipo_labor_id.id,
                    'tarifa_pago': labor.tarifa_pago or 0.0,
                    'sequence': labor.secuencia,
                }))
            self.labor_ids = lineas

    # --- Datos del tablero consolidado ----------------------------------
    @api.model
    def get_tracking_dashboard(self):
        today = fields.Date.context_today(self)
        monday = today - timedelta(days=today.weekday())
        first = today.replace(day=1)

        Registro = self.env['cara.mia.registro.trabajo.orden'].sudo()

        def total(model, domain, campo):
            return model._read_group(domain, [], [campo + ':sum'])[0][0] or 0

        def sums(d1, d2):
            dt1 = datetime.combine(d1, time.min)
            dt2 = datetime.combine(d2 + timedelta(days=1), time.min)
            return {
                # Pares programados: órdenes con fecha estimada en el periodo
                'programado': total(self, [
                    ('fecha_estimada', '>=', d1), ('fecha_estimada', '<=', d2),
                    ('state', '!=', 'canceled')], 'total_pares'),
                # Pares terminados: órdenes finalizadas en el periodo
                'finalizado': total(self, [
                    ('state', '=', 'done'),
                    ('fecha_finalizacion', '>=', dt1), ('fecha_finalizacion', '<', dt2)], 'total_pares'),
                # Pares procesados: suma por cada labor registrada
                'procesado': total(Registro, [
                    ('fecha', '>=', d1), ('fecha', '<=', d2),
                    ('produccion_id', '!=', False)], 'total_pares'),
            }

        def fmt(d):
            return d.strftime('%d/%m')

        semana = sums(monday, monday + timedelta(days=6))
        semana['rango'] = f'{fmt(monday)} - {fmt(monday + timedelta(days=6))}'
        fin_mes = first + relativedelta(months=1, days=-1)
        mes = sums(first, fin_mes)
        mes['rango'] = f'{fmt(first)} - {fmt(fin_mes)}'

        serie_semanal = []
        for i in range(-5, 3):
            ini = monday + timedelta(weeks=i)
            row = sums(ini, ini + timedelta(days=6))
            row.update(label=fmt(ini), actual=(i == 0))
            serie_semanal.append(row)

        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        serie_mensual = []
        for i in range(-3, 3):
            ini = first + relativedelta(months=i)
            row = sums(ini, ini + relativedelta(months=1, days=-1))
            row.update(label=f'{meses[ini.month - 1]} {ini.year}', actual=(i == 0))
            serie_mensual.append(row)

        dom_act = [('state', 'in', ESTADOS_ACTIVOS), ('fecha_estimada', '!=', False)]
        pend_pares = self._read_group(dom_act, [], ['total_pares:sum'])[0][0] or 0
        limite = today + timedelta(days=7)
        entregas = {
            'pendientes': self.search_count(dom_act),
            'pendientes_pares': pend_pares,
            'vencidas': self.search_count(dom_act + [('fecha_estimada', '<', today)]),
            'proximas': self.search_count(dom_act + [
                ('fecha_estimada', '>=', today), ('fecha_estimada', '<=', limite)]),
        }

        lista = []
        for rec in self.search(dom_act, order='fecha_estimada asc, id', limit=12):
            lista.append({
                'id': rec.id,
                'name': rec.name,
                'cliente': rec.cliente_id.display_name or '',
                'pares': rec.total_pares,
                'fecha': str(rec.fecha_estimada),
                'dias': rec.dias_transcurridos,
                'cargo': rec.cargo_actual or '',
                'progreso': round(rec.progreso),
                'estancada': rec.esta_estancada,
                'vencida': rec.fecha_estimada < today,
            })

        return {
            'hoy': str(today),
            'limite_proximas': str(limite),
            'estados_activos': list(ESTADOS_ACTIVOS),
            'semana': semana,
            'mes': mes,
            'serie_semanal': serie_semanal,
            'serie_mensual': serie_mensual,
            'entregas': entregas,
            'estancadas': self.search_count([('esta_estancada', '=', True)]),
            'activas': self.search_count([('state', 'in', ESTADOS_ACTIVOS)]),
            'lista': lista,
            'list_view_id': self.env.ref('caramia_production.view_caramia_production_list').id,
            'form_view_id': self.env.ref('caramia_production.view_caramia_production_form').id,
            'search_view_id': self.env.ref('caramia_tracking.view_caramia_production_search').id,
        }

    @api.model
    def _cron_actualizar_estancadas(self):
        ordenes = self.search([('state', 'in', ESTADOS_ACTIVOS)])
        antes = ordenes.filtered('esta_estancada')
        ordenes._compute_tracking()
        for rec in ordenes.filtered('esta_estancada') - antes:
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=f'Orden estancada: {rec.name}',
                note=rec.motivo_estancamiento,
                user_id=(rec.create_uid or self.env.user).id,
            )

