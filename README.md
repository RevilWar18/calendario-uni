# calendario-uni

Personal tool that syncs my university assignments from Moodle
into a Google Calendar, color-coded by urgency.

## How it works
1. Reads my Moodle calendar export (.ics).
2. Matches each event to a subject and computes its urgency.
3. Creates or updates events in a dedicated Google Calendar.

Built with Python, the Google Calendar API and Windows Task Scheduler.