#coding=utf-8
import pstats
#
p = pstats.Stats('profile.stats')
# p.sort_stats("cumulative")
p.sort_stats("tottime")
# 输出累计时间报告
p.print_stats()
# 输出调用者的信息
p.print_callers()
# 输出哪个函数调用了哪个函数
p.print_callees()
