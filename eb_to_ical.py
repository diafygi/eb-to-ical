import re
import json
import logging
from datetime import timezone, datetime
from urllib.error import HTTPError
from urllib.parse import parse_qsl
from urllib.request import urlopen, Request

def app(environ, start_response):
    resp_body = b""

    # iCal escape logic
    #   only allow simple ascii characters and linebreaks,
    #   and escape backslashes, commas, semicolons and linebreaks
    def escape(bytes):
        bytes = bytes.encode() if isinstance(bytes, str) else bytes
        return (re.sub(b"[^\x20-\x7e\n]", b"", bytes)
            .replace(b"\\", b"\\\\")
            .replace(b",", b"\\,")
            .replace(b";", b"\\;")
            .replace(b"\n", b"\\n"))

    # iCal line limit at 75 octets
    def wrap_write(bytes):
        bytes = bytes.encode() if isinstance(bytes, str) else bytes
        cur_line, wrapped = b"", b""
        for byte_int in bytes:
            if len(cur_line) >= 75 - 2: # 75 minus linebreak characters (\r\n):
                wrapped += cur_line + b"\r\n"
                cur_line = b" "
            cur_line += chr(byte_int).encode()
        if cur_line:
            wrapped += cur_line + b"\r\n"
        nonlocal resp_body
        resp_body += wrapped

    # determine the organizer_id from the query parameter
    org_param = dict(parse_qsl(environ.get("QUERY_STRING") or "")).get("organizer") or ""
    org_re = re.search("([0-9a-zA-Z]+)/?(\\?[^\\?]+)?$", org_param)
    if not org_re:
        resp_body = b"Unknown Eventbrite Organization"
        start_response("400 Bad Request", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(resp_body))),
        ])
        return [resp_body]
    org_id = org_re.groups()[0]

    # Can't use the API since /v3/organizations/{org_id}/events/ doesn't work, so have to scrape from the website itself :(
    # (see https://groups.google.com/d/msg/eventbrite-api/g88Ian3Kidw/XupDhExqAQAJ)

    # make eventbrite request to get organizer's past and future events
    events = []
    for evt_type in ["future", "past"]:
        page = 1
        while page:
            eb_url = f"https://www.eventbrite.com/org/{org_id}/showmore/?type={evt_type}&page={page}"

            # report any non-2XX errors
            try:
                eb_resp = urlopen(Request(url=eb_url))
            except HTTPError as resp_err:
                err_resp = json.dumps({
                    "error": "error_from_eventbrite",
                    "eb_error": {
                        "url": eb_url,
                        "code": resp_err.code,
                        "reason": resp_err.reason,
                        "headers": {k: v for k, v in resp_err.headers.items()},
                        "body": resp_err.read().decode(),
                    }
                }, indent=4).encode()
                start_response("502 Bad Gateway", [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(err_resp))),
                ])
                return [err_resp]

            # report any malformed response payloads
            try:
                eb_resp_json = json.loads(eb_resp.read())
                events.extend(eb_resp_json['data']['events'])
                eb_has_next = eb_resp_json['data']['has_next_page']
            except (ValueError, KeyError) as ex:
                err_resp = json.dumps({
                    "error": "error_parsing_eb_response",
                    "eb_response": {
                        "url": eb_url,
                        "status": eb_resp.status,
                        "body": eb_resp.read().decode(),
                    }
                }, indent=4).encode()
                start_response("502 Bad Gateway", [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(err_resp))),
                ])
                return [err_resp]

            # iterate to next page
            page = (page + 1) if eb_has_next else None

    # VCALENDAR header
    wrap_write("BEGIN:VCALENDAR")
    wrap_write("VERSION:2.0")
    wrap_write("PRODID:-//DaylightPirates//EB-to-iCAL//EN")

    # VEVENT objects
    for i, event in enumerate(reversed(sorted(events, key=lambda e: e['published']))):

        # X-WR-CALNAME (first loop before VEVENT)
        if i == 0:
            if event.get("organizer"):
                wrap_write(b"X-WR-CALNAME:" + escape(event['organizer']['name']) + b" - Eventbrite Events")
                wrap_write(b"X-ORIGINAL-URL:" + escape(event['organizer']['url']))
            else:
                wrap_write("X-WR-CALNAME:Eventbrite Events")

        wrap_write("BEGIN:VEVENT")

        # DTSTAMP
        dtstamp = event['published'].replace("-", "").replace(":", "")
        wrap_write(b"DTSTAMP:" + escape(dtstamp))

        # DTSTART
        dtstart = event['start']['utc'].replace("-", "").replace(":", "")
        wrap_write(b"DTSTART:" + escape(dtstart))

        # DTEND
        dtend = event['end']['utc'].replace("-", "").replace(":", "")
        wrap_write(b"DTEND:" + escape(dtend))

        # SUMMARY
        wrap_write(b"SUMMARY:" + escape(event['name']['text']))

        # DESCRIPTION
        wrap_write(b"DESCRIPTION:" + escape(event['url'] + "\n\n" + event['description']['text']))

        # CREATED (ngx.utctime, "yyyy-mm-dd hh:mm:ss")
        created = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        wrap_write(b"CREATED:" + escape(created))

        if event.get("venue"):
            # GEO
            latitude = event['venue'].get("address", {}).get("latitude")
            longitude = event['venue'].get("address", {}).get("longitude")
            if latitude and longitude:
                wrap_write(b"GEO:" + escape(latitude) + b";" + escape(longitude))

            # LOCATION
            location = None
            if event['venue'].get("name"):
                location = event['venue']['name']
            if event['venue'].get("address", {}).get("localized_address_display"):
                if location:
                    location = location + ", " + event['venue']['address']['localized_address_display']
                else:
                    location = event['venue']['address']['localized_address_display']
            if location:
                wrap_write(b"LOCATION:" + escape(location))

        # URL
        wrap_write(b"URL:" + escape(event['url']))

        # LAST-MODIFIED
        changed = event['published'].replace("-", "").replace(":", "")
        wrap_write(b"LAST-MODIFIED:" + escape(changed))

        # UID
        wrap_write(b"UID:" + escape(event['id']))

        wrap_write(b"END:VEVENT")

    # VCALENDAR footer
    wrap_write(b"END:VCALENDAR")

    start_response("200 OK", [
        ("Content-Type", "text/calendar; charset=utf-8"),
        ("Content-Disposition", 'attachment; filename="eventbrite_organizer_events.ics"'),
        ("Content-Length", str(len(resp_body))),
    ])
    return [resp_body]

