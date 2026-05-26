import configparser

CONFIGS = {}

cp = configparser.ConfigParser()
cp.read("config.ini", encoding="utf-8")
d = dict(cp._sections)
for k in d:
    CONFIGS[k] = dict(d[k])


if __name__ == '__main__':
    print(CONFIGS)