from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError, UserError
import json
from functools import wraps
from datetime import date, timedelta, datetime


# Validate the Bearer token / return an appropriate error response based on the route type (json or http)
def validate_token(route_type="json"):
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            def error(message, status=401):
                payload = {
                    "status": "error",
                    "message": message,
                }

                if route_type == "json":
                    return payload

                return request.make_response(
                    json.dumps(payload),
                    headers=[("Content-Type", "application/json")],
                    status=status,
                )

            token = request.httprequest.headers.get("Authorization")

            if not token:
                return error("Missing Authorization Bearer Token")

            if token.startswith("Bearer "):
                token = token[7:]

            token_obj = (
                request.env["api.token"]
                .sudo()
                .search(
                    [
                        ("token", "=", token),
                        ("is_active", "=", True),
                    ],
                    limit=1,
                )
            )

            if not token_obj:
                return error("Invalid or Expired Token")

            if token_obj.expiry_date and token_obj.expiry_date < fields.Datetime.now():
                return error("Token Expired")

            ip = (
                request.httprequest.headers.get("X-Forwarded-For")
                or request.httprequest.remote_addr
            )

            token_obj.sudo().write(
                {
                    "last_used": fields.Datetime.now(),
                    "last_ip": ip,
                }
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


class ClinicApiController(http.Controller):
    # Generate New Token From Public Endpoint
    @http.route(
        "/api/token/generate",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def generate_token(self, **kwargs):
        user_id = kwargs.get("user_id")

        if not user_id:
            return {
                "status": "error",
                "message": "User ID is required",
            }

        user = request.env["res.users"].sudo().browse(user_id)

        if not user.exists():
            return {
                "status": "error",
                "message": "User not found",
            }
        expiry_date = fields.Datetime.now() + timedelta(days=30)
        token = (
            request.env["api.token"]
            .sudo()
            .search(
                [("user_id", "=", user.id)],
                limit=1,
            )
        )

        if token:
            token.write(
                {
                    "expiry_date": expiry_date,
                    "is_active": True,
                    "last_used": False,
                    "last_ip": False,
                }
            )
            token.action_regenerate_token()
        else:
            token = (
                request.env["api.token"]
                .sudo()
                .create(
                    {
                        "name": f"{user.name} API Token",
                        "user_id": user.id,
                        "expiry_date": expiry_date,
                        "is_active": True,
                    }
                )
            )

        return {
            "status": "success",
            "message": "Token generated successfully",
            "data": {
                "name": f"{token.name} API Token",
                "user_id": token.user_id.id,
                "token": token.token,
                "is_active": token.is_active,
                "expires_on": token.expiry_date,
                "last_used": token.last_used or "null",
            },
        }

    # /api/clinic/appointments/create
    # Create Property From API Call
    @http.route(
        "/api/clinic/appointments/create",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    @validate_token("json")
    def create_appointment(self, **kwargs):
        try:
            params = kwargs
            patient = (
                request.env["clinic.patient"].sudo().browse(params.get("patient_id"))
            )

            if not patient.exists():
                return {
                    "status": "error",
                    "message": "Patient not found.",
                }

            doctor = request.env["clinic.doctor"].sudo().browse(params.get("doctor_id"))

            if not doctor.exists():
                return {
                    "status": "error",
                    "message": "Doctor not found.",
                }

            # Create Appointment
            appointment_obj = (
                request.env["clinic.appointment"]
                .sudo()
                .create(
                    {
                        "patient_id": params.get("patient_id"),
                        "doctor_id": params.get("doctor_id"),
                        "date": params.get("date"),
                    }
                )
            )

            return {
                "status": "success",
                "message": "Appointment Created Successfully",
                "data": {
                    "appointment_id": appointment_obj.id,
                    "name": appointment_obj.name,
                    "doctor_name": appointment_obj.doctor_id.name,
                    "doctor_speciality": appointment_obj.doctor_id.specialty_id.name,
                    "patient_name": appointment_obj.patient_id.name,
                    "patient_email": appointment_obj.patient_id.email,
                    "patient_age": appointment_obj.patient_id.age,
                    "date": appointment_obj.date,
                    "state": appointment_obj.state,
                },
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # /api/clinic/doctors/<int:id> HTTP
    # List Doctor By ID
    @http.route(
        "/api/clinic/doctors/<int:doctor_id>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    @validate_token("http")
    def get_doctor(self, doctor_id):
        # GET http://localhost:8017/api/clinic/doctors/1
        try:
            doctor_obj = request.env["clinic.doctor"].sudo().browse(doctor_id)

            if not doctor_obj.exists():
                return request.make_response(
                    json.dumps(
                        {
                            "status": "error",
                            "message": f"Doctor With id {doctor_id} not found",
                        }
                    ),
                    headers={"Content-Type": "application/json"},
                )
            data = {
                "status": "success",
                "data": {
                    "id": doctor_obj.id,
                    "name": doctor_obj.name,
                    "email": (doctor_obj.email or "null"),
                    "speciality": doctor_obj.specialty_id.name,
                    "license_number": doctor_obj.license_number,
                    "consultation_fee": doctor_obj.consultation_fee,
                    "today_appointment_count": doctor_obj.today_appointment_count,
                },
            }
            return request.make_response(
                json.dumps(data), headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            return request.make_response(
                json.dumps({"status": "error", "message": str(e)}),
                headers={"Content-Type": "application/json"},
            )

    # /api/clinic/appointments/list
    # Dynamic Search Domain (filter params)
    @http.route(
        "/api/clinic/appointments/list",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    @validate_token("json")
    def list_appointments(self, **kwargs):
        try:
            params = kwargs

            # Dynamic Search Domain
            domain = []
            if params.get("doctor_id"):
                domain.append(("doctor_id", "=", int(params["doctor_id"])))

            if params.get("date"):
                appointment_date = datetime.strptime(params["date"], "%d/%m/%Y").date()
                domain.append(("date", "=", appointment_date))

            if params.get("state"):
                domain.append(("state", "=", params["state"]))

            if params.get("specialty_id"):
                domain.append(("specialty_id", "=", int(params["specialty_id"])))

            # payment_status not stored - search will not work
            # if params.get("payment_status"):
            #     domain.append(("payment_status", "=", params["payment_status"]))

            # check if domain request is empty
            if not domain:
                return {
                    "status": "error",
                    "message": "At least one search filter is required.",
                }

            # Search properties
            appointments = (
                request.env["clinic.appointment"]
                .sudo()
                .search(domain, limit=params.get("limit", 50))
            )

            # Format response
            data = []
            for rec in appointments:
                data.append(
                    {
                        "id": rec.id,
                        "doctor_id": rec.doctor_id.id,
                        "doctor_name": rec.doctor_id.name,
                        "speciality": rec.specialty_id.name,
                        "patient_id": rec.patient_id.id,
                        "patient_name": rec.patient_id.name,
                        "date": rec.date,
                        "start_time": rec.start_time,
                        "end_time": rec.end_time,
                        "reason": rec.reason or "null",
                        "state": rec.state,
                    }
                )

            return {"status": "success", "count": len(data), "data": data}

        except Exception as e:
            return {"status": "error", "message": str(e)}
