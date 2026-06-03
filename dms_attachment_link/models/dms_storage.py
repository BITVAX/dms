# Copyright 2026 BITVAX
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DmsStorage(models.Model):
    _inherit = "dms.storage"

    auto_import_attachments = fields.Boolean(
        string="Auto-import attachments",
        help="If enabled, an attachment added to a record that has a directory in "
        "this storage is automatically stored as a DMS file, and the "
        "attachment becomes a link to that DMS file (single binary).",
    )
