/** @odoo-module */
import { registry } from "@web/core/registry";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KanbanView } from "@web/views/kanban/kanban_view";
import { useService } from "@web/core/utils/hooks";

class WooCollapseButtonController extends KanbanController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async toggleBtn(ev) {
        const companyId = parseInt(ev.currentTarget.dataset.companyId);
        try {
            const result = await this.orm.call(
                "res.company",
                "action_toggle_woo_instances_onboarding_panel",
                [companyId]
            );

            const panel = document.querySelector('.o_onboarding_container.collapse');
            const button = document.querySelector('#woo_button_toggle');

            if (result === 'closed') {
                panel.classList.remove('show');
                button.textContent = 'Create more woo instance';
                button.style.backgroundColor = '#ececec';
                button.style.border = '1px solid #ccc';
            } else {
                panel.classList.add('show');
                button.textContent = 'Hide On boarding Panel';
                button.style.backgroundColor = '';
                button.style.border = '';
            }
        } catch (error) {
            this.notification.notify({
                title: "Warning",
                message: "Something Went Wrong",
                type: "warning",
            });
        }
    }
}

WooCollapseButtonController.template = "woo_commerce_ept.WooCollapseButtonController";

const WooOnBoardingToggleKanbanView = {
    ...KanbanView,
    Controller: WooCollapseButtonController,
};

registry.category("views").add("wooOnBoardingToggle", WooOnBoardingToggleKanbanView);