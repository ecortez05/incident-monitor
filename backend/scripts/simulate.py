"""Send fake traffic to the API so the dashboard has something to show.

    python scripts/simulate.py                # runs until Ctrl+C
    python scripts/simulate.py --burst api    # fire a burst of errors from "api"
"""
import argparse
import random
import time

import httpx

SERVICES = ["api", "auth", "payments", "worker", "search"]
MESSAGES = {
    "debug": ["cache miss for key user:42", "retrying request"],
    "info": ["request completed in 120ms", "user signed in", "job finished"],
    "warning": ["slow query (1.8s)", "queue depth above 500", "memory at 85%"],
    "error": ["connection refused to db", "timeout calling upstream", "unhandled exception in handler"],
    "critical": ["out of memory, restarting", "primary database unreachable"],
}
WEIGHTS = {"debug": 15, "info": 55, "warning": 20, "error": 8, "critical": 2}


def send(client, source, level, message):
    r = client.post("/events", json={"source": source, "level": level, "message": message})
    r.raise_for_status()
    print(f"{level:8} {source:10} {message}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--burst", metavar="SOURCE", help="send a run of errors from one service")
    args = parser.parse_args()

    with httpx.Client(base_url=args.url, timeout=5) as client:
        if args.burst:
            for _ in range(6):
                send(client, args.burst, "error", random.choice(MESSAGES["error"]))
                time.sleep(0.2)
            return

        while True:
            level = random.choices(list(WEIGHTS), weights=list(WEIGHTS.values()))[0]
            send(client, random.choice(SERVICES), level, random.choice(MESSAGES[level]))
            time.sleep(random.uniform(0.3, 1.5))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
