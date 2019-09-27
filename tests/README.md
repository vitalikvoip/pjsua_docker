# pjsua_tests

# Docs
Usage:  ./test.py  file.csv domain outbound_proxy [protocol]

Usage: ./ua.py options
          options:
              -l [login],       --login=[login]
              -p [password],    --password=[password]
              -d [domain],      --domain=[domain]
              -P [proxy],       --proxy=[proxy]
              -D [destination], --destination=[num]    <= optional
              -m                --media                <= optional
              -h                --help                 <= optional
              -v                --verbose              <= optional

# Running a test
./test.py ifctest_load_test_accouts.txt ifctest.net lab.ifctest.net

# Stopping test
ctrl+c

# file.csv format
123456 QAZWSXQAZWSX

# where login is 123456 and password is QAZWSXQAZWSX
