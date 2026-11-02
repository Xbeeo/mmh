from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta
import pytz


class AbsentLateWizard(models.TransientModel):
    _name = 'absent.late.wizard'
    _description = 'Absent & Late Employee Wizard'

    date_from = fields.Date(
        string='Date From',
        required=True,
        default = fields.Date.today
    )

    date_to = fields.Date(
        string='Date To',
        required=True,
        default=fields.Date.today
    )

    def action_print_report(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError(_("Date From cannot be greater than Date To."))

        return self.env.ref(
            'xbo_mmh_report.action_absent_late_employee_report'
        ).report_action(self)

    def _get_report_lines(self):
        self.ensure_one()

        employees = self.env['hr.employee'].sudo().search([
            ('active', '=', True),
            ('resource_calendar_id', '!=', False),
        ], order='name')

        Attendance = self.env['hr.attendance'].sudo()

        report_lines = []

        current_date = self.date_from

        while current_date <= self.date_to:

            for employee in employees:

                calendar = employee.resource_calendar_id

                if not calendar:
                    continue

                # Employee timezone
                tz_name = (
                    employee.tz
                    or calendar.tz
                    or 'UTC'
                )

                tz = pytz.timezone(tz_name)

                # Local day start and end
                local_start = tz.localize(
                    datetime.combine(current_date, time.min)
                )

                local_end = local_start + timedelta(days=1)

                # Convert local date boundaries to UTC
                utc_start = local_start.astimezone(pytz.UTC).replace(
                    tzinfo=None
                )

                utc_end = local_end.astimezone(pytz.UTC).replace(
                    tzinfo=None
                )

                # Get actual working intervals from employee schedule.
                # This also respects scheduled non-working days and leaves.
                intervals_by_resource = calendar._work_intervals_batch(
                    local_start,
                    local_end,
                    resources=employee.resource_id,
                    tz=tz,
                )

                intervals = intervals_by_resource.get(
                    employee.resource_id.id
                )

                if not intervals:
                    intervals = intervals_by_resource.get(False)

                if not intervals:
                    continue

                # First scheduled working time of the day
                scheduled_starts = []

                for interval in intervals:
                    interval_start = interval[0]

                    if not interval_start.tzinfo:
                        interval_start = pytz.UTC.localize(
                            interval_start
                        )

                    interval_start = interval_start.astimezone(tz)

                    scheduled_starts.append(interval_start)

                if not scheduled_starts:
                    continue

                scheduled_start = min(scheduled_starts)

                # 15 minutes grace period
                late_time = scheduled_start + timedelta(minutes=15)

                # Get employee attendance of this local date
                attendances = Attendance.search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', utc_start),
                    ('check_in', '<', utc_end),
                ], order='check_in asc')

                if not attendances:

                    # No attendance = Absent
                    report_lines.append({
                        'date': current_date.strftime('%d-%m-%Y'),
                        'employee': employee.name,
                        'status': 'Absent',
                        'check_in': '-',
                        'check_out': '-',
                        'worked_hours': '00:00',
                    })

                    continue

                # First check-in
                first_attendance = attendances[0]

                check_in = fields.Datetime.context_timestamp(
                    employee,
                    first_attendance.check_in
                ).astimezone(tz)

                # Last checkout
                checked_out = attendances.filtered(
                    lambda attendance: attendance.check_out
                )

                if checked_out:
                    last_attendance = checked_out[-1]

                    check_out = fields.Datetime.context_timestamp(
                        employee,
                        last_attendance.check_out
                    ).astimezone(tz)

                    checkout_text = check_out.strftime('%I:%M %p')
                else:
                    checkout_text = '-'

                # Total worked hours of all attendance records
                total_hours = sum(
                    attendances.mapped('worked_hours')
                )

                hours = int(total_hours)
                minutes = int(round((total_hours - hours) * 60))

                if minutes == 60:
                    hours += 1
                    minutes = 0

                worked_hours = f'{hours:02d}:{minutes:02d}'

                # Check late status
                if check_in > late_time:

                    report_lines.append({
                        'date': current_date.strftime('%d-%m-%Y'),
                        'employee': employee.name,
                        'status': 'Late',
                        'check_in': check_in.strftime('%I:%M %p'),
                        'check_out': checkout_text,
                        'worked_hours': worked_hours,
                    })

            current_date += timedelta(days=1)

        return report_lines