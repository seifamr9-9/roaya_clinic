/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SmartClinicAppointment = publicWidget.Widget.extend({

    selector: ".clinic-section",

    start: function () {

        this._super.apply(this, arguments);

        const doctorField =
            document.querySelector("select[name='doctor_id']");

        const dateField =
            document.querySelector("input[name='appointment_date']");

        if (doctorField) {
            doctorField.addEventListener(
                "change",
                () => this.loadSlots()
            );
        }

        if (dateField) {
            dateField.addEventListener(
                "change",
                () => this.loadSlots()
            );
        }
    },

    loadSlots: async function () {

        const doctorField =
            document.querySelector("select[name='doctor_id']");

        const dateField =
            document.querySelector("input[name='appointment_date']");

        const slotSelect =
            document.querySelector("select[name='slot_id']");

        if (!doctorField || !dateField || !slotSelect) {
            return;
        }

        const doctor = doctorField.value;
        const date = dateField.value;

        if (!doctor || !date) {
            return;
        }

        try {

            const response = await fetch(
                "/appointment/get_slots",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        params: {
                            doctor_id: doctor,
                            appointment_date: date,
                        }
                    }),
                }
            );

            const result = await response.json();

            slotSelect.innerHTML = "";

            const slots = result.result || [];

            if (!slots.length) {

                slotSelect.innerHTML =
                    '<option value="">No Available Slots</option>';

                return;
            }

            slots.forEach(function (slot) {

                slotSelect.innerHTML += `
                    <option value="${slot.id}">
                        ${slot.name}
                    </option>
                `;
            });

        } catch (error) {

            console.error(
                "Smart Clinic Slot Loading Error",
                error
            );
        }
    },
});