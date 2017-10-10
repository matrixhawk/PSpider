# _*_ coding: utf-8 _*_

"""
concur_threads_insts.py by xianhu
"""

import time
import logging
from .concur_abase import TPEnum, BaseThread


# ===============================================================================================================================
def work_fetch(self):
    """
    procedure of fetching, auto running, and return False if you need stop thread
    """
    # ----1----
    priority, url, keys, deep, repeat = self._pool.get_a_task(TPEnum.URL_FETCH)

    # ----2----
    fetch_result, content = self._worker.working(url, keys, repeat)

    # ----3----
    if fetch_result == 1:
        self._pool.update_number_dict(TPEnum.URL_FETCH, +1)
        self._pool.add_a_task(TPEnum.HTM_PARSE, (priority, url, keys, deep, content))
    elif fetch_result == 0:
        self._pool.add_a_task(TPEnum.URL_FETCH, (priority+1, url, keys, deep, repeat+1))

    # ----4----
    self._pool.finish_a_task(TPEnum.URL_FETCH)
    return False if fetch_result == -2 else True

FetchThread = type("FetchThread", (BaseThread,), dict(working=work_fetch))


# ===============================================================================================================================
def work_parse(self):
    """
    procedure of parsing, auto running, and only return True
    """
    # ----1----
    priority, url, keys, deep, content = self._pool.get_a_task(TPEnum.HTM_PARSE)

    # ----2----
    parse_result, url_list, save_list = self._worker.working(priority, url, keys, deep, content)

    # ----3----
    if parse_result > 0:
        self._pool.update_number_dict(TPEnum.HTM_PARSE, +1)
        for _url, _keys, _priority in url_list:
            self._pool.add_a_task(TPEnum.URL_FETCH, (_priority, _url, _keys, deep+1, 0))
        for item in save_list:
            self._pool.add_a_task(TPEnum.ITEM_SAVE, (url, keys, item))

    # ----4----
    self._pool.finish_a_task(TPEnum.HTM_PARSE)
    return True

ParseThread = type("ParseThread", (BaseThread,), dict(working=work_parse))


# ===============================================================================================================================
def work_save(self):
    """
    procedure of saving, auto running, and only return True
    """
    # ----1----
    url, keys, item = self._pool.get_a_task(TPEnum.ITEM_SAVE)

    # ----2----
    save_result = self._worker.working(url, keys, item)

    # ----3----
    if save_result:
        self._pool.update_number_dict(TPEnum.ITEM_SAVE, +1)

    # ----4----
    self._pool.finish_a_task(TPEnum.ITEM_SAVE)
    return True

SaveThread = type("SaveThread", (BaseThread,), dict(working=work_save))


# ===============================================================================================================================
def init_monitor_thread(self, name, pool, sleep_time=5):
    """
    constructor of MonitorThread
    """
    BaseThread.__init__(self, name, None, pool)

    self._sleep_time = sleep_time       # sleeping time in every loop
    self._init_time = time.time()       # initial time of this spider

    self._last_fetch_num = 0            # fetch number in last time
    self._last_parse_num = 0            # parse number in last time
    self._last_save_num = 0             # save number in last time
    return


def work_monitor(self):
    """
    monitor the pool, auto running, and return False if you need stop thread
    """
    time.sleep(self._sleep_time)
    info = "%s status: running_tasks=%s;" % (self._pool.__class__.__name__, self._pool.get_number_dict(TPEnum.TASKS_RUNNING))

    cur_fetch_num = self._pool.get_number_dict(TPEnum.URL_FETCH)
    cur_not_fetch_num = self._pool.get_number_dict(TPEnum.URL_NOT_FETCH)
    info += " fetch=(%d, %d, %d/(%ds));" % (cur_not_fetch_num, cur_fetch_num, cur_fetch_num-self._last_fetch_num, self._sleep_time)
    self._last_fetch_num = cur_fetch_num

    cur_parse_num = self._pool.get_number_dict(TPEnum.HTM_PARSE)
    cur_not_parse_num = self._pool.get_number_dict(TPEnum.HTM_NOT_PARSE)
    info += " parse=(%d, %d, %d/(%ds));" % (cur_not_parse_num, cur_parse_num, cur_parse_num-self._last_parse_num, self._sleep_time)
    self._last_parse_num = cur_parse_num

    cur_save_num = self._pool.get_number_dict(TPEnum.ITEM_SAVE)
    cur_not_save_num = self._pool.get_number_dict(TPEnum.ITEM_NOT_SAVE)
    info += " save=(%d, %d, %d/(%ds));" % (cur_not_save_num, cur_save_num, cur_save_num-self._last_save_num, self._sleep_time)
    self._last_save_num = cur_save_num

    info += " total_seconds=%d" % (time.time() - self._init_time)
    logging.warning(info)

    return False if self._pool.get_monitor_stop_flag() else True

MonitorThread = type("MonitorThread", (BaseThread,), dict(__init__=init_monitor_thread, working=work_monitor))
