# Copyright 2026 BITVAX
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo.addons.base.tests.common import BaseCommon


class TestDmsReverseArchive(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.env["dms.storage"].create(
            {
                "name": "Test Storage",
                "save_type": "database",
                "auto_import_attachments": True,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.directory = cls.env["dms.directory"].create(
            {
                "name": "Test Dir",
                "storage_id": cls.storage.id,
                "is_root_directory": True,
                "res_model": "res.partner",
                "res_id": cls.partner.id,
            }
        )

    def _new_attachment(self, **kw):
        vals = {
            "name": "doc.pdf",
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "datas": base64.b64encode(b"hello"),
        }
        vals.update(kw)
        return self.env["ir.attachment"].create(vals)

    def test_reverse_creates_single_binary(self):
        att = self._new_attachment()
        self.assertTrue(
            att.dms_file_id, "el adjunto debe quedar re-apuntado a un dms.file"
        )
        self.assertEqual(att.dms_file_id.directory_id, self.directory)
        self.assertEqual(att.datas, base64.b64encode(b"hello"))
        bridges = self.env["ir.attachment"].search(
            [("dms_file_id", "=", att.dms_file_id.id)]
        )
        self.assertEqual(bridges, att)

    def test_optin_required(self):
        self.storage.auto_import_attachments = False
        self.directory.auto_import_attachments = False
        att = self._new_attachment()
        self.assertFalse(
            att.dms_file_id, "sin opt-in en carpeta ni storage no sincroniza"
        )

    def test_skip_technical(self):
        att = self._new_attachment(res_field="image_1920")
        self.assertFalse(att.dms_file_id)
        other = self.env["ir.attachment"].create(
            {
                "name": "x.pdf",
                "res_model": "res.company",
                "res_id": self.env.company.id,
                "datas": base64.b64encode(b"x"),
            }
        )
        self.assertFalse(other.dms_file_id)

    def test_no_loop_pointer(self):
        att = self._new_attachment()
        bridges = self.env["ir.attachment"].search(
            [("dms_file_id", "=", att.dms_file_id.id)]
        )
        self.assertEqual(len(bridges), 1)

    def test_archive_removes_bridge_keeps_dms(self):
        att = self._new_attachment()
        dms_file = att.dms_file_id
        dms_file.active = False
        self.assertFalse(
            self.env["ir.attachment"].search([("dms_file_id", "=", dms_file.id)]),
            "el puente se quita de Adjuntos",
        )
        self.assertTrue(dms_file.with_context(active_test=False).exists())
        self.assertFalse(dms_file.active, "sigue en DMS, solo archivado")

    def test_unarchive_recreates_bridge(self):
        att = self._new_attachment()
        dms_file = att.dms_file_id
        dms_file.active = False
        dms_file.active = True
        bridge = self.env["ir.attachment"].search([("dms_file_id", "=", dms_file.id)])
        self.assertEqual(len(bridge), 1, "se recrea el puente")
        self.assertEqual(bridge.res_id, self.partner.id)

    def test_forward_skips_inactive(self):
        dms_file = (
            self.env["dms.file"]
            .with_context(dms_skip_attachment_link=True)
            .create(
                {
                    "name": "y.pdf",
                    "directory_id": self.directory.id,
                    "content": base64.b64encode(b"y"),
                    "active": False,
                }
            )
        )
        res = dms_file.action_create_attachment_from_record()
        self.assertFalse(res, "un dms.file inactivo no genera puente")

    def test_walkup_parent_enables(self):
        self.storage.auto_import_attachments = False
        self.directory.auto_import_attachments = True  # carpeta padre habilitada
        partner2 = self.env["res.partner"].create({"name": "Child P"})
        child_dir = self.env["dms.directory"].create(
            {
                "name": "Child Dir",
                "storage_id": self.storage.id,
                "parent_id": self.directory.id,
                "res_model": "res.partner",
                "res_id": partner2.id,
            }
        )
        att = self.env["ir.attachment"].create(
            {
                "name": "c.pdf",
                "res_model": "res.partner",
                "res_id": partner2.id,
                "datas": base64.b64encode(b"c"),
            }
        )
        self.assertTrue(att.dms_file_id, "hereda del ancestro habilitado (walk-up)")
        self.assertEqual(att.dms_file_id.directory_id, child_dir)

    def test_storage_fallback(self):
        # storage True, directory sin flag y sin parent -> fallback al storage
        att = self._new_attachment()
        self.assertTrue(att.dms_file_id, "fallback al flag del storage")
