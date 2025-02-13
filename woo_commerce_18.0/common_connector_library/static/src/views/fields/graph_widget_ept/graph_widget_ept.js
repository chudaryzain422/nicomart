/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { getColor, hexToRGBA } from "@web/core/colors/colors";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";
import { cookie } from "@web/core/browser/cookie";
import { useService } from "@web/core/utils/hooks";

export class EmiproDashboardGraph extends Component {
    static template = "common_connector_library.EmiproDashboardGraph";
    static props = {
        ...standardFieldProps,
        graphType: String,
    };

    setup() {
        super.setup();
        this.chart = null;
        this.orm = useService("orm");
        this.action = useService("action");
        this.canvasRef = useRef("canvas");
        this.graph_data = null;

        // Load data from props
        const { record } = this.props;
        if (record?.data?.[this.props.name]) {
            this.data = JSON.parse(record.data[this.props.name]);
        }

        if (record?.data) {
            const matchKey = Object.keys(record.data).find((key) => key.includes("_order_data"));
            this.graph_data = matchKey ? JSON.parse(record.data[matchKey]) : null;
        }

        // Load Chart.js
        onWillStart(() => {
            return loadJS("/web/static/lib/Chart/Chart.js");
        });

        // Effect to render the chart
        useEffect(() => {
            this.renderChart();
            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }

    renderChart() {
        if (!this.graph_data || !this.props.graphType) {
            return;
        }

        if (this.chart) {
            this.chart.destroy();
        }

        const config = this.getLineChartConfig();
        this.chart = new Chart(this.canvasRef.el, config);
    }

    getLineChartConfig() {
        const labels = this.graph_data?.values?.map((pt) => pt.x) || [];
        const color10 = getColor(10, cookie.get("color_scheme"));
        const isSampleData = this.graph_data?.is_sample_data || false;

        return {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        data: this.graph_data?.values || [],
                        fill: "start",
                        label: this.graph_data?.key || "",
                        backgroundColor: hexToRGBA(color10, isSampleData ? 0.05 : 0.2),
                        borderColor: hexToRGBA(color10, isSampleData ? 0.1 : 1),
                        borderWidth: 2,
                        pointStyle: "line",
                    },
                ],
            },
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        intersect: false,
                        position: "nearest",
                        caretSize: 0,
                    },
                },
                scales: {
                    x: { position: "bottom" },
                    y: {
                        position: "left",
                        ticks: {
                            beginAtZero: true,
                        },
                    },
                },
                maintainAspectRatio: false,
                elements: {
                    line: { tension: 0.5 },
                },
            },
        };
    }

    updateGraphData(newData) {
        this.graph_data = newData;
        this.renderChart();
    }

    onchangeSortOrderData(e) {
        const context = { ...this.props.record.context, sort: e.currentTarget.value };

        return this.orm.call(this.props.record.resModel, "read", [this.props.record.resId], { context }).then((result) => {
            if (result.length) {
                this.updateGraphData(JSON.parse(result[0][this.match_key]));
            }
        });
    }

    _getProducts() {
        return this.action.doAction(this.graph_data?.product_date?.product_action);
    }

    _getCustomers() {
        return this.action.doAction(this.graph_data?.customer_data?.customer_action);
    }

    _getOrders() {
        return this.action.doAction(this.graph_data?.order_data?.order_action);
    }

    _getShippedOrders() {
        return this.action.doAction(this.graph_data?.order_shipped?.order_action);
    }

    _getRefundOrders() {
        return this.action.doAction(this.graph_data?.refund_data?.refund_action);
    }

    _getReport() {
        return this.orm.call(this.props.record.resModel, "open_report", [this.props.record.resId]).then((result) => {
            this.action.doAction(result);
        });
    }

    _getLog() {
        return this.orm.call(this.props.record.resModel, "open_logs", [this.props.record.resId]).then((result) => {
            this.action.doAction(result);
        });
    }

    _performOperation() {
        return this.orm.call(this.props.record.resModel, "perform_operation", [this.props.record.resId]).then((result) => {
            this.action.doAction(result);
        });
    }
}

export const emiproDashboardGraph = {
    component: EmiproDashboardGraph,
    supportedTypes: ["text"],
    extractProps: ({ attrs }) => ({
        graphType: attrs.graph_type,
    }),
};

registry.category("fields").add("dashboard_graph_ept", emiproDashboardGraph);
