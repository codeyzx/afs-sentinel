web: uvicorn afs.web.app:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
release: python -m afs initdb
