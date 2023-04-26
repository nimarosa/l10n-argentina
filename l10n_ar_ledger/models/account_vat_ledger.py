##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class AccountVatLedger(models.Model):
    _name = "account.vat.ledger"
    _description = "Account VAT Ledger"
    _inherit = ["mail.thread"]
    _order = "date_from desc"

    digital_skip_invoice_tests = fields.Boolean(
        string="Skip invoice test?",
        help="If you skip invoice tests probably you will have errors when "
        "loading the files in digital.",
    )
    digital_skip_lines = fields.Char(
        string="Lines list to skip with digital files",
        help="Enter a list of lines, for eg '1, 2, 3'. If you skip some lines "
        "you would need to enter them manually",
    )
    REGDIGITAL_CV_ALICUOTAS = fields.Text(
        "REGDIGITAL_CV_ALICUOTAS",
        readonly=True,
    )
    REGDIGITAL_CV_COMPRAS_IMPORTACIONES = fields.Text(
        "REGDIGITAL_CV_COMPRAS_IMPORTACIONES",
        readonly=True,
    )
    REGDIGITAL_CV_CBTE = fields.Text(
        "REGDIGITAL_CV_CBTE",
        readonly=True,
    )
    digital_vouchers_file = fields.Binary(
        "Digital Voucher File", compute="_compute_digital_files", readonly=True
    )
    digital_vouchers_filename = fields.Char(
        "Digital Voucher Filename",
        compute="_compute_digital_files",
    )
    digital_aliquots_file = fields.Binary(
        "Digital Aliquots File", compute="_compute_digital_files", readonly=True
    )
    digital_aliquots_filename = fields.Char(
        "Digital Aliquots Filename",
        readonly=True,
        compute="_compute_digital_files",
    )
    digital_import_aliquots_file = fields.Binary(
        "Digital Import Aliquots File", compute="_compute_digital_files", readonly=True
    )
    digital_import_aliquots_filename = fields.Char(
        "Digital Import Aliquots File",
        readonly=True,
        compute="_compute_digital_files",
    )
    prorate_tax_credit = fields.Boolean("Prorate Tax Credit")
    name = fields.Char("Name", compute="_compute_name")
    reference = fields.Char("Reference")
    type = fields.Selection(
        [("sale", "Sale"), ("purchase", "Purchase")], "Type", required=True
    )
    date_from = fields.Date(
        string="Date From",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Date(
        string="Date To",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    journal_ids = fields.Many2many(
        "account.journal",
        "account_vat_ledger_journal_rel",
        "vat_ledger_id",
        "journal_id",
        string="Journals",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    invoice_ids = fields.Many2many(
        "account.move", string="Invoices", compute="_compute_invoices"
    )
    attachment_ids = fields.Many2many(comodel_name="ir.attachment", string="Adjuntos")
    state = fields.Selection(
        [("draft", "Draft"), ("presented", "Presented"), ("cancel", "Cancelled")],
        "State",
        required=True,
        default="draft",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env["res.company"]._company_default_get(
            "account.vat.ledger"
        ),
    )

    def _compute_name(self):
        for record in self:
            ledger_type = _("IVA Ventas") if record.type == "sale" else _("IVA Compras")
            date_from_str = (
                fields.Date.from_string(record.date_from).strftime("%d/%m/%Y")
                if record.date_from
                else ""
            )
            date_to_str = (
                fields.Date.from_string(record.date_to).strftime("%d/%m/%Y")
                if record.date_to
                else ""
            )
            name = _("%s / Periodo: %s - %s") % (
                ledger_type,
                date_from_str,
                date_to_str,
            )
            if record.reference:
                name = f"{name} (Ref.: {record.reference})"
            record.name = name

    @api.depends("journal_ids", "date_from", "date_to")
    def _compute_invoices(self):
        self.invoice_ids = self.env["account.move"].search(
            [
                ("state", "not in", ["draft", "cancel"]),
                ("name", "!=", False),
                ("journal_id", "in", self.journal_ids.ids),
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
            ],
            order="invoice_date asc, name asc, id asc",
        )

    # def _compute_digital_files(self):
    #     self.ensure_one()
    #     if self.REGDIGITAL_CV_ALICUOTAS:
    #         self.digital_aliquots_filename = _("%s_ALICUOTAS_%s.txt") % (
    #             self.type == "sale" and "VENTAS" or "COMPRAS",
    #             self.date_to.strftime("%Y-%m"),
    #         )
    #         self.digital_aliquots_file = encodebytes(
    #             self.REGDIGITAL_CV_ALICUOTAS.encode("ISO-8859-1")
    #         )
    #     else:
    #         self.digital_aliquots_file = False
    #         self.digital_aliquots_filename = False
    #     if self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES:
    #         self.digital_import_aliquots_filename = _("%s_ALIC_IMPO_%s.txt") % (
    #             self.type == "sale" and "VENTAS" or "COMPRAS",
    #             self.date_to.strftime("%Y-%m"),
    #         )
    #         self.digital_import_aliquots_file = encodebytes(
    #             self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES.encode("ISO-8859-1")
    #         )
    #     else:
    #         self.digital_import_aliquots_file = False
    #         self.digital_import_aliquots_filename = False
    #     if self.REGDIGITAL_CV_CBTE:
    #         self.digital_vouchers_filename = _("%s_CBTES_%s.txt") % (
    #             self.type == "sale" and "VENTAS" or "COMPRAS",
    #             self.date_to.strftime("%Y-%m"),
    #         )
    #         self.digital_vouchers_file = encodebytes(
    #             self.REGDIGITAL_CV_CBTE.encode("ISO-8859-1")
    #         )
    #     else:
    #         self.digital_vouchers_file = False
    #         self.digital_vouchers_filename = False

    def _compute_digital_files(self):
        self.ensure_one()
        file_type = "VENTAS" if self.type == "sale" else "COMPRAS"
        date_str = self.date_to.strftime("%Y-%m")

        def update_file_properties(file_content, file_name_attr, file_attr):
            if file_content:
                setattr(
                    self,
                    file_name_attr,
                    _(f"{file_type}_{file_name_attr}_{date_str}.txt"),
                )
                setattr(self, file_attr, encodebytes(file_content.encode("ISO-8859-1")))
            else:
                setattr(self, file_name_attr, False)
                setattr(self, file_attr, False)

        update_file_properties(
            self.REGDIGITAL_CV_ALICUOTAS,
            "digital_aliquots_filename",
            "digital_aliquots_file",
        )
        update_file_properties(
            self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES,
            "digital_import_aliquots_filename",
            "digital_import_aliquots_file",
        )
        update_file_properties(
            self.REGDIGITAL_CV_CBTE,
            "digital_vouchers_filename",
            "digital_vouchers_file",
        )

    def compute_digital_data(self):
        invoices = self.get_digital_invoices()
        self._check_partners(invoices)
        self._build_LID_ALIC(invoices)
        self._build_LID_CBTE(invoices)

    def _build_LID_ALIC(self, invoices):
        self.ensure_one()
        result = []
        result_impo_purchases = []

        for invoice in invoices:
            for tax in invoice._get_vat():
                row = []

                if self.type == "purchase":
                    if invoice.l10n_latam_document_type_id == "66":
                        impo_purchase_row = [
                            (invoice.l10n_latam_document_number or "").rjust(16, "0"),
                            self.format_amount(tax["BaseImp"]),
                            str(tax["Id"]),
                            self.format_amount(tax["Importe"]),
                        ]
                        result_impo_purchases.append(impo_purchase_row)
                    else:
                        row.extend(
                            [
                                str(invoice.l10n_latam_document_type_id.code).zfill(3),
                                self.get_point_of_sale(invoice),
                                "{:0>20d}".format(int(invoice.name.split("-")[2])),
                                self.get_partner_document_code(
                                    invoice.commercial_partner_id
                                ),
                                self.get_partner_document_number(
                                    invoice.commercial_partner_id
                                ),
                            ]
                        )
                else:
                    row.extend(
                        [
                            "{:0>3d}".format(
                                int(invoice.l10n_latam_document_type_id.code)
                            ),
                            self.get_point_of_sale(invoice),
                            "{:0>20d}".format(int(invoice.name.split("-")[2])),
                        ]
                    )
                row.extend(
                    [
                        self.format_amount(tax["BaseImp"]),
                        "{:0>4d}".format(int(tax["Id"])),
                        self.format_amount(tax["Importe"]),
                    ]
                )
            result.append("".join(row))
        self.REGDIGITAL_CV_ALICUOTAS = "\r\n".join(result)
        self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES = "\r\n".join(result_impo_purchases)

    def _build_LID_CBTE(self, invoices):
        self.ensure_one()
        result = []
        for inv in invoices:
            invoice_document_number = int(inv.name.split("-")[2])
            invoice_amounts = inv._l10n_ar_get_amounts()
            row = [
                # Ventas/Compras - Campo 1: Fecha de comprobante
                fields.Date.from_string(inv.invoice_date).strftime("%Y%m%d"),
                # Ventas/Compras - Campo 2: Tipo de Comprobante
                "{:0>3d}".format(int(inv.l10n_latam_document_type_id.code)),
                # Ventas/Compras - Campo 3: Punto de venta
                self.get_point_of_sale(inv),  # TODO: Ver
                # Ventas/Compras - Campo 4: Número de Comprobante
                # TODO: Ver el metodo para obtenerlo
                "{:0>20d}".format(invoice_document_number),
            ]
            if self.type == "purchase":
                # Compras - Campo 5: Despacho de importacion
                row.append(
                    (inv.l10n_latam_document_number or inv.number or "").rjust(16, "0")
                ),  # TODO: Ver el metodo para obtenerlo
            else:
                # Ventas - Campo 5: Numero de comprobante hasta
                row.append("{:0>20d}".format(invoice_document_number)),
            row += [
                # Ventas/Compras - Campo 6: Código de documento del vendedor/comprador
                self.get_partner_document_code(inv.commercial_partner_id),
                # Ventas/Compras Campo 7: Número de Identificación del vendedor/comprador
                self.get_partner_document_number(inv.commercial_partner_id),
                # Ventas/Compras Campo 8: Apellido y Nombre del vendedor.
                inv.commercial_partner_id.name.ljust(30, " ")[:30],
                # Ventas/Compras Campo 9: Importe Total de la Operación
                self.format_amount(inv.amount_total),
            ]
            if self.type == "sale":
                row += [
                    # Ventas - Campo 10: Importe no gravado
                    self.format_amount(invoice_amounts["vat_untaxed_base_amount"]),
                    # Ventas - Campo 11: Percepcion a no categorizados - TODO: No implementado
                    self.format_amount(0),
                    # Ventas - Campo 12: Importe de operaciones exentas
                    self.format_amount(invoice_amounts["vat_exempt_base_amount"]),
                    # Ventas - Campo 13: Importe de percepciones impuestos nacionales
                    self.format_amount(invoice_amounts["profits_perc_amount"]),
                    # Ventas - Campo 14: Importe de percepciones de ingresos brutos
                    self.format_amount(invoice_amounts["iibb_perc_amount"]),
                ]
            else:
                row += [
                    # Compras - Campo 10: Importe no gravado
                    self.format_amount(invoice_amounts["vat_untaxed_base_amount"]),
                    # Compras - Campo 11: Importe de operaciones exentas
                    self.format_amount(invoice_amounts["vat_exempt_base_amount"]),
                    # Compras - Campo 12: Importe de percecpiones de IVA
                    self.format_amount(invoice_amounts["vat_perc_amount"]),
                    # Compras - Campo 13: Importe de percepciones impuestos nacionales
                    self.format_amount(invoice_amounts["profits_perc_amount"]),
                    # Compras - Campo 14: Importe de percepciones de ingresos brutos
                    self.format_amount(invoice_amounts["iibb_perc_amount"]),
                ]
            row += [
                # Ventas/Compras - Campo 15: Importe de percepciones de impuestos municipales
                self.format_amount(invoice_amounts["mun_perc_amount"]),
                # Ventas/Compras - Campo 16: Importe de impuestos internos
                self.format_amount(invoice_amounts["intern_tax_amount"]),
                # Ventas/Compras - Campo 17: Código de Moneda
                inv.currency_id.l10n_ar_afip_code,
                # Ventas/Compras - Campo 18: Tipo de Cambio
                self.format_amount(inv.l10n_ar_currency_rate, padding=10, decimals=6),
                # Ventas/Compras - Campo 19: Cantidad de alícuotas de IVA
                str(len(inv._get_vat())),
                # Ventas/Compras - Campo 20: Código de operación. TODO: Hardcoded "0"
                "0",
            ]
            if self.type == "purchase":
                # Compras - Campo 21: Credito fiscal computable
                row.append(self.format_amount(invoice_amounts["vat_amount"]))
            # Ventas/Compras - Campo 21/22: Otros impuestos
            row.append(self.format_amount(invoice_amounts["other_taxes_amount"]))
            if self.type == "sale":
                # Ventas: Campo 22: Vencimiento del comprobante
                row.append(
                    fields.Date.from_string(
                        inv.invoice_date_due or inv.invoice_date
                    ).strftime("%Y%m%d")
                )
                # TODO: Ver casos donde no hay vencimiento
            if self.type == "purchase":
                # Compras - Campo 23: CUIT Emisor / Corredor - # TODO: No implementado
                row.append(self.format_amount(0, padding=11))
                # Compras - Campo 24: Denominacion emisor / corredor - # TODO: No implementado
                row.append("".ljust(30, " ")[:30])
                # Compras - Campo 25: IVA Comision - # TODO: No implementado
                row.append(self.format_amount(0))
            result.append("".join(row))
        self.REGDIGITAL_CV_CBTE = "\r\n".join(result)

    def _check_partners(self, invoices):
        if self.type == "purchase":
            partners = invoices.mapped("commercial_partner_id").filtered(
                lambda r: r.l10n_latam_identification_type_id.l10n_ar_afip_code
                in (False, 99)
                or not r.vat
            )
            if partners:
                partner_list = "\r\n".join(
                    [f"[{p.id}] {p.display_name}" for p in partners]
                )
                raise ValidationError(
                    _(
                        "On purchase digital, partner document type is mandatory "
                        "and it must be different from 99. "
                        "Partners: \r\n\r\n"
                        f"{partner_list}"
                    )
                )

    def format_amount(self, amount, padding=15, decimals=2):
        template = amount < 0 and "-{:0>%dd}" % (padding - 1) or "{:0>%dd}" % (padding)
        return template.format(int(round(abs(amount) * 10**decimals, decimals)))

    def get_digital_invoices(self, return_skiped=False):
        self.ensure_one()
        return self.env["account.move"].search(
            [
                ("l10n_latam_document_type_id.export_to_digital", "=", True),
                ("id", "in", self.invoice_ids.ids),
            ],
            order="invoice_date asc",
        )
        # if self.digital_skip_lines:
        #     skip_lines = literal_eval(self.digital_skip_lines)
        #     if isinstance(skip_lines, int):
        #         skip_lines = [skip_lines]
        #     to_skip = invoices.browse()
        #     for line in skip_lines:
        #         to_skip += invoices[line - 1]
        #     if return_skiped:
        #         return to_skip
        #     invoices -= to_skip
        # return invoices

    def get_partner_document_code(self, partner):
        if partner.l10n_ar_afip_responsibility_type_id.code == "5":
            return str(
                partner.l10n_latam_identification_type_id.l10n_ar_afip_code
            ).zfill(2)
        return "80"

    def get_partner_document_number(self, partner):
        number = partner.vat
        if partner.l10n_ar_afip_responsibility_type_id.code == "5":
            number = re.sub("[^0-9]", "", number or "")
        if number is not False:
            return number.rjust(20, "0")
        else:
            raise ValidationError(
                _(
                    f"""Partner {partner.name} has not
                    CUIT/CUIL or DNI. Required
                    for VAT Ledger Book."""
                )
            )

    def get_point_of_sale(self, invoice):
        if self.type == "sale":
            return "{:0>5d}".format(invoice.journal_id.l10n_ar_afip_pos_number)
        return invoice.l10n_latam_document_number[:5]
