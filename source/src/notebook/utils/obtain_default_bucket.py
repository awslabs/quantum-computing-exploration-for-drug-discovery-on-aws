import os


def obtain_default_bucket(target: str) -> str:
    with open(os.path.join(os.path.dirname(__file__),
              '../.default-settings')) as f:
        lines = f.readlines()
        for line in lines:
            if (line.startswith(target+'=')):
                return line.split('=')[1]


if __name__ == "__main__":
    print(obtain_default_bucket('bucketName'))
