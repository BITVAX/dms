# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class DmsFile(models.Model):
    _inherit = "dms.file"

    def write(self, vals):
        res = super().write(vals)
        if "active" in vals:
            for dms_file in self:
                if not dms_file.active:
                    dms_file._dms_link_remove_bridges()
                else:
                    dms_file._dms_link_recreate_bridge()
        return res

    def _dms_link_remove_bridges(self):
        self.env["ir.attachment"].search([("dms_file_id", "in", self.ids)]).unlink()

    def _dms_link_recreate_bridge(self):
        for dms_file in self:
            directory = dms_file.directory_id
            visited = set()
            while directory and directory.id not in visited:
                visited.add(directory.id)
                if directory.res_model and directory.res_id:
                    dms_file.with_context(
                        active_model=directory.res_model,
                        active_id=directory.res_id,
                    ).action_create_attachment_from_record()
                    break
                directory = directory.parent_id

    def _prepare_ir_attachment_values(self):
        return {
            "dms_file_id": self.id,
            "name": self.name,
            "res_model": self.env.context.get("active_model"),
            "res_id": self.env.context.get("active_id"),
        }

    def action_create_attachment_from_record(self):
        if not self.active:
            return self.env["ir.attachment"]
        return self.env["ir.attachment"].create(self._prepare_ir_attachment_values())
