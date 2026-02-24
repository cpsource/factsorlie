# TODO

## Cloudflare Turnstile Captcha for /submit

The Turnstile error 110200 means the site key isn't authorized for this domain. The current key is configured for frflashy.com, not factsorlie.com. You need to create a new Turnstile widget in your Cloudflare dashboard for factsorlie.com.

For Turnstile — go to https://dash.cloudflare.com/?to=/:account/turnstile and add a new site with hostname `factsorlie.com`. That will give you a new site key and secret key. Then add them to `/home/ubuntu/.env` as:

```
CLOUDFLARE_TURNSTYLE_SITE_KEY=<new_key>
CLOUDFLARE_TURNSTYLE_SECRET_KEY=<new_secret>
```

And restart with `docker-compose up -d`.

Once configured, uncomment the Turnstile code in:
- `app.py` — captcha verification in `/submit` route
- `templates/submit.html` — Turnstile widget
- `tools/qa/test_submit.py` — captcha failure test

## Favicon

The favicon 404 is harmless but easy to fix — add a `favicon.ico` to the static directory.
