# Calendar Feeds

## Goal

The app should generate read-only iCalendar/ICS feeds that external calendar applications can subscribe to.

This allows Apple Calendar, Google Calendar, Outlook, and similar apps to display selected opportunity and operation data.

## Use Cases

### All Opportunities

Subscribe to every opportunity in the database.

### Filtered Opportunities

Subscribe to saved-filter results, such as:

- within 60 km of Schoonebeek
- profit score above 80
- only events with electricity
- only opportunities in August
- not filtered out by user criteria

### Application Deadlines

Subscribe to application deadlines so the user can avoid missing windows.

### Committed Operations

Subscribe only to operations the user has committed to.

This is the most important operational calendar because it represents what the user plans to do in real life.

### Operation Tasks

Future feed for setup, teardown, prep, shopping, loading, and follow-up tasks.

## ICS Feed Requirements

- feeds are read-only
- each feed has a stable URL
- each feed can be enabled/disabled
- feed filters are stored in the database
- committed operations should produce calendar events
- deadlines should produce all-day or timed calendar entries
- opportunities may be exported as all-day events unless times are known

## Security

If the app is local-only, feed tokens are mostly convenience identifiers.

If remote access is ever added, feed access and tokens require a new security review and possibly a new ADR.
