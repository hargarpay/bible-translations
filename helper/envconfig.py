import os
import re

def load_env(env = ".env"):
    with open(env) as file:
        for line in file:
            comment = re.search("^#", line)
            if line != "\n" and comment is None:
                line = re.sub("\n", "", line)
                env_var = re.split("=", line)
                if len(env_var) == 2:
                    os.environ[env_var[0]] = env_var[1]

load_env()