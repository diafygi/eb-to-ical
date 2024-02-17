# Eventbrite-to-iCal Converter

**Website:** [https://eb-to-ical.daylightpirates.org/](https://eb-to-ical.daylightpirates.org/)

I wanted to follow several Eventbrite organizers' events on my personal
calendar, but apparently Eventbrite doesn't have iCalendar support. So I made
a proxy that converts the Eventbrite API to iCal (.ics) format. It is super
bare-bones, using only nginx and python (directly via the nginx config).

## How To Use

### Option 1: Use the website

If you just want to convert an organizer's events to an iCal format, all you
need to do is paste their Eventbrite profile (e.g. `https://www.eventbrite.com/o/privacy-lab-7851144983`)
or id (e.g. `7851144983`) into the above [website](https://eb-to-ical.daylightpirates.org/).

All the website does is generate a link for Option 2 (so you don't have to).

### Option 2: Create the link yourself

If you want to automate things, you can just create the iCal link yourself.

```
https://eb-to-ical.daylightpirates.org/eventbrite-organizer-ical?organizer={organizer_id}
```

Replace `{organizer_id}` with the Eventbrite organizer's id
(e.g. `https://www.eventbrite.com/o/privacy-lab-`**`7851144983`**).

NOTE: Since Jan 1, 2020, the Eventbrite API [prohibits](https://groups.google.com/d/msg/eventbrite-api/g88Ian3Kidw/XupDhExqAQAJ)
getting another organizer's list of public events, so unfortunately we have to
use the website's internal API to get past and future events for an organizer :(

### Option 3: Self-host

If you want to run this converter yourself, just include
['cgi.nginx.conf'](https://github.com/diafygi/nginx2cgi/blob/main/cgi.nginx.conf)
in whatever nginx `server` config you want, and configure it to run
[`eb_to_ical.py`](https://github.com/diafygi/eb-to-ical/blob/main/eb_to_ical.py).
All it does is call the python script using CGI, which then looks up the organization's
events and converts it to the iCal format.

Install requirements (needed for `cgi.nginx.conf` to work):
```sh
apt install libnginx-mod-http-perl
```

Add to `server` config (see
[`example_server.conf`](https://github.com/diafygi/eb-to-ical/blob/main/example_server.conf)
for a what I use):
```
server {
    ...
    location /eventbrite-organizer-ical {
        set $cgi_script "cd /etc/nginx/sites-available/eb-to-ical/ && python3 -c 'import eb_to_ical, wsgiref.handlers; wsgiref.handlers.CGIHandler().run(eb_to_ical.app)'";
        include "/etc/nginx/sites-available/nginx2cgi/cgi.nginx.conf";
    }
    ...
}
```

Make sure nginx likes the new include:
```
sudo service nginx configtest
```

Restart the server (you can use `reload` if you already had `libnginx-mod-http-perl` installed):
```
sudo service nginx restart
```

## Donate

If this was useful to you, please donate to the EFF. I don't work there,
but they do fantastic work. I'd recommend signing up for a monthly recurring
donation of $19.84.

[https://eff.org/donate/](https://eff.org/donate/)

## Copyright

Written by Daniel Roesler ([https://daylightpirates.org/](https://daylightpirates.org/)).

Copyright 2024. Released under the GNU AGPLv3.

