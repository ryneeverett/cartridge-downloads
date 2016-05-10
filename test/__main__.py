import os
import sys
import textwrap
import subprocess

import django
from django.conf import settings
from django.test.utils import get_runner


if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'resources.settings'
    django.setup()
    test_runner = get_runner(settings)()
    is_failure = bool(test_runner.run_tests(['test_downloads']))

    if not is_failure:
        with open('requirements.txt', 'w') as reqs:
            reqs.write(textwrap.dedent("""\
                # This file exists simply as a record of what was installed
                # when the tests passed. Go ahead and commit it.\n"""))

            freeze = subprocess.Popen(
                ['pip', 'freeze', '--local'], stdout=subprocess.PIPE)

            for line in freeze.stdout.readlines():
                line = line.decode()
                if 'cartridge-downloads' not in line:
                    reqs.write(line)

    sys.exit(is_failure)
