# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    dms_file_id = fields.Many2one(comodel_name="dms.file")

    @api.depends("dms_file_id", "dms_file_id.content")
    def _compute_datas(self):
        """Get the contents of the attachment directly from the DMS file."""
        _self = self.filtered("dms_file_id")
        res = super(IrAttachment, (self - _self))._compute_datas()
        for item in _self:
            item.datas = item.dms_file_id.content
        return res

    @api.model_create_multi
    def create(self, vals_list):
        attachments = super().create(vals_list)
        attachments._dms_link_sync_from_attachment()
        return attachments

    def _dms_link_sync_from_attachment(self):
        for att in self:
            if att.dms_file_id or att.res_field:
                continue
            if not att.res_model or not att.res_id or not att.datas:
                continue
            directory = att._dms_link_target_directory()
            if not directory:
                continue
            dms_file = (
                self.env["dms.file"]
                .with_context(
                    dms_skip_attachment_link=True,
                )
                .create(
                    {
                        "name": att.name,
                        "directory_id": directory.id,
                        "content": att.datas,
                    }
                )
            )
            # Two separate writes on purpose: writing the computed `datas` and its
            # dependency `dms_file_id` in the SAME write is order-undefined and can
            # leave `datas` cached empty. First clear the stored binary, then point
            # to the dms.file so `_compute_datas` reads the content from it.
            att.write({"datas": False})
            att.write({"dms_file_id": dms_file.id})

    def _dms_link_target_directory(self):
        """Return the first directory linked to this attachment's record that has
        auto-import enabled (own flag, an ancestor's flag, or the storage default).

        A record may have more than one linked directory (e.g. one per storage),
        so we cannot just take the first match: we must pick one that actually
        opts in. If none does, return an empty recordset (no sync).
        """
        self.ensure_one()
        directories = self.env["dms.directory"].search(
            [
                ("res_model", "=", self.res_model),
                ("res_id", "=", self.res_id),
            ]
        )
        for directory in directories:
            if directory._dms_auto_import_enabled():
                return directory
        return self.env["dms.directory"]
