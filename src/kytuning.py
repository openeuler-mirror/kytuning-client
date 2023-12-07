#!/usr/bin/python3

import kytuning

if __name__ == '__main__':
    try:
        kytuning.Main().run()
    except Exception as e:
        print(e)
