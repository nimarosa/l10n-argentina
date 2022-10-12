from odoo import _, models
from odoo.exceptions import ValidationError


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def comp_consultar(self):
        self.ensure_one()
        if not self.journal_id or not self.l10n_latam_document_type_id:
            raise ValidationError(_("Faltan datos para consultar AFIP"))
        vals = {
            "journal_id": self.journal_id.id,
            "doc_type": self.l10n_latam_document_type_id.id,
        }
        wizard_id = self.env["wizard.comp.consultar"].create(vals)
        return {
            "name": _("Consultar comprobante"),
            "res_model": "wizard.comp.consultar",
            "view_mode": "form",
            "res_id": wizard_id.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
