# Eventbrite-to-iCal Converter

**Website:** [https://eb-to-ical.daylightpirates.org/](https://eb-to-ical.daylightpirates.org/)

I wanted to follow several Eventbrite organizers' events on my personal
calendar, but apparently Eventbrite doesn't have iCalendar support. So I made
a proxy that converts the Eventbrite API to iCal (.ics) format. It is super
bare-bones, using only nginx and Lua (directly in the nginx config).

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

If you want to run this converter yourself, just include the
[`eb_to_ical.conf`](https://github.com/diafygi/eb-to-ical/blob/master/eb_to_ical.conf)
in whatever nginx `server` config you want. All it does is add two locations
(`/eventbrite-organizer-ical` and `/eventbrite-api`). The iCal conversion is
done via Lua directly in the nginx config, so no outside dynamic servers are
required!

Install requirements:
```sh
apt-get install nginx-extras lua-cjson
```

Add to `server` config (see
[`example_server.conf`](https://github.com/diafygi/eb-to-ical/blob/master/example_server.conf)
for a what I use):
```
server {
    ...
    include /path/to/eb_to_ical.conf;
    ...
}
```

Make sure nginx likes the new include:
```
sudo service nginx configtest
```

Restart the server (you can use `reload` if you were already using `nginx-extras`):
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

Copyright 2017. Released under the GNU AGPLv3.

