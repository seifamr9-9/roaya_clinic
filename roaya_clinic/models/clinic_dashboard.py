from datetime import datetime, time, timedelta

from odoo import models, fields, api


class ClinicDashboard(models.AbstractModel):
    """Data provider for the clinic manager dashboard.

    This model holds no data of its own — it only computes aggregated
    KPIs on demand from clinic.appointment, clinic.charge, clinic.patient
    and crm.lead. It is called directly from the dashboard's JS client
    action via the ORM service (orm.call('clinic.dashboard', 'get_dashboard_data', ...)).
    """

    _name = "clinic.dashboard"
    _description = "Clinic Dashboard Data Provider"

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_data(self, date_from, date_to):
        """Main method called from the client action.

        :param date_from: str 'YYYY-MM-DD' (inclusive)
        :param date_to: str 'YYYY-MM-DD' (inclusive)
        :return: dict, JSON-serializable
        """
        date_from = fields.Date.from_string(date_from)
        date_to = fields.Date.from_string(date_to)
        datetime_from = datetime.combine(date_from, time.min)
        datetime_to = datetime.combine(date_to, time.max)

        appointments = self._get_appointments(date_from, date_to)
        charges = self._get_paid_charges(date_from, date_to)

        return {
            "kpis": self._get_kpis(
                appointments, charges, datetime_from, datetime_to
            ),
            "appointments_trend": self._get_appointments_trend(),
            "revenue_by_doctor": self._get_revenue_by_doctor(charges),
            "status_distribution": self._get_status_distribution(appointments),
            "doctor_performance": self._get_doctor_performance(
                appointments, charges
            ),
            "crm": self._get_crm_summary(datetime_from, datetime_to),
        }

    # ------------------------------------------------------------------
    # Data fetching helpers
    # ------------------------------------------------------------------
    def _get_appointments(self, date_from, date_to):
        return self.env["clinic.appointment"].search(
            [("date", ">=", date_from), ("date", "<=", date_to)]
        )

    def _get_paid_charges(self, date_from, date_to):
        """Charges actually collected (state=paid) within the period,
        based on payment_date (the real cash-in date)."""
        return self.env["clinic.charge"].search(
            [
                ("state", "=", "paid"),
                ("payment_date", ">=", date_from),
                ("payment_date", "<=", date_to),
            ]
        )

    # ------------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------------
    def _get_kpis(self, appointments, charges, datetime_from, datetime_to):
        total_count = len(appointments)
        done_count = len(appointments.filtered(lambda a: a.state == "done"))
        no_show_count = len(
            appointments.filtered(lambda a: a.state == "no_show")
        )

        new_patients_count = self.env["clinic.patient"].search_count(
            [
                ("create_date", ">=", datetime_from),
                ("create_date", "<=", datetime_to),
            ]
        )

        return {
            "total_revenue": sum(charges.mapped("total_amount")),
            "appointment_count": total_count,
            "done_rate": round((done_count / total_count) * 100, 1)
            if total_count
            else 0.0,
            "no_show_rate": round((no_show_count / total_count) * 100, 1)
            if total_count
            else 0.0,
            "new_patients_count": new_patients_count,
        }

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    def _get_appointments_trend(self):
        """Fixed last-30-days trend, independent of the selected filter."""
        today = fields.Date.today()
        start = today - timedelta(days=29)

        appointments = self.env["clinic.appointment"].search(
            [("date", ">=", start), ("date", "<=", today)]
        )

        counts_by_day = {}
        for appt in appointments:
            counts_by_day[appt.date] = counts_by_day.get(appt.date, 0) + 1

        trend = []
        current = start
        while current <= today:
            trend.append(
                {
                    "date": current.isoformat(),
                    "count": counts_by_day.get(current, 0),
                }
            )
            current += timedelta(days=1)

        return trend

    def _get_revenue_by_doctor(self, charges):
        revenue_by_doctor = {}
        for charge in charges:
            doctor = charge.doctor_id
            if not doctor:
                continue
            revenue_by_doctor[doctor] = (
                revenue_by_doctor.get(doctor, 0.0) + charge.total_amount
            )

        return [
            {
                "doctor": doctor.name,
                "doctor_id": doctor.id,
                "revenue": round(revenue, 2),
            }
            for doctor, revenue in sorted(
                revenue_by_doctor.items(), key=lambda item: item[1], reverse=True
            )
        ]

    def _get_status_distribution(self, appointments):
        state_labels = dict(
            self.env["clinic.appointment"]._fields["state"].selection
        )
        distribution = {}
        for state, label in state_labels.items():
            count = len(appointments.filtered(lambda a, s=state: a.state == s))
            if count:
                distribution[label] = count
        return distribution

    # ------------------------------------------------------------------
    # Doctor performance table
    # ------------------------------------------------------------------
    def _get_doctor_performance(self, appointments, charges):
        stats = {}

        for appt in appointments:
            doctor = appt.doctor_id
            if not doctor:
                continue
            entry = stats.setdefault(
                doctor,
                {"appointment_count": 0, "cancelled_or_no_show": 0, "revenue": 0.0},
            )
            entry["appointment_count"] += 1
            if appt.state in ("cancelled", "no_show"):
                entry["cancelled_or_no_show"] += 1

        for charge in charges:
            doctor = charge.doctor_id
            if not doctor:
                continue
            entry = stats.setdefault(
                doctor,
                {"appointment_count": 0, "cancelled_or_no_show": 0, "revenue": 0.0},
            )
            entry["revenue"] += charge.total_amount

        result = []
        for doctor, entry in stats.items():
            appointment_count = entry["appointment_count"]
            cancel_rate = (
                round((entry["cancelled_or_no_show"] / appointment_count) * 100, 1)
                if appointment_count
                else 0.0
            )
            result.append(
                {
                    "doctor": doctor.name,
                    "doctor_id": doctor.id,
                    "appointment_count": appointment_count,
                    "revenue": round(entry["revenue"], 2),
                    "cancel_no_show_rate": cancel_rate,
                }
            )

        result.sort(key=lambda row: row["revenue"], reverse=True)
        return result

    # ------------------------------------------------------------------
    # CRM summary
    # ------------------------------------------------------------------
    def _get_crm_summary(self, datetime_from, datetime_to):
        leads = self.env["crm.lead"].search(
            [
                ("create_date", ">=", datetime_from),
                ("create_date", "<=", datetime_to),
            ]
        )
        new_leads_count = len(leads)
        converted_count = len(leads.filtered(lambda l: l.appointment_id))
        conversion_rate = (
            round((converted_count / new_leads_count) * 100, 1)
            if new_leads_count
            else 0.0
        )

        return {
            "new_leads_count": new_leads_count,
            "converted_count": converted_count,
            "conversion_rate": conversion_rate,
        }