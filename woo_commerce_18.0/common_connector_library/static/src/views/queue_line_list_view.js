/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

class QueueLineEptDashBoard extends Component {
    static template = "common_connector_library.QueueLineEptDashBoard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    async onNameClick(record) {
        const context = record.context || {};
        const dashboardModel = context.dashboard_model;
        const queueLineModel = context.queue_line_model;

        if (dashboardModel && queueLineModel) {
            const action = await this.orm.call(
                dashboardModel,
                'get_queue_lines',
                [[record.resId]],
                {
                    queue_line_model: queueLineModel,
                    shipped: context.shipped || false,
                    unshipped: context.unshipped || false,
                }
            );
            if (action) {
                await this.action.doAction(action);
            }
        }
    }
}

export class QueueLineEptDashboardRenderer extends ListRenderer {
    static components = {
        ...ListRenderer.components,
        QueueLineEptDashBoard,
    };

    async onCellClicked(record, column, ev) {
        if (column.name === 'name') {
            const context = column.context || {};
            const dashboardModel = context.dashboard_model;
            const queueLineModel = context.queue_line_model;

            if (dashboardModel && queueLineModel) {
                ev.preventDefault();
                const action = await this.orm.call(
                    dashboardModel,
                    'get_queue_lines',
                    [[record.resId]],
                    {
                        queue_line_model: queueLineModel,
                        shipped: context.shipped || false,
                        unshipped: context.unshipped || false,
                    }
                );
                if (action) {
                    await this.action.doAction(action);
                }
            } else {
                await super.onCellClicked(record, column, ev);
            }
        } else {
            await super.onCellClicked(record, column, ev);
        }
    }
}

export const QueueLineEptDashBoardListView = {
    ...listView,
    Renderer: QueueLineEptDashboardRenderer,
};

registry.category("views").add("queue_line_ept_dashboard", QueueLineEptDashBoardListView);