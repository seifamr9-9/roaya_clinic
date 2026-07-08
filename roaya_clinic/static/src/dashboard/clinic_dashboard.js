/** @odoo-module **/

import { Component, useState, useRef, onWillStart, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { browser } from "@web/core/browser/browser";

// Key used to remember the last selected range across component
// re-mounts (e.g. when the user opens a filtered list from a KPI
// and then navigates back to the dashboard).
const RANGE_STORAGE_KEY = "roaya_clinic.dashboard.range";

export class ClinicDashboard extends Component {
    static template = "roaya_clinic.ClinicDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.chartRef = useRef("revenueChart");
        this.chart = null;

        // Restore the previously selected range (if any) instead of
        // always defaulting back to "today" after the component is
        // re-created.
        const storedRange = browser.sessionStorage.getItem(RANGE_STORAGE_KEY);
        const initialRange = ["today", "week", "month"].includes(storedRange)
            ? storedRange
            : "today";

        this.state = useState({
            range: initialRange,
            data: null,
            loading: true,
            chartType: "bar", // bar | horizontalBar | line | pie | doughnut
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        // Re-render the chart every time the canvas is mounted/updated,
        // we have data to show (loading finished), or the chart type changes.
        useEffect(
            () => {
                if (!this.state.loading && this.state.data) {
                    this.renderRevenueChart();
                }
                return () => {
                    if (this.chart) {
                        this.chart.destroy();
                        this.chart = null;
                    }
                };
            },
            () => [
                this.chartRef.el,
                this.state.loading,
                this.state.data,
                this.state.chartType,
            ]
        );
    }

    /**
     * Converts the selected range ("today" / "week" / "month") into
     * concrete date_from / date_to strings expected by the backend.
     */
    getDateRange(range) {
        const today = new Date();
        const format = (d) => d.toISOString().slice(0, 10);

        const dateFrom = new Date(today);
        const dateTo = new Date(today);

        if (range === "week") {
            dateFrom.setDate(today.getDate() - 6);
        } else if (range === "month") {
            dateFrom.setDate(today.getDate() - 29);
        }

        return { date_from: format(dateFrom), date_to: format(dateTo) };
    }

    async loadData() {
        this.state.loading = true;
        const { date_from, date_to } = this.getDateRange(this.state.range);
        const data = await this.orm.call(
            "clinic.dashboard",
            "get_dashboard_data",
            [date_from, date_to]
        );
        this.state.data = data;
        this.state.loading = false;
    }

    async onRangeChange(range) {
        if (range === this.state.range) {
            return;
        }
        this.state.range = range;
        // Persist the choice so it survives a navigate-away / navigate-back.
        browser.sessionStorage.setItem(RANGE_STORAGE_KEY, range);
        await this.loadData();
    }

    /**
     * Switch the visual style of the revenue chart
     * (bar / horizontalBar / line / pie / doughnut).
     */
    onChartTypeChange(type) {
        if (type === this.state.chartType) {
            return;
        }
        this.state.chartType = type;
    }

    // ------------------------------------------------------------------
    // Chart rendering
    // ------------------------------------------------------------------
    renderRevenueChart() {
        if (!this.chartRef.el) {
            return;
        }
        const revenueByDoctor = this.state.data.revenue_by_doctor || [];

        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        const palette = [
            "#1565c0", "#2e7d32", "#ef6c00", "#6a1b9a",
            "#00838f", "#c62828", "#4527a0", "#00695c",
        ];

        const labels = revenueByDoctor.map((r) => r.doctor);
        const values = revenueByDoctor.map((r) => r.revenue);
        const colors = revenueByDoctor.map((_, i) => palette[i % palette.length]);

        const selected = this.state.chartType;
        const isCircular = selected === "pie" || selected === "doughnut";
        const chartJsType =
            selected === "horizontalBar"
                ? "bar"
                : selected === "doughnut"
                ? "doughnut"
                : selected;

        const dataset = {
            label: "Revenue",
            data: values,
            backgroundColor: colors,
            borderRadius: isCircular ? 0 : 6,
            maxBarThickness: 42,
            borderColor: isCircular ? "#fff" : undefined,
            borderWidth: isCircular ? 2 : 0,
            fill: selected === "line" ? false : undefined,
            tension: selected === "line" ? 0.35 : undefined,
            pointBackgroundColor: selected === "line" ? colors : undefined,
            pointRadius: selected === "line" ? 4 : undefined,
        };

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: isCircular },
                tooltip: {
                    callbacks: {
                        label: (ctx) =>
                            isCircular
                                ? ` ${ctx.label}: ${ctx.parsed}`
                                : ` ${ctx.parsed.x ?? ctx.parsed.y}`,
                    },
                },
            },
            onClick: (evt, elements) => {
                if (!elements.length) {
                    return;
                }
                const index = elements[0].index;
                const doctor = revenueByDoctor[index];
                if (doctor) {
                    this.onClickDoctor(doctor.doctor_id);
                }
            },
            onHover: (evt, elements) => {
                evt.native.target.style.cursor = elements.length
                    ? "pointer"
                    : "default";
            },
        };

        if (!isCircular) {
            options.indexAxis = selected === "horizontalBar" ? "y" : "x";
            options.scales = {
                x: { beginAtZero: true, grid: { color: "#eee" } },
                y: { grid: { display: false } },
            };
        }

        this.chart = new Chart(this.chartRef.el, {
            type: chartJsType,
            data: { labels, datasets: [dataset] },
            options,
        });
    }

    // ------------------------------------------------------------------
    // Navigation helpers — open a filtered list view
    // ------------------------------------------------------------------
    _openAppointments(extraDomain = []) {
        const { date_from, date_to } = this.getDateRange(this.state.range);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Appointments",
            res_model: "clinic.appointment",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["date", ">=", date_from],
                ["date", "<=", date_to],
                ...extraDomain,
            ],
        });
    }

    _openCharges() {
        const { date_from, date_to } = this.getDateRange(this.state.range);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Paid Charges",
            res_model: "clinic.charge",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["state", "=", "paid"],
                ["payment_date", ">=", date_from],
                ["payment_date", "<=", date_to],
            ],
        });
    }

    _openPatients() {
        const { date_from, date_to } = this.getDateRange(this.state.range);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "New Patients",
            res_model: "clinic.patient",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["create_date", ">=", date_from],
                ["create_date", "<=", date_to],
            ],
        });
    }

    _openLeads(extraDomain = []) {
        const { date_from, date_to } = this.getDateRange(this.state.range);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Leads",
            res_model: "crm.lead",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["create_date", ">=", date_from],
                ["create_date", "<=", date_to],
                ...extraDomain,
            ],
        });
    }

    onClickRevenue() {
        this._openCharges();
    }

    onClickAppointments() {
        this._openAppointments();
    }

    onClickDoneRate() {
        this._openAppointments([["state", "=", "done"]]);
    }

    onClickNoShowRate() {
        this._openAppointments([["state", "=", "no_show"]]);
    }

    onClickNewPatients() {
        this._openPatients();
    }

    onClickNewLeads() {
        this._openLeads();
    }

    onClickConvertedLeads() {
        this._openLeads([["appointment_id", "!=", false]]);
    }

    onClickDoctor(doctorId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "clinic.doctor",
            res_id: doctorId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("roaya_clinic.clinic_dashboard", ClinicDashboard);