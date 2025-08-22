import os, sys

COMMANDS_TO_SKIP = {'migrate', 'makemigrations', 'collectstatic', 'shell', 'dbshell', 'showmigrations', 'check', 'test'}

def should_skip_startup() -> bool:
    # 1) явний прапорець через змінну оточення
    if os.environ.get('LAZYSOFT_DISABLE_STARTUP') == '1':
        return True
    # 2) якщо запускається одна з «системних» команд Django
    argv = set(sys.argv)
    if any(cmd in argv for cmd in COMMANDS_TO_SKIP):
        return True
    return False
