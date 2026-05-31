# Collabrate-Final-Year-Project

## Logging

Backend logs are written to stdout by default, which works well for most deployment platforms.

Optional backend environment variables:

```env
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

Frontend API logs use the browser console. Set `VITE_LOG_LEVEL=debug`, `info`, `warn`, or `error` before building the frontend.
