(function () {
    function init() {
        var form = document.querySelector('form[action="/appointment/confirm"]');
        if (!form) return;

        var specialtySelect = form.querySelector('select[name="specialty_id"]');
        var doctorSelect = form.querySelector('select[name="doctor_id"]');
        var dateInput = form.querySelector('input[name="appointment_date"]');
        var slotSelect = form.querySelector('select[name="slot_id"]');

        if (!doctorSelect || !dateInput || !slotSelect) return;

        // Keep a copy of every doctor <option> as it was rendered by the server,
        // so we can rebuild the dropdown after filtering without losing data.
        var allDoctorOptions = Array.prototype.slice.call(doctorSelect.options);

        function pad(n) { return n < 10 ? '0' + n : n; }
        function floatToTime(f) {
            var h = Math.floor(f);
            var m = Math.round((f - h) * 60);
            return pad(h) + ':' + pad(m);
        }

        function filterDoctorsBySpecialty() {
            if (!specialtySelect) return;
            var specialtyId = specialtySelect.value;
            var previousDoctorId = doctorSelect.value;

            doctorSelect.innerHTML = '';

            allDoctorOptions.forEach(function (opt) {
                var optSpecialtyId = opt.getAttribute('data-specialty-id');
                var isPlaceholder = opt.value === '';
                var matches = isPlaceholder || !specialtyId || optSpecialtyId === specialtyId;
                if (matches) {
                    doctorSelect.appendChild(opt.cloneNode(true));
                }
            });

            // Try to keep the previously selected doctor if it's still valid for this specialty
            if (previousDoctorId) {
                var stillValid = Array.prototype.some.call(doctorSelect.options, function (o) {
                    return o.value === previousDoctorId;
                });
                if (stillValid) {
                    doctorSelect.value = previousDoctorId;
                } else {
                    doctorSelect.value = '';
                }
            }

            // Doctor selection changed (or was cleared) — refresh the time slots accordingly
            loadSlots();
        }

        function syncSpecialtyFromPreselectedDoctor() {
            // Used when the page loads with a doctor already chosen (e.g. via
            // /appointment?doctor_id=1) but no specialty selected yet. Looks up
            // that doctor's specialty from the original option list and applies
            // it to the Department select, so the two fields stay consistent.
            if (!specialtySelect || !doctorSelect.value) return;
            var selectedOption = allDoctorOptions.filter(function (opt) {
                return opt.value === doctorSelect.value;
            })[0];
            if (selectedOption) {
                var specialtyId = selectedOption.getAttribute('data-specialty-id');
                if (specialtyId) {
                    specialtySelect.value = specialtyId;
                }
            }
        }

        function loadSlots() {
            var doctorId = doctorSelect.value;
            var date = dateInput.value;

            slotSelect.innerHTML = '<option value="">Select Time Slot</option>';
            if (!doctorId || !date) return;

            fetch('/appointment/get_slots', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { doctor_id: doctorId, appointment_date: date }
                })
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var slots = (data && data.result) || [];
                if (!slots.length) {
                    var opt = document.createElement('option');
                    opt.value = '';
                    opt.textContent = 'No slots available for this day';
                    slotSelect.appendChild(opt);
                    return;
                }
                slots.forEach(function (slot) {
                    var opt = document.createElement('option');
                    opt.value = slot.id;
                    opt.textContent = floatToTime(slot.start_time) + ' - ' + floatToTime(slot.end_time);
                    slotSelect.appendChild(opt);
                });
            })
            .catch(function (err) { console.error('Failed to load slots', err); });
        }

        if (specialtySelect) {
            specialtySelect.addEventListener('change', filterDoctorsBySpecialty);
        }
        doctorSelect.addEventListener('change', loadSlots);
        dateInput.addEventListener('change', loadSlots);

        // Apply initial filtering/state in case a specialty or doctor is pre-selected
        // (e.g. coming from /appointment?doctor_id=1)
        if (doctorSelect.value && specialtySelect && !specialtySelect.value) {
            // A doctor is already selected (from the URL) but no specialty yet —
            // derive the specialty from that doctor first, so Department shows
            // correctly and the doctor list stays filtered/consistent with it.
            syncSpecialtyFromPreselectedDoctor();
            filterDoctorsBySpecialty();
        } else if (specialtySelect && specialtySelect.value) {
            filterDoctorsBySpecialty();
        } else if (doctorSelect.value) {
            loadSlots();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already loaded (e.g. script executed after DOMContentLoaded fired) — run immediately
        init();
    }
})();