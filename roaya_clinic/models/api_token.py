from odoo import models, fields, api
import secrets
from datetime import timedelta


class ApiToken(models.Model):
    _name = "api.token"
    _description = "API Access Tokens"
    _order = "id desc"

    name = fields.Char(required=True)
    token = fields.Char(index=True, copy=False, readonly=True)
    user_id = fields.Many2one(
        "res.users", required=True, ondelete="cascade", index=True
    )
    is_active = fields.Boolean(default=True)

    expiry_date = fields.Datetime()
    last_used = fields.Datetime(readonly=True)
    last_ip = fields.Char(readonly=True)

    @api.model
    def create(self, vals):
        if not vals.get("token"):
            vals["token"] = secrets.token_urlsafe(32)

        if not vals.get("expiry_date"):
            vals["expiry_date"] = fields.Datetime.now() + timedelta(days=30)

        return super().create(vals)

    def is_valid(self):
        self.ensure_one()

        if not self.is_active:
            return False

        if self.expiry_date and self.expiry_date < fields.Datetime.now():
            return False

        return True

    def action_regenerate_token(self):
        self.ensure_one()

        self.write(
            {
                "token": secrets.token_urlsafe(32),
                "expiry_date": fields.Datetime.now() + timedelta(days=30),
                "last_used": False,
                "last_ip": False,
            }
        )
