import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

registry.category("services").add("manual_attendance_systray", {
    async start() {
        if (!(await user.hasGroup("xbo_mmh_custom.group_manual_attendance"))) {
            registry.category("systray").remove("hr_attendance.attendance_menu");
        }
    },
});