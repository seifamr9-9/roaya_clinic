from odoo import models, fields, api
import io
import base64
from datetime import date

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class DailyCensusWizard(models.TransientModel):
    _name = "daily.census.wizard"
    _description = "Daily Census Report Wizard"

    date = fields.Date(
        string="Census Date",
        required=True,
        default=fields.Date.today,
    )

    excel_file = fields.Binary(string="Download Excel", readonly=True)
    file_name = fields.Char(string="File Name", readonly=True)
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        default="draft",
    )

    def action_generate_excel(self):
        self.ensure_one()

        appointments = self.env["clinic.appointment"].search(
            [("date", "=", self.date)]
        )
        charges = self.env["clinic.charge"].search(
            [("appointment_id.date", "=", self.date)]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # ── Formats ──────────────────────────────────────────────────────────
        title_fmt = workbook.add_format({
            "bold": True, "font_size": 14,
            "align": "center", "valign": "vcenter",
            "bg_color": "#2E75B6", "font_color": "white",
        })
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#D6E4F0",
            "border": 1, "align": "center",
        })
        cell_fmt = workbook.add_format({"border": 1})
        money_fmt = workbook.add_format({
            "border": 1, "num_format": "#,##0.00"
        })
        total_fmt = workbook.add_format({
            "bold": True, "border": 1,
            "bg_color": "#E2EFDA", "num_format": "#,##0.00",
        })
        apt_title_fmt = workbook.add_format({
            "bold": True, "font_size": 12,
            "bg_color": "#1F4E79", "font_color": "white",
            "border": 1, "valign": "vcenter",
        })
        section_fmt = workbook.add_format({
            "bold": True, "bg_color": "#BDD7EE",
            "border": 1,
        })
        label_fmt = workbook.add_format({
            "bold": True, "border": 1,
            "bg_color": "#F2F2F2",
        })
        value_fmt = workbook.add_format({"border": 1})
        chg_total_fmt = workbook.add_format({
            "bold": True, "border": 1,
            "bg_color": "#E2EFDA", "num_format": "#,##0.00",
        })
        chg_total_label_fmt = workbook.add_format({
            "bold": True, "border": 1,
            "bg_color": "#E2EFDA",
        })

        # ── Helpers ───────────────────────────────────────────────────────────
        def float_to_time(f):
            h = int(f)
            m = int((f - h) * 60)
            return f"{h:02d}:{m:02d}"

        def state_label(s):
            return {
                "draft": "Draft", "confirmed": "Confirmed",
                "checked_in": "Checked In", "in_progress": "In Progress",
                "done": "Done", "cancelled": "Cancelled", "no_show": "No Show",
            }.get(s, s or "")

        def charge_state_label(s):
            return {"draft": "Draft", "pending": "Pending", "paid": "Paid"}.get(s, s or "")

        def line_type_label(t):
            return {
                "consultation": "Consultation", "lab": "Lab",
                "prescription": "Prescription", "other": "Other",
            }.get(t, t or "")

        # ── Summary Sheet ─────────────────────────────────────────────────────
        ws_sum = workbook.add_worksheet("Summary")
        ws_sum.merge_range("A1:B1", f"Daily Census Report – {self.date}", title_fmt)
        ws_sum.set_row(0, 30)
        ws_sum.set_column("A:A", 30)
        ws_sum.set_column("B:B", 20)

        total_revenue = sum(charges.mapped("total_amount"))
        paid_revenue = sum(charges.filtered(lambda c: c.state == "paid").mapped("total_amount"))
        pending_revenue = sum(charges.filtered(lambda c: c.state == "pending").mapped("total_amount"))

        summary_data = [
            ("Total Appointments", len(appointments)),
            ("Confirmed", len(appointments.filtered(lambda a: a.state == "confirmed"))),
            ("Done", len(appointments.filtered(lambda a: a.state == "done"))),
            ("Cancelled", len(appointments.filtered(lambda a: a.state == "cancelled"))),
            ("No Show", len(appointments.filtered(lambda a: a.state == "no_show"))),
            ("", ""),
            ("Total Revenue", total_revenue),
            ("Paid", paid_revenue),
            ("Pending", pending_revenue),
        ]

        for row, (label, value) in enumerate(summary_data, start=2):
            ws_sum.write(row, 0, label, header_fmt)
            if isinstance(value, float):
                ws_sum.write(row, 1, value, money_fmt)
            else:
                ws_sum.write(row, 1, value, cell_fmt)

        # ── Appointments Sheet ────────────────────────────────────────────────
        ws_app = workbook.add_worksheet("Appointments")
        ws_app.merge_range(0, 0, 0, 7, f"Appointments – {self.date}", title_fmt)
        ws_app.set_row(0, 30)
        ws_app.set_column("A:A", 20)
        ws_app.set_column("B:B", 25)
        ws_app.set_column("C:C", 25)
        ws_app.set_column("D:D", 20)
        ws_app.set_column("E:F", 12)
        ws_app.set_column("G:G", 15)
        ws_app.set_column("H:H", 15)


        app_headers = ["#", "Patient", "Doctor", "Specialty", "Start", "End", "State", "Ref"]
        for col, h in enumerate(app_headers):
            ws_app.write(1, col, h, header_fmt)

        for i, apt in enumerate(appointments, start=1):
            ws_app.write(i + 1, 0, i, cell_fmt)
            ws_app.write(i + 1, 1, apt.patient_id.name or "", cell_fmt)
            ws_app.write(i + 1, 2, apt.doctor_id.name or "", cell_fmt)
            ws_app.write(i + 1, 3, apt.specialty_id.name or "", cell_fmt)
            ws_app.write(i + 1, 4, float_to_time(apt.start_time), cell_fmt)
            ws_app.write(i + 1, 5, float_to_time(apt.end_time), cell_fmt)
            ws_app.write(i + 1, 6, state_label(apt.state), cell_fmt)
            ws_app.write(i + 1, 7, apt.name or "", cell_fmt)

        r = len(appointments) + 3

       
        for apt in appointments:

            # Title
            ws_app.merge_range(r, 0, r, 7,
                               f"Appointment: {apt.name or 'New'}  |  {apt.patient_id.name or ''}  |  {self.date}",
                               apt_title_fmt)
            ws_app.set_row(r, 25)
            r += 1

            # Patient
            ws_app.merge_range(r, 0, r, 7, "Patient", section_fmt)
            r += 1
            ws_app.write(r, 0, "Name", label_fmt)
            ws_app.merge_range(r, 1, r, 3, apt.patient_id.name or "", value_fmt)
            ws_app.write(r, 4, "Phone", label_fmt)
            ws_app.merge_range(r, 5, r, 7, apt.patient_id.phone or "", value_fmt)
            r += 1

            # Doctor
            ws_app.merge_range(r, 0, r, 7, "Doctor", section_fmt)
            r += 1
            ws_app.write(r, 0, "Name", label_fmt)
            ws_app.merge_range(r, 1, r, 3, f"Dr. {apt.doctor_id.name or ''}", value_fmt)
            ws_app.write(r, 4, "Specialty", label_fmt)
            ws_app.merge_range(r, 5, r, 7, apt.specialty_id.name or "", value_fmt)
            r += 1

            # Appointment Details
            ws_app.merge_range(r, 0, r, 7, "Appointment Details", section_fmt)
            r += 1
            ws_app.write(r, 0, "Ref", label_fmt)
            ws_app.merge_range(r, 1, r, 3, apt.name or "", value_fmt)
            ws_app.write(r, 4, "State", label_fmt)
            ws_app.merge_range(r, 5, r, 7, state_label(apt.state), value_fmt)
            r += 1
            ws_app.write(r, 0, "Date", label_fmt)
            ws_app.merge_range(r, 1, r, 3, str(apt.date or ""), value_fmt)
            ws_app.write(r, 4, "Time", label_fmt)
            ws_app.merge_range(r, 5, r, 7,
                               f"{float_to_time(apt.start_time)} - {float_to_time(apt.end_time)}",
                               value_fmt)
            r += 1

            if apt.reason:
                ws_app.write(r, 0, "Reason", label_fmt)
                ws_app.merge_range(r, 1, r, 7, apt.reason or "", value_fmt)
                r += 1

            if apt.notes:
                ws_app.write(r, 0, "Notes", label_fmt)
                ws_app.merge_range(r, 1, r, 7, apt.notes or "", value_fmt)
                r += 1

            # Charges
            if apt.charge_ids:
                ws_app.merge_range(r, 0, r, 7, "Charges", section_fmt)
                r += 1

                chg_headers = ["Ref", "Type", "Amount", "Late Fee", "Total",
                               "Due Date", "Payment Method", "Status"]
                for col, h in enumerate(chg_headers):
                    ws_app.write(r, col, h, header_fmt)
                r += 1

                apt_total = 0
                for chg in apt.charge_ids:
                    ws_app.write(r, 0, chg.name or "", cell_fmt)
                    ws_app.write(r, 1, line_type_label(chg.line_type), cell_fmt)
                    ws_app.write(r, 2, chg.amount, money_fmt)
                    ws_app.write(r, 3, chg.late_fee, money_fmt)
                    ws_app.write(r, 4, chg.total_amount, money_fmt)
                    ws_app.write(r, 5, str(chg.due_date or ""), cell_fmt)
                    ws_app.write(r, 6, chg.payment_method or "", cell_fmt)
                    ws_app.write(r, 7, charge_state_label(chg.state), cell_fmt)
                    apt_total += chg.total_amount
                    r += 1

                # Grand Total
                ws_app.merge_range(r, 0, r, 3, "Grand Total", chg_total_label_fmt)
                ws_app.write(r, 4, apt_total, chg_total_fmt)
                ws_app.merge_range(r, 5, r, 7, "", cell_fmt)
                r += 1


        # ── Charges Sheet ─────────────────────────────────────────────────────
        ws_chg = workbook.add_worksheet("Charges")
        ws_chg.merge_range("A1:H1", f"Charges – {self.date}", title_fmt)
        ws_chg.set_row(0, 30)
        ws_chg.set_column("A:A", 10)
        ws_chg.set_column("B:C", 25)
        ws_chg.set_column("D:D", 18)
        ws_chg.set_column("E:G", 15)
        ws_chg.set_column("H:H", 12)

        chg_headers = ["#", "Patient", "Doctor", "Type", "Amount", "Late Fee", "Total", "Status"]
        for col, h in enumerate(chg_headers):
            ws_chg.write(1, col, h, header_fmt)

        for i, chg in enumerate(charges, start=1):
            row = i + 1
            ws_chg.write(row, 0, i, cell_fmt)
            ws_chg.write(row, 1, chg.patient_id.name or "", cell_fmt)
            ws_chg.write(row, 2, chg.doctor_id.name or "", cell_fmt)
            ws_chg.write(row, 3, line_type_label(chg.line_type), cell_fmt)
            ws_chg.write(row, 4, chg.amount, money_fmt)
            ws_chg.write(row, 5, chg.late_fee, money_fmt)
            ws_chg.write(row, 6, chg.total_amount, money_fmt)
            ws_chg.write(row, 7, charge_state_label(chg.state), cell_fmt)

        last = len(charges) + 2
        ws_chg.write(last, 5, "TOTAL", total_fmt)
        ws_chg.write(last, 6, total_revenue, total_fmt)

        # ── Save ──────────────────────────────────────────────────────────────
        workbook.close()
        output.seek(0)
        excel_data = base64.b64encode(output.read())

        file_name = f"daily_census_{self.date}.xlsx"
        self.write({
            "excel_file": excel_data,
            "file_name": file_name,
            "state": "done",
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/daily.census.wizard/{self.id}/excel_file/{file_name}?download=true",
            "target": "new",
        }