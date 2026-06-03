# Copyright 2026 BITVAX
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    auto_import_attachments = fields.Boolean(
        string="Auto-import attachments",
        help="If enabled, attachments added to the linked record are stored as DMS "
        "files. Applies to this directory and all its sub-directories "
        "(inherited). If unset on the whole chain, the storage default applies.",
    )

    def _dms_auto_import_enabled(self):
        """True if this directory or any ancestor opts in; else the storage default."""
        self.ensure_one()
        node = self
        visited = set()
        while node and node.id not in visited:
            visited.add(node.id)
            if node.auto_import_attachments:
                return True
            node = node.parent_id
        return self.storage_id.auto_import_attachments
