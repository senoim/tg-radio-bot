import os

def env(name: str, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or str(v).strip() == ""):
        raise RuntimeError(f"Missing env var: {name}")
    return v

BOT_TOKEN = env("BOT_TOKEN", required=True)
API_ID = int(env("API_ID", required=True))
API_HASH = env("API_HASH", required=True)

ASSISTANT_SESSION = env("ASSISTANT_SESSION", required=True)

DATABASE_URL = env("DATABASE_URL", required=True)

DEVS = set()
for x in env("DEVS", "").replace(" ", "").split(","):
    if x.isdigit():
        DEVS.add(int(x))

AUTO_START = env("AUTO_START", "0") == "1"   # يحاول يشغل عند الإضافة (اختياري)
DEFAULT_LOOP = env("DEFAULT_LOOP", "1") == "1"
