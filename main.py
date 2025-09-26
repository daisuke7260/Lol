import multiprocessing
from winrate_ml_1v1 import main as winrate_main
from character_overlay import main as overlay_main

if __name__ == '__main__':
    p1 = multiprocessing.Process(target=winrate_main)
    p2 = multiprocessing.Process(target=overlay_main)

    p1.start()
    p2.start()

    # 任意：終わるまで待つ
    p1.join()
    p2.join()
